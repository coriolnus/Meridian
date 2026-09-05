# DEVİR — EDG-2026-042 HAFTALIK KOŞUM #4 (2026-09-05)

**Hüküm işleme Rol-1'dedir.** Bu koşum bir ÖLÇÜM OTURUMUdur: git komutu koşulmadı, karta ve
ROADMAP'e YAZILMADI, dağıtım yapılmadı. Aşağıdaki metinler HAZIR ÖNERİdir; işlenene kadar
**açık kalem**dir (CLAUDE.md §5: işlenmemiş hüküm açık kalemdir).

- Artefakt dizini: `research/olcumler/edg042_kosum_2026-09-05/`
- Canlı snapshot: `canli_ham.json` sha256 `5b015842d006f3f9…`, çekim **2026-09-05T18:39:20Z**, A1
- Reçete: R3/AYRIK `edg042_recete_ayrik_2026-08-31/` (kart işaretçisi) — bayt-özdeş, sha ✓
- Hakem: H2 `edg042_hakem_2026-09-01/` (kart işaretçisi) — sha kıyaslandı, ayrışma YOK
- Doğrulama: 91 passed · `FAILED|ERROR` grep boş · `PYTEST_EXIT=0` · `codelaw.ok = True`

## 1. Kova tablosu

| Kova | n | seans | eşik (n/seans) | eşik dolu? | medyan bps | p25 / p75 | min / maks | en büyük seans payı | damga |
|---|---|---|---|---|---|---|---|---|---|
| `giris_once` (K1-önce) | 15 | 5 | 30 / 10 | **hayır — eşik BEKLEMEZ (kalıcı taban)** | +16,131 | −26,397 / +67,659 | −130,739 / +327,46 | %33,3 | ÖLÇÜLEMEDİ (n=15 < 30) — betimleyici |
| `giris_1345` (K1-1345) | 8 | 5 | 30 / 10 | hayır | +12,476 | −38,455 / +192,589 | −65,214 / +286,115 | %37,5 | ÖLÇÜLEMEDİ (n=8 < 30) — betimleyici |
| `cikis_hedef` (K2) | 6 | 2 | 15 / 6 | hayır | −4,21 | −4,99 / +10,496 | −46,622 / +125,386 | **%66,7 → kill #7 ŞERHİ ZORUNLU** | ÖLÇÜLEMEDİ (n=6 < 15) — betimleyici |
| `cikis_stop` (K3) | 7 | 6 | 15 / 6 | hayır (**seans DOLDU**, n bağlayıcı) | +2,496 | −2,223 / +3,803 | −120,812 / +21,892 | %28,6 | ÖLÇÜLEMEDİ (n=7 < 15) — betimleyici |

`olculemedi` her üç kovada **0**. Model varsayımı (goal.slippage_bps) = **5** — koşum günü künyesi.

**HÜKÜMLÜ KOŞUM TETİKLENMEDİ · CI HESAPLANMADI · KARAR KURALI UYGULANMADI · `status: measuring` KALIR.**

## 2. Önceki koşuma göre değişim (#3 2026-08-31 → #4 2026-09-05)

| Kova | n | seans | medyan bps |
|---|---|---|---|
| `giris_once` | 15 → **15** (donuk kol, beklenen) | 5 → 5 | +16,131 → **+16,131** (birebir) |
| `giris_1345` | 2 → **8** (+6) | 2 → 5 (+3) | +210,07 → **+12,476** |
| `cikis_hedef` | 6 → **6** (+0) | 2 → 2 | −4,21 → −4,21 (birebir) |
| `cikis_stop` | 4 → **7** (+3) | 3 → 6 (+3) | +0,889 → **+2,496** |

`giris_once`'un birebir sabit kalması P-3 hükmünün doğrulanmasıdır: kol 2026-08-23T14:53:43Z'de
emekli oldu ve bir daha satır üretmiyor.

**`giris_1345` medyanındaki büyük düşüş (+210,07 → +12,476) bir hüküm DEĞİLDİR.** Önceki değer
n=2 üzerineydi (ECL +175,1 · CRM +245,0); bu hafta gelen altı satırın dördü modelin altında ya
da yakınında (CF +6,0 · MPC +18,9 · REGN −65,2 · VRTX −38,5 ×2) ve biri yine büyük pozitif
(NOW +286,1). Dağılım hâlâ vahşi: p25/p75 = −38,5 / +192,6. n=8, eşik 30.

