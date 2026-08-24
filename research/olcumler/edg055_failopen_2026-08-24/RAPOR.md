# EDG-2026-055 — earnings fail-open gerçekleşmiş bedeli · RETRO SAYIM

**Tarih:** 2026-08-24 · **Rol:** ölçüm ajanı · **Kart:** `research/cards/EDG-2026-055-earnings-fail-open.yaml`
(ön-kayıtlı, eşik donmuş, `r1_pit_derinligi_serhi_2026_08_24` şerhli)
**Hücre:** `failopen_retro_sayim` (TEK hücre, K += 1) · **Çıktı:** `sonuc.json` · **Betik:** `olc.py`

> **BU RAPOR HÜKÜM İÇERMEZ.** Sayılar aşağıdadır; damgayı ve hükmü Rol-1 işler. Karta
> dokunulmadı (salt-okuma), `state/` altına yazılmadı, motor dosyası değiştirilmedi, git
> koşulmadı.

---

## 0. PAYDA — YÜZEYDE (R1 şerhinin istediği dört sayı)

| alan | değer |
|---|---|
| **`N_giris`** (PIT penceresinde CANLI giriş) | **10** — 6 kapanmış `live_paper` + 4 açık pozisyon |
| **`N_failopen_kapsam`** (bunların fail-open damgalısı) | **0** |
| **pencere** | **2026-08-03 → 2026-08-17** |
| **snapshot sayısı** | **10** (hepsi `nasdaq`; fetch günleri 08-03,04,05,06,07,10,12,13,14,17) |

**Ateşlenen R1 dalı: DAL 2** — `N_giris ≥ 1` AMA `N_failopen_kapsam = 0`.
Kartın kendi metniyle: bu dal **BETİMLEYİCİ** damgadır, "ölçülmüş-ret" **DEĞİLDİR**.
`success_metric` (vaka N + toplam R üzerinden karar) bu dalda **ÇALIŞTIRILMAZ**; hücre yine de
hesaplandı ve aşağıda raporlanıyor.

`N_kapsam_olculemedi = 0` — 10 girişin hepsinde girişten ÖNCE alınmış bir PIT anlık görüntüsü
vardı; kapsam sorusu hiçbir giriş için cevapsız kalmadı.

---

## 1. HÜCRE — `failopen_retro_sayim`

| alan | değer |
|---|---|
| `vaka_n` | **0** |
| `vaka_toplam_r` | **null** — vaka kümesi boş; `0.0` yazmak yokluğu ölçüm gibi gösterirdi |
| `vaka_toplam_pnl_dolar` | null (aynı neden) |
| `vaka_olculemedi_n` | 0 |

Vaka yüklemi (kartın tanımı, değiştirilmedi): *giriş anında sembol takvim kapsamı DIŞINDA*
(**fail-open damgası**) **×** *sonradan öğrenilen gerçek rapor tarihi girişten ≤ 5 gün sonra*
(`BLACKOUT_DAYS = 5`, kapının kendi eşiği). İlk çarpan 10 girişin hiçbirinde doğru olmadığı için
vaka kümesi boştur — yani `vaka_n = 0` sayısı, **ikinci çarpanın ölçüldüğü değil, birinci çarpanın
hiç tetiklenmediği** bir penceredir.

---

## 2. GİRİŞ TABLOSU (10 satır — paydanın tamamı, gizlenen satır yok)

`asof` = kapının o girişte elinde olan takvim = `fetch_date < giriş günü` olan SON anlık görüntü.
(Tazelemeler ≈20:1x UTC, yani seans KAPANIŞINDAN sonra; girişler ≈13:30 UTC, açılışta. Aynı günün
anlık görüntüsünü kullanmak geleceği sızdırırdı.)

| kimlik | sembol | giriş | durum | asof snap | kapsam (PIT) | asof rapor tarihi | ileri çapa? | vaka | R |
|---|---|---|---|---|---|---|---|---|---|
| T00098 | NUE | 2026-08-06 | kapalı | 2026-08-05 | known | 2026-07-27 | hayır | hayır | −0,993 |
| ACIK-EMR | EMR | 2026-08-06 | açık | 2026-08-05 | known | 2026-08-04 | hayır | hayır | — |
| ACIK-BKNG | BKNG | 2026-08-06 | açık | 2026-08-05 | known | 2026-08-04 | hayır | hayır | — |
| ACIK-AMGN | AMGN | 2026-08-06 | açık | 2026-08-05 | known | 2026-08-04 | hayır | hayır | — |
| T00096 | ALL | 2026-08-07 | kapalı | 2026-08-06 | known | 2026-08-05 | hayır | hayır | −1,028 |
| T00097 | VLO | 2026-08-10 | kapalı | 2026-08-07 | known | 2026-07-30 | hayır | hayır | +0,918 |
| T00099 | MRK | 2026-08-14 | kapalı | 2026-08-13 | known | 2026-08-04 | hayır | hayır | +3,379 |
| ACIK-CRM | CRM | 2026-08-14 | açık | 2026-08-13 | known | 2026-08-26 | **evet** | hayır | — |
| T00100 | MRNA | 2026-08-17 | kapalı | 2026-08-14 | known | 2026-07-31 | hayır | hayır | +14,675 |
| T00101 | HUM | 2026-08-17 | kapalı | 2026-08-14 | known | 2026-07-29 | hayır | hayır | −1,017 |