`cikis_stop`'ta bu hafta gelen üç satır (NOW −3,7 · ECL +5,0 · CF +21,9) medyanı modelin
altında tutuyor; **seans eşiği (6) ilk kez doldu**, bağlayıcı kısıt artık yalnız n.

`cikis_hedef` iki haftadır hiç büyümedi (n=6, 2 seans) — hedef çıkışı üretilmiyor.

## 3. Eşiğe kalan mesafe (KABA İZDÜŞÜM — ÖLÇÜM DEĞİL, birikim hızı varsayımı)

| Kova | eksik n | eksik seans | bu haftanın hızı | izdüşüm |
|---|---|---|---|---|
| `giris_1345` | 22 | 5 | 6 dolum / 5 seans = 1,2 dolum/seans | bu hızla ~18 seans ≈ **3,7 hafta** (≈2026-10-03); kartın 08-31'de ölçtüğü 0,40 hızıyla ~11 hafta (≈2026-11-21). Bağlayıcı: **n** |
| `cikis_hedef` | 9 | 4 | **0 dolum / 5 seans** | **İZDÜŞÜM VERİLEMEZ** — hız sıfır, tahmin uydurma olurdu (kart: ölçülemeyen değer `None` + neden). Bağlayıcı belirsiz |
| `cikis_stop` | 8 | 0 (doldu) | 3 dolum / 5 seans = 0,6 | ~13 seans ≈ **2,7 hafta** (≈2026-09-24). Bağlayıcı: **n** |

UYARI: haftalık hız n=6 / n=3 üzerine kuruludur — bir hız değil bir İŞARETtir. `giris_1345`
hızının 0,40 → 1,2'ye çıkması gerçek bir hızlanma da olabilir, tek haftanın gürültüsü de.
İki hızla verilen bant bu yüzdendir.

## 4. Pencere hakem katmanı (EXE-2026-009 — bu kartın hükmü DEĞİL)

- Betikler işaretçi sha256'larıyla kıyaslandı: **ayrışma yok**, koşuldu (`pencere_ham.json`
  çekim 2026-09-05T18:41:16Z).
- `giris_once` n=15 / 5 seans → eşik dolu, CI hesaplandı: **[−43,038 ; +80,699]**
  (B=5000, seed=20260812, kümeleme=seans) — hakem kuralının öneri-tetiği girdisi, HÜKÜM DEĞİL.
- `giris_1345` n=8 < 10 → **kıyas YAPILMADI**.
- damga↔ts ayrışan **0** · damga_bilinmeyen **0** · damgasız 13 · olculemedi 0.
- `oneri_tetigi` = **`orneklem_birikimde`** · **`geri_al_onerisi` beyanı YOKTUR.**

## 5. AÇIK KALEM — BU KOŞUMDA DOĞDU (operatör/Rol-1 kararı ister)

**`giris_1345`'te aynı seansın aynı fiyatı iki satır olarak sayılıyor (VRTX, 2026-09-02).**

```
P-2026-09-02-VRTX      ts=2026-09-03T13:45:01Z  fill=556,94  bps=−38,455
P-2026-09-02-VRTX-pead ts=2026-09-03T13:45:02Z  fill=556,94  bps=−38,455
```

İki AYRI plan (temel + `pead` ailesi), AYNI ticker, AYNI dolum fiyatı. Ertesi gün ikincisi
`armed_dropped_already_open` ile düşüyor: **pozisyon tekil, gönderim izi çift.**

Kartın kill listesi kova İÇİ bağımlı gözlemi konuşmuyor (kill#5 yalnız kovalar ARASI birleştirmeyi
yasaklar) — P-3'ün doğduğu boşluğun aynı sınıfı. **Reçete AYNEN koşuldu, sayı düzeltilmedi:**
ölçüm oturumu kural seçmez ve sayıya bakarak kural koymak ön-kayıt disiplinini deler.

ETKİ BEYANI (hüküm değil): tekilleştirilseydi `giris_1345` n=8→7, medyan ve eşik hükmü
DEĞİŞMEZDİ. Kalem şimdi kayda geçirilmeli — eşik dolduktan sonra konacak bir tekillik kuralı,
tam olarak P-3'ün yasakladığı şey olur.

## 6. Karta işlenmesi ÖNERİLEN blok (Rol-1 işler; ölçüm oturumu karta YAZMADI)

`research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml` sonuna, yeni anahtar:

```yaml
hafta_kosum_4_2026_09_05: >
  HAFTALIK KOŞUM #4 (zamanlanmış görev `edg042-friksiyon-haftalik`, ölçüm oturumu; Rol-1 işledi).
  Artefakt: research/olcumler/edg042_kosum_2026-09-05/ (snapshot sha 5b015842…, çekim
  2026-09-05T18:39:20Z, goal.slippage_bps=5 künyeli). Reçete R3/AYRIK (kart işaretçisi),
  betikler bayt-özdeş (a846449e… / 1787a9ff…). Salt-okunur; canlıya ve state/'e tek bayt
  yazılmadı. SONUÇ — DÖRT KOVA DA EŞİK ALTINDA, BETİMLEYİCİ, CI yok, karar kuralı uygulanmadı,
  status measuring:
    giris_once  n=15 / 5 seans · medyan +16,131 · p25/p75 −26,397/+67,659 · seans payı %33,3
                (KALICI TABAN — koşum #3'e göre BİREBİR sabit; kol 08-23'te emekli oldu)
    giris_1345  n=8  / 5 seans · medyan +12,476 · p25/p75 −38,455/+192,589 · seans payı %37,5
    cikis_hedef n=6  / 2 seans · medyan −4,21   · seans payı %66,7 → kill #7 ŞERHİ ZORUNLU
    cikis_stop  n=7  / 6 seans · medyan +2,496  · seans payı %28,6 · SEANS EŞİĞİ DOLDU (n bağlayıcı)
    olculemedi 0 (üç kovada da) · kill denetimi sekizde sekiz temiz (KOMUT.txt [4]).
  KOŞUM #3'E GÖRE DEĞİŞİM: giris_1345 n 2→8 (+6, 3 yeni plan-günü: 08-28 NOW · 09-01 CF/MPC ·
  09-02 REGN/VRTX×2) ve medyan +210,07→+12,476 — DÜŞÜŞ HÜKÜM DEĞİLDİR: önceki değer n=2
  üzerineydi, yeni altı satırın dördü modelin altında/yakınında, biri (NOW +286,1) yine büyük
  pozitif; dağılım vahşi kalıyor. cikis_stop n 4→7, seans 3→6 (eşik doldu). cikis_hedef İKİ
  HAFTADIR SABİT (n=6/2 seans) — hedef çıkışı üretilmiyor, izdüşüm verilemez (hız sıfır).
  EŞİĞE KABA MESAFE (izdüşüm, ölçüm DEĞİL): giris_1345 22 dolum eksik — bu haftanın hızıyla
  (1,2 dolum/seans) ~3,7 hafta, kartın 08-31'de ölçtüğü hızla (0,40) ~11 hafta; bant bu yüzden
  iki uçlu. cikis_stop 8 dolum eksik → ~2,7 hafta. cikis_hedef: İZDÜŞÜM YOK (hız 0).
  EK hakem (EXE-2026-009, H2/ts): giris_once n=15 CI [−43,038 ; +80,699] · giris_1345 n=8 < 10
  → kıyas yapılmadı · damga↔ts ayrışan 0 · damga_bilinmeyen 0 · oneri_tetigi
  orneklem_birikimde · geri_al_onerisi YOK.
  YENİ AÇIK KALEM (P-3'ün kardeşi, kart bunu KONUŞMUYOR): giris_1345'te 2026-09-02 VRTX İKİ
  satırla temsil ediliyor — P-2026-09-02-VRTX ve P-2026-09-02-VRTX-pead, aynı fill (556,94) ve
  aynı bps (−38,455); ertesi gün ikincisi armed_dropped_already_open ile düşüyor, yani pozisyon
  TEKİL gönderim izi ÇİFT. Kartın kill#5'i yalnız kovalar ARASI birleştirmeyi yasaklar, kova İÇİ
  bağımlı gözlemin kuralı YOKTUR. Reçete AYNEN koşuldu, sayı DÜZELTİLMEDİ (ölçüm oturumu kural
  seçmez). Etki beyanı: tekilleştirilseydi n=8→7, eşik hükmü değişmezdi. Kural EŞİK DOLMADAN
  konmalıdır ya da hiç konmamalıdır — P-3'ün aynı gerekçesi. OPERATÖR KALEMİ.
```