**Pencere DIŞINDA kalan canlı girişler** (bilerek sayılmadı, beyanlı): T00102 MRVL ve T00103 LLY
(giriş 2026-08-20) ile açık pozisyonlar MRNA/MRK/BDX (giriş 2026-08-20) — PIT arşivi 2026-08-17'de
bittiği için bu girişlerin "giriş anında ne biliniyordu" sorusu arşivden **cevaplanamaz**.

### Neden açık pozisyonlar da paydada
Kaynak damgası (`ledgerstamp`) işlem **kapanırken** basılır; açık bir pozisyonun damgası henüz
yoktur ama **girişi olmuştur**. Paydayı yalnız kapanmışlardan kurmak örneklemi sessizce 6'ya
düşürürdü. İki alt sayı ayrı ayrı da yüzeyde: `N_giris_kapali_live_paper = 6`,
`N_giris_acik_pozisyon = 4`.

---

## 3. ÇAPRAZ DOĞRULAMA — PIT yeniden kurulumu ↔ planın KENDİ damgası

10 girişin 5'inin planı canlı plan defterinde bulundu (`trade_plans` 500 satırlık DÖNEN defter;
düşen plan için damga **None** kalır ve UYDURULMAZ). Bulunan 5 planın hepsinde kaydedilmiş
`gate_checks.earnings_blackout.coverage = "known"`.

**Çelişki: 0.** PIT yeniden kurulumu, planın kendi damgasıyla bulunabilen her satırda birebir
aynı sonucu verdi — yani hüküm yolundaki kapsam sorusu iki bağımsız kanıtla aynı yeri gösteriyor.

---

## 4. BETİMLEYİCİ — karar kuralına GİRMEZ

**(a) Pencere R'si (bağlam):** kapanmış 6 canlı işlemin toplam R'si **+15,934**. Bu sayı hücrenin
değil paydanın betimlemesidir; vaka kümesi boş olduğu için kartın "aynı dönemin fail-open-olmayan
işlemlerine göre dağılım farkı" kalemi **kıyaslanacak ikinci küme olmadığından ölçülemedi**.

**(b) BAYAT ÇAPA — 10 girişin 9'u.** Bu kartın eksenine göre "kapsam VAR" (`known`) sayılan 9
girişte, giriş anında bilinen **tek rapor tarihi GEÇMİŞTEYDİ** (NUE 07-27, HUM 07-29, VLO 07-30,
MRNA 07-31, EMR/BKNG/AMGN/MRK 08-04, ALL 08-05). Yalnız CRM'in ileri çapası vardı (2026-08-26).
Yani karartma kapısı bu 9 girişte sembolü **tanıyordu** ama ileriye bakacak çapası yoktu; `known`
etiketiyle geçmek ile fail-open ile geçmek, kapının **davranışı** bakımından bu satırlarda
ayırt edilemez. **Bu olgu kartın fail-open ekseninin DIŞINDADIR** — sayıldı, hüküm taşımıyor,
eşiği yok; ayrı bir kalem olarak Rol-1'in önüne konuyor.