## 7. ROADMAP satır önerileri (Rol-1 işler)

**Ö-54 / TSK-071 satırının (`ROADMAP.md:579`) sonuna eklenecek:**

> → 🔁 **KOŞUM #4 2026-09-05 18:39Z** (`edg042_kosum_2026-09-05/`, snapshot `5b015842…`, R3/AYRIK):
> dört kova da EŞİK ALTINDA → hükümlü koşum tetiklenmedi, CI yok, `status: measuring`.
> `giris_once` **n=15 / +16,131 BİREBİR SABİT** (kalıcı taban doğrulandı — kol 08-23'te emekli) ·
> **`giris_1345` n=2→8 / seans 2→5, medyan +210,1 → +12,5** (düşüş HÜKÜM DEĞİL: önceki n=2 idi;
> yeni altı satırın dördü modelin altında/yakınında, NOW +286,1 yine büyük pozitif; p25/p75
> −38,5/+192,6) · `cikis_hedef` **İKİ HAFTADIR SABİT n=6/2 seans** (izdüşüm verilemez, hız 0;
> kill #7 şerhi %66,7 ile zorunlu) · **`cikis_stop` n=4→7, seans 3→6 — SEANS EŞİĞİ DOLDU**,
> bağlayıcı yalnız n (8 eksik ≈ 2,7 hafta). Eşiğe kaba mesafe `giris_1345`: 22 dolum eksik →
> bu haftanın hızıyla (1,2/seans) ~3,7 hafta, kartın ölçtüğü hızla (0,40) ~11 hafta.
> Hakem (EXE-009/H2): `orneklem_birikimde`, geri-al önerisi YOK, damga↔ts ayrışan 0.
> ⛔ **YENİ AÇIK KALEM (P-3 kardeşi):** `giris_1345` 2026-09-02 VRTX'i İKİ satır sayıyor
> (temel + `pead`, aynı fill/bps; ertesi gün `armed_dropped_already_open`) — pozisyon tekil,
> gönderim izi çift. Kartın kill#5'i kova İÇİ bağımlı gözlemi KONUŞMUYOR. Sayı düzeltilmedi
> (ölçüm oturumu kural seçmez); tekilleştirmede n=8→7, eşik hükmü değişmezdi. **Kural eşik
> dolmadan konmalı** — operatör kalemi.

**§7 (Ö-54 kronoloji defteri, `ROADMAP.md:3656` civarındaki blok) tek satırı:**

> - **2026-09-05 `EDG-2026-042` HAFTALIK KOŞUM #4 (`Ö-54`):** dört kova da eşik altında →
>   hükümlü koşum TETİKLENMEDİ, `status: measuring` sürüyor. `giris_1345` n=2→8 (medyan
>   +210,1→+12,5 — n=2'lik önceki değerin düzeltilmesi, hüküm değil), `cikis_stop` n=4→7 ve
>   **seans eşiği doldu** (bağlayıcı yalnız n), `cikis_hedef` iki haftadır sabit (hız 0 →
>   izdüşüm verilemedi), `giris_once` kalıcı taban olarak BİREBİR sabit. Hakem
>   `orneklem_birikimde`, geri-al önerisi yok. YENİ AÇIK KALEM: `giris_1345`'te aynı seansın
>   aynı dolumu iki plan (`VRTX` + `VRTX-pead`) üzerinden çift sayılıyor — kova İÇİ bağımlı
>   gözlemin kuralı kartta YOK, P-3'ün kardeşi, operatör kalemi.

## 8. Görev durumu

Bitiş kontrolü (görev [1]): eşiğe ULAŞABİLEN üç kova (`giris_1345` · `cikis_hedef` ·
`cikis_stop`) **hükümlü verdict TAŞIMIYOR** → zamanlanmış görev **KAPANMAZ**, sıradaki koşum
2026-09-12.