**(c) MARUZİYET VEKİLİ (kartın `features_asof` ek kalemi) — BUGÜNKÜ takvimi kullanır, bilerek
HÜKÜMSÜZDÜR.** Evren 251 · bugün takvimde 216 · **kapsam dışı 35** (WP4 A3'ün listesiyle birebir
aynı çıktı, bağımsız yeniden üretim). Bu 35 sembolde tarihsel defterin **127/893 işlemi = %14,22**.
Bu blok bir geçmiş girişin kazanç gününe denk gelip gelmediğini **SORMAZ**; yalnız bugünkü
kapsam-dışı listesinin defterdeki payını sayar. Hüküm yolu **salt PIT**tir (bkz. §5 kill #1).

---

## 5. KILL LİSTESİ — dördü de ayrı ayrı kontrol edildi

| # | kill ölçütü | sonuç | kanıt |
|---|---|---|---|
| 1 | bugünkü takvimle geçmiş yargılandı mı → geçersiz | **HAYIR** | Hüküm yolundaki iki soru da YALNIZ `history/earnings_snapshots.jsonl`'dan yanıtlandı: kapsam = `fetch_date < giriş` olan son anlık görüntü; gerçek rapor = `fetch_date ≥ giriş` anlık görüntülerinin birleşimi. `state/earnings.csv` (bugünkü takvim) betikte YALNIZ §4(c) hükümsüz maruziyet vekilinde okunur, vaka yükleminde okunmaz. |
| 2 | fail-open damgası olmayan işlem vakaya sayıldı mı → geçersiz | **HAYIR** | Vaka yüklemi `fail_open is True` şartına bağlı; `False` ya da `None` olan satır vakaya giremez (`None` ayrı sayaçta: `N_kapsam_olculemedi`, `vaka_olculemedi_n`). Zaten `vaka_n = 0`. |
| 3 | kapı tasarımına dokunuldu mu → geçersiz | **HAYIR** | Betik yalnız okur. `meridian/` altında hiçbir dosya değişmedi; `meridian` **import bile edilmedi** (`REPLAY_UNIVERSE` kaynaktan `ast` ile okundu, yan etkisiz). Yazılan tek yer `research/olcumler/edg055_failopen_2026-08-24/`. |
| 4 | ikinci eksen/alt-dilim eklendi mi → geçersiz | **HAYIR** | Hükümlü hücre TEK: `failopen_retro_sayim` (K += 1). Diğer her sayı `sonuc.json`da `betimleyici_hukumsuz` altında toplanmıştır ve **eşiksizdir**; hiçbiri karar kuralına girmez. |

---

## 6. VERİ TABANI VE TAZELİK BEYANI

| kaynak | ne | damga |
|---|---|---|
| `backups/a1/state-2026-08-22.tar.gz` | A1'in (canlı sistem) günlük `state` yedeği, `ops/pull-a1-backups.sh` ile çekilmiş VM-dışı yerel kopya | arşiv üretimi 2026-08-23 02:35 (A1'de); yerel dosya damgası aynı (rsync `-a`) |
| ↳ `state/history/earnings_snapshots.jsonl` | PIT takvim arşivi — **hüküm yolu** | mtime 2026-08-17 23:18 · 10 satır |
| ↳ `state/meridian.db` | canlı defter: `trades` (893) + `portfolio` (7 açık pozisyon) | mtime 2026-08-23 02:29 |
| ↳ `state/earnings.csv` | YALNIZ hükümsüz maruziyet vekili | mtime 2026-08-17 23:18 |

**YEREL `state/` KULLANILMADI** — bayat ayna (çoğu dosya 2026-07-30; `trades.jsonl` 95 satırlık
tohum defteri, canlı 893'ü içermiyor). Yedekten yalnız üç üye geçici bir dizine açılır ve koşum
sonunda silinir; repoya ikili dosya bırakılmaz. Yedeğin ve her üyenin sha256'sı `sonuc.json`
`kaynak` bloğunda.

---

## 7. ÖLÇÜLEMEYENLER (uydurma yasağı)

1. **2026-08-03 ÖNCESİ ve 2026-08-17 SONRASI canlı girişler** — PIT arşivi bu iki tarih arasında
   var. Öncesi: arşiv 2026-08-03'te başlıyor, geriye doldurulamaz (kartın `beyanli_sinirlar` (1)).
   Sonrası: 2026-08-20 girişleri (MRVL, LLY, MRNA, MRK, BDX) için "giriş anında ne biliniyordu"
   sorusunun arşivde karşılığı yok. **None + neden.**
2. **Kartın "aynı dönemin fail-open-olmayan işlemlerine göre dağılım farkı" kalemi** — vaka kümesi
   boş olduğu için kıyaslanacak birinci küme yok. **None + neden.**
3. **NUE ve ALL'ın (ve 3 açık pozisyonun) planlarındaki KAYITLI kapsam damgası** — `trade_plans`
   500 satırlık dönen defter, bu planlar düşmüş; canlı olay defterinde de `gate_checks` taşıyan
   bir kayıt bulunamadı. **None + neden** (bu satırlar hüküm yolundan düşmedi: kapsam sorusu PIT
   yeniden kurulumuyla cevaplandı, kayıtlı damga yalnız çapraz doğrulamaydı — §3).
4. **Girişlerin SAAT damgası** — defterde `ts_open` yalnız GÜN. `asof` seçimi bu yüzden
   "aynı günün akşam tazelemesini kullanma" kuralıyla muhafazakâr tarafa kuruldu (§2).

---

## 8. YENİDEN ÜRETİM VE DETERMİNİZM

```
/Users/erdemozturk/AI-Trading/.venv/bin/python \
  /Users/erdemozturk/AI-Trading/research/olcumler/edg055_failopen_2026-08-24/olc.py
```

Betik `datetime.now()` çağırmaz, rastgelelik içermez; ölçüm tarihi ve kaynak yedek literaldir,
`sonuc.json` `sort_keys` ile yazılır.

**İki koşum, bayt-özdeş:**
`sha256(sonuc.json) = 7460fb5ba1813f182694c74cc02556bb44944719dcb5fbcb74dda5cce1635518` (her iki
koşumda aynı; `cmp` farksız).

**Kapsam testleri (tam suite DEĞİL):**
```
.venv/bin/python -m pytest tests/test_kart_kimlik_v219.py tests/test_kart_hukum_damgasi_v251.py \
  tests/test_codelaw_kor_nokta_v214.py -p no:randomly --no-header -rf
→ 54 passed
```
