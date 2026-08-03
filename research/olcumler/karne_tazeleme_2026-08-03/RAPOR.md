# KARNE TAZELEME — "sistem geriye dönük kâr ediyor mu?" güncel kodla yeniden üretim

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı · **Hüküm sahibi:** Rol-1
**Kart:** YOK ve gerekmiyor — bu bir kenar-hipotezi değil, sistemin KENDİ muhasebesinin güncel kodla
yeniden üretimidir. Eşik İCAT EDİLMEDİ, hüküm CÜMLESİ KURULMADI: aşağıda yalnız sayı, kaynak ve
tek-değişken atfı var.
**Salt-ölçüm beyanı:** her koşum kendi kum havuzunda (`MERIDIAN_ROOT` + `config.STATE` yönlendirmesi),
gerçek `state/`e YAZILMADI (kanıt §6), canlıya (ssh) dokunulmadı, git komutu koşulmadı.

---

## 0. NE ÖLÇÜLDÜ, HANGİ MOTORLA (iddia değil damga)

`research/olcumler/karne_tazeleme_2026-08-03/kod_damgasi.json`:

| motor | .py dosya | sha256(16) | ne |
|---|---|---|---|
| `depo/meridian` | 93 | `b9cb663ba54fdb4d` | bugünkü çalışma ağacı |
| `sandbox_guncel` | 93 | **`b9cb663ba54fdb4d`** | depo ile **BAYT EŞİT** — "SONRA" kolları bunu koştu |
| `sandbox_taban` | 91 | `b7d617e91c09f23b` | `karne_olcum` ölçümünün HEAD **505603b** kopyası — "ÖNCE" kolu |
| `sandbox_atrsiz` | 93 | `52369ceada6e9df1` | `sandbox_guncel` + **TEK SATIR** fark (tanı kolu, §3.1) |

**Koşum yolu deponun standardıdır, yeni motor YAZILMADI:** `backtest.walk_forward` (harness
`kosum.py` + `kosum_kanca.py` — `karne_olcum` ölçümünün betikleri, bu dizine AYNEN kopyalandı) ve
cf tarafında `cf_backfill.run` (`cf_kosum.py` yalnız `MERIDIAN_ROOT`u kurup üretim fonksiyonunu
çağırır). Kancalar hüküm değiştirmez; `fill_entry`e geçen `reject_out={}` motorun kendi
parametresidir.

**R1 geometrisi (dört kolda BİREBİR, `karne_olcum` ile de aynı):** IS `2022-01-01` → OOS
`2024-01-01` → `2026-04-30` → holdout `2026-07-30`; foldlar `[2024-01-01, 2024-10-01, 2025-07-01,
2026-04-30]`; embargo 10. Search dilimi `2024-01-11 → 2025-08-18` (span 585 gün), confirm sonu
`2026-04-30`. `strategy_version = 3`, kaynak `state/strategy.yaml:version` (sabit yazılmadı).
Evren: `REPLAY_UNIVERSE` 251 → **yüklenen 250** (`FISV` için `state/bars/fisv.csv` YOK); replay
takvimi 2022-01-03 → 2026-07-29; barlar canlı önbellekten SEMBOLİK BAĞ ile salt-okunur.

**Dört kol (tek-değişken tasarımı):**

| kol | motor | state | tek fark |
|---|---|---|---|
| `taban` | 505603b kopyası | `karne_olcum`un 2026-08-01 state'i | — (ÖNCE'nin yeniden üretimi) |
| `atrsiz` | bugün − 1 satır | bugünün state'i | `replay`de `fill_entry`e `atr=` GEÇİRİLMEZ |
| `heat45` | bugün | bugünün state'i, `heat_hard_r` **4.5** | ısı tavanı |
| `guncel` | bugün | bugünün state'i (`heat_hard_r` **5.0**) | — (SONRA) |

**Determinizm kapısı GEÇTİ:** `taban` kolu, 2026-08-01 raporunun `tam_guncel` kolunu **birebir**
üretti — `trade_digest_tum`, `trade_digest_search`, `plan_digest`, `equity_digest` DÖRDÜ DE aynı
(`ba44ae938531…`, `b8ee02d79929…`). Yani aşağıdaki "önce" sütunu bir alıntı değil, bu sandbox'ta
yeniden üretilmiş bir ölçümdür ve fark varsa kurulumdan değil koddan gelir.

---

## 1. ÖNCE / SONRA TABLOSU

### 1a. Otoriter walk-forward karnesi (R1 geometrisi, sv=3)

| alan | **ÖNCE** (`taban`, 505603b + 08-01 state) | **SONRA** (`guncel`, bugün) | fark |
|---|---|---|---|
| oos_score | 0,0579 | **0,0196** | −0,0383 |
| **PARA-v3 (search)** | **0,1605** | **−0,0037** | **−0,1642** |
| is_score | 0,0651 | 0,0651 | **0,0000** |
| holdout_score | None (5/30 işlem) | None (6/30 işlem) | — |
| full_detail score | 0,0748 | 0,0894 | +0,0146 |
| n işlem (toplam replay) | 201 | 147 | −54 |
| n işlem (OOS) | 130 | 75 | −55 |
| n işlem (search) | 103 | 61 | −42 |
| n işlem (confirm) | 22 | 13 | −9 |
| avg_r (OOS) | 0,012 | −0,015 | −0,027 |
| win_rate (OOS) | 0,354 | 0,333 | −0,021 |
| sharpe (OOS) | 0,226 | −0,043 | −0,269 |
| max_drawdown (OOS, kapanmış-işlem) | 0,0717 | 0,0735 | +0,0018 |
| total_return (OOS) | 0,0319 | −0,0046 | −0,0365 |
| fold_avg_r ortalaması | 0,0608 | 0,0122 | −0,0486 |
| süre (sn) | 1391,4 | 1488,7 | — |

### 1b. Aynı koşumun PARA defteri (kırpılmamış dolar) ve replay işlem defteri

| alan | **ÖNCE** | **SONRA** | fark |
|---|---|---|---|
| PARA-v3 search skoru | 0,1605 | −0,0037 | −0,1642 |
| search dilimi realize $ (`realized_usd.pnl_usd`) | +6.901,93 | **−161,89** | −7.063,82 |
| search hedefi $ (`hedef_usd`, %25/yıl × 585 gün) | 42.995,22 | 42.995,22 | 0 |
| search total_return | 0,069 | −0,0016 | −0,0706 |
| search max_drawdown | 0,053 | 0,0492 | −0,0038 |
| PARA-v3 bileşimi | tek terim: `para` = kıs(pencere getirisi / hedef) | aynı | yasa DEĞİŞMEDİ (`shadowlaw.py` bayt-aynı) |
| **replay defteri net $** | **+2.492,87** | **−1.182,15** | **−3.675,02** |
| profit factor (replay defteri) | 1,0499 | 0,9646 | −0,0853 |
| kazanan / kaybeden | 73 / 128 | 52 / 95 | — |
| ödenen friksiyon $ | 2.957,70 | 1.735,61 | −1.222,09 |
| sermaye eğrisi sonu (100.000$ başlangıç) | 102.492,85 | 98.817,86 | −3.674,99 |
| tam pencere toplam getiri | +%2,49 | **−%1,18** | −%3,67 |
| tam pencere M2M maks düşüş | 0,0720 | 0,0739 | +0,0019 |
| yıllık vol (tam pencere) | 0,0579 | 0,0509 | −0,0070 |
| dolum çağrısı → dolan | 237 → 201 | 176 → 147 | — |
| dolum retleri | `entry_missed_limit` 26 · `max_chase` 6 · `open_below_stop` 3 · `qty_zero` 1 | `entry_missed_limit` 23 · `max_chase` 3 · `open_below_stop` 3 | — |

### 1c. cf (karşı-olgusal) defteri

| alan | **ÖNCE** — canlı snapshot `state/counterfactuals.jsonl` (mtime 2026-07-30) | **SONRA** — güncel kodla yeniden türetim (`cf_backfill.run 2022-01-01→2026-07-30`) |
|---|---|---|
| satır | 7.161 | 8.689 |
| plan satırı (GO/REVIEW/NO_GO) | 2.173 | 3.815 |
| near-miss satırı | 4.988 | 4.874 |
| verdict | GO 782 · REVIEW 1.060 · NO_GO 331 | GO 828 · REVIEW 1.317 · NO_GO 1.670 |
| `taken` | 849 | 694 |
| çözülen satır (R'si olan) | 7.053 | 8.502 |
| **ortalama R** | **0,0450** | **0,0446** |
| kazanan oranı | 0,4422 | 0,4206 |
| toplam R | 317,58 | 379,35 |
| tarih aralığı / gün | 2022-01-03 → 2026-07-23 / 1.011 | 2022-01-03 → 2026-07-27 / 1.083 |
| kazanç kapısı sayacı | (alan yoktu) | `{"plan": 3839, "olculemedi_cf": 3839}` |

> Bu iki sütun TEK BİR değişkenin farkı DEĞİLDİR: canlı snapshot 2026-07-21…30 arasında, o
> günün koduyla, artımlı olarak biriktirildi; sağdaki sütun bugünün koduyla tek seferde
> türetildi. Aradaki her farkı tek bir değişikliğe bağlamak bu ölçümün kapsamı dışındadır —
> tek-değişken atfı §3.2'dedir ve orada 8.689 satırın **1**'ini açıklar.

### 1d. Canlı karne yüzeyi (aynı soruya BAŞKA bir defterden bakış)

Kaynak: `state/trades.jsonl` (mtime 2026-07-23; 95/95 satır re-seed kökenli, mühendislik günlüğü
§546) + `state/equity_curve.json`; `analytics.result_verdict` / `analytics.profit_waterfall`
snapshot KOPYASI üzerinde koştu (`analiz.py`, çıktı `once_ozet.json`).

| alan | değer |
|---|---|
| n işlem | 95 |
| net $ | −5.542,09 |
| işlem başına ort. $ | −58,34 · blok-bootstrap %95 CI [−137,75; +14,53] (sıfırı dışlamıyor) |
| profit factor | 0,5666 |
| maks düşüş | 0,0804 (kapanmış-işlem 0,057 · günlük M2M 0,0804) |
| ödenen friksiyon $ | 581,49 |
| `result_verdict` çıktısı (motorun kendi cümlesi) | "0/4 sağlandı (0 zayıf, 4 sağlanmadı, 0 ölçülemedi) — para kanıtlanmadı" |
| profit_waterfall (genel) | sinyal MFE +0,9648R · geri verilen −0,9854R · friksiyon 0,0215R · **net −0,0421R** |

> **BU SÜTUN YUKARIDAKİ KOLLARLA AYNI SİSTEMİ ÖLÇMÜYOR** ve toplanamaz: `trades.jsonl`
> satırlarının hepsi `strategy_version = 4` taşıyor (operatör override, `regime.min_exposure_score
> = 20`), oysa kollar `state/strategy.yaml`ın v3'ünü (aynı anahtar = 40) koşuyor. Tek fark ölçüldü:
> `{"regime.min_exposure_score": [20, 40]}`. Ayrıca defter 2023-01-23 → 2026-07-17 penceresini
> kapsıyor, kollar 2022-01-03 → 2026-07-29'u.

### 1e. Taban-fazlası (baseline excess) — **ÖLÇÜLEMEDİ + neden**

`state/scoreboard.json`: `current_version = 3`; v3 satırının `parent`ı **None**, v4 satırının
`parent`ı da **None** (`source: operator_override`). Ebeveyn olmayınca `ΔS = aday − ebeveyn`
tanımsızdır; `analytics.live_expectancy_ceiling` de kendi ağzıyla **`olculemedi`** diyor:
*"v3 karne satırında `backtest_full.avg_r` YOK — backtest beklentisi ölçülmemiş, tavan
hesaplanamaz"*. Uydurulmuş bir taban yazılmadı.

---

## 2. FARK NEREDE DOĞDU — İLK AYRIŞMA NOKTASI

Kollar 2022-01-03'ten **2024-02-13'e kadar BİREBİR aynıdır** (`is_score` dört kolda da 0,0651 —
IS penceresi 2024-01-01'de biter, ayrışmadan önce). İlk üç ayrışma aynı güne düşer:

| ayrışma | ilk vaka |
|---|---|
| dolum | **2024-02-14 · GE** — `taban`: `dolu` · `guncel`: `entry_missed_limit` |
| plan | **2024-02-14 · P-2024-02-14-EMR** — `taban`de plan YOK, `guncel`de REVIEW |
| işlem | `taban` 2024-02-14 GE · `guncel` 2024-02-15 EMR |

Bu tarihten sonrası yol-bağımlıdır: kaçan tek dolum, o günün slot dolumunu ve ertesi günlerin
aday sıralamasını değiştirir. Bu yüzden "−54 işlem"in tamamı 54 ayrı karar değil, **bir kararın
zincirlemesidir**.

---

## 3. FARK-ATFI (tek-değişken aç/kapa koşumlarıyla ÖLÇÜLDÜ)

### 3.1 Walk-forward tablosu — atıf tam

| değişiklik | nasıl ölçüldü | oos_score | PARA-v3 | n işlem | net $ |
|---|---|---|---|---|---|
| **E1 giriş-limitinin ATR bacağı** (`backtest.replay` → `fill_entry(atr=armed_atr.get(t))`, C11/C18) | `atrsiz` kolu: bugünün motoru, YALNIZ bu argüman sökülü | **0,0579 → 0,0196** | **0,1605 → −0,0037** | **202 → 147** | **+2.481,40 → −1.182,15** |
| **replay-PIT düzeltmesi** (89d4497 — bugünün takvimi tarihsel plana uygulanmıyor) | `taban` ↔ `atrsiz` (ikisi de ATR'siz; tek fark bu) | 0,0579 → 0,0579 (**0**) | 0,1605 → 0,1605 (**0**) | 201 → 202 (**+1**) | +2.492,87 → +2.481,40 (**−11,47**) |
| **ısı tavanı 4,5R → 5,0R** | `heat45` ↔ `guncel` (tek fark `goal.limits.heat_hard_r`) | **0** | **0** | **0** | **0** |
| **kardeş-PIT düzeltmesi** (bugün: `cf_backfill` + `shadow_variants`) | yapısal | **0** | **0** | **0** | **0** |
| **earnings takvim-düzeyi fail-closed** (A1, `calendar_untrustworthy`) | yapısal | **0** | **0** | **0** | **0** |
| **turnover w=0** | `atrsiz` kolu (turnover'lı motor) taban skorlarını BİREBİR üretti | **0** | **0** | **0** | **0** |
| `bounds.yaml` değişiklikleri (turnover satırı eklendi, `regime.spy_sma_gate` düştü) | yapısal | **0** | **0** | **0** | **0** |

**Kanıtlar, sırayla:**

1. **ATR bacağı (baskın kalem).** `atrsiz` kolu — bugünün motoru, `backtest.replay`de
   `fill_entry`e `atr=` geçirilmeyen TEK satırlık tanı sürümü — `taban`ın skorlarını **birebir**
   üretti: oos 0,0579 · PARA-v3 0,1605 · is 0,0651 · oos_n 130 · search_n 103 · avg_r 0,012 ·
   win_rate 0,354 · sharpe 0,226 · maxDD 0,0717 · total_return 0,0319 · `trade_digest_search`
   `taban`la AYNI. Yani tablodaki skor farkının **tamamı** bu argümandır. Mekanizma
   `broker.fill_entry` sözleşmesinde yazılı: *"`atr` … None = ölçülemedi → limit yalnız yüzde
   tavanıyla kurulur"*; ATR verilince limit `tetik + min(0,5×ATR, %1×tetik)` olur, yani
   **daralır** ve daha çok plan `entry_missed_limit` ile kaçar (dolum çağrısı 237→176).
   Bu, replay'in canlı icra yasasına (C13: `loop.py` de ATR geçiriyor, `broker.py:296`) hizalanması
   sonucudur — kapsam beyanı, hüküm değil.
2. **replay-PIT.** `taban` ↔ `atrsiz` işlem kümesi farkı **tek satır**: `MMM`, giriş 2026-07-22,
   çıkış 2026-07-24, R −0,162, −11,47$, `exit_reason: regime_flip`. Kaynağı `taban`ın plan
   defterindeki TEK karartma vetosu: `P-2026-07-21-MMM|NO_GO`
   ("kazanç öncesi karartma (earnings blackout)"). `atrsiz`/`heat45`/`guncel` kollarında bu veto
   **0** kez geçer. Plan defteri de bunu tek satırda gösterir: `taban` 93 GO / 353 REVIEW / 145
   NO_GO → `atrsiz` 93 GO / **354** REVIEW / **144** NO_GO (aynı 591 plan; tek fark MMM'in
   NO_GO→REVIEW dönüşü). Vaka OOS penceresinin (bitiş 2026-04-30) DIŞINDA, holdout içinde kaldığı
   için raporlanan skorların hiçbirine girmez; holdout skoru zaten `None` (6/30 işlem). Para
   tarafındaki karşılığı: n 201→202, net +2.492,87→+2.481,40 (−11,47$), PF 1,0499→1,0496.
   **DİKKAT (ölçüm tuzağı, kayda geçsin):** `gate_reasons` metninde "karartma" kelimesini aramak
   YANLIŞ sayı verir — fail-open kapsam NOTU da ("… karartma kapısı KONTROL EDEMEDİ") aynı kelimeyi
   taşır ve iki kolda da 153/164 planda geçer. Veto sayımı TAM metinle ("kazanç öncesi karartma")
   yapılmalıdır; `karsilastir.py` bu ayrımı yapar.
3. **Isı 4,5→5,0R.** `heat45` ve `guncel` kolları AYNI `plan_digest` (`e907ac686452`), AYNI
   `trade_digest` (`4676800e30f1`), AYNI verdict dağılımı (GO 123 · REVIEW 399 · NO_GO 117) verdi.
   Eşik ÇALIŞIYOR ama BAĞLAMIYOR: "portföy ısısı sert tavanı … aşıyor" gerekçesi 4,5R'de **83**,
   5,0R'de **27** planda üretildi — 56 planlık farkın hiçbiri verdict değiştirmedi, çünkü o planlar
   zaten başka bir sert kalemle (ağırlıklı "max 5 pozisyon dolu") NO_GO'ydu. Bağlayıcı vaka: **0**.
4. **Kardeş-PIT ve A1 fail-closed — yapısal sıfır.** `backtest.py` `cf_backfill`i de
   `shadow_variants`ı da import etmez (grep: 0 çağrı); `earnings.calendar_untrustworthy` yalnız
   `loop.py` ve `scheduler.py`de geçer, replay yolunda YOKTUR. Yani bu iki kalemin walk-forward
   tablosuna etkisi ölçüm gerektirmeden sıfırdır.
5. **turnover w=0 — çivilendi ve ölçüldü.** `state/strategy.yaml`da `entry.w_turnover` YOK
   (bounds'ta var, arama uzayında). `atrsiz` kolu turnover kodunu TAŞIYAN motorla koştu ve
   505603b'nin skorlarını birebir üretti; `tests/test_turnover_kablolama_v149.py` 25/25 yeşil.
   **Uyarı:** `research/edgar_facts/shares_outstanding.csv.gz` sandbox'a bağlanmasaydı bileşen
   "ölçülemedi" (fail-open) yoluna düşecekti; bağ kuruldu ve `edgar_shares_file_missing` uyarısı
   koşumlarda 0 kez çıktı.
6. **`bounds.yaml`.** `backtest.py` `config.bounds`u okumaz (grep: yalnız yerel `fold_bounds`
   değişkeni); bounds arama uzayıdır, walk-forward parametreleri `strategy.yaml`dan gelir ve o
   dosya iki state arasında **bayt-aynıdır** (`diff` rc=0).

### 3.2 cf defteri — kardeş-PIT'in tek-değişken ölçümü

İki cf kolu AYNI kodla, AYNI state ile, AYNI 1.146 seansı koştu; **tek fark** `cf_backfill.py`nin
sandbox kopyasında karartma vetosu satırının açık/kapalı olmasıdır:

| ölçüm | `cf_taban` (ESKİ kod: veto AÇIK) | `cf_guncel` (kardeş-PIT) |
|---|---|---|
| seans / açılan / çözülen | 1.146 / 8.763 / 8.689 | 1.146 / 8.763 / 8.689 |
| kazanç kapısı sayacı | `{"plan": 3839, "eski_kod_takvim_konustu": 2}` | `{"plan": 3839, "olculemedi_cf": 3839}` |
| verdict | GO 828 · REVIEW 1.316 · NO_GO **1.671** | GO 828 · REVIEW 1.317 · NO_GO **1.670** |
| `taken` | 694 | 694 |
| ortalama R / toplam R | 0,0446 / 379,35 | 0,0446 / 379,35 |
| süre (sn) | 3.440,9 | 3.440,8 |

**Satır-satır fark: 8.689 ortak kimlikten 1 tanesi** —
`CF-2026-07-15-STLD-exhaustion_hammer`: `NO_GO` → `REVIEW`, `taken` her iki kolda da `false`.
Yani düzeltme cf defterinin **sonuç** tarafını (R, kazanma oranı, hangi satır alındı) hiç
değiştirmedi; değiştirdiği tek şey **bir satırın hükmünün dürüstlüğüdür**: eski kod 2022-2026
aralığındaki 3.839 planın 2'sine bugünün ileri-pencere takvimini uygulayıp konuşuyordu, yenisi
3.839'unda da "ölçemedim" diyor (`olculemedi_cf`).

Aynı olgunun ikinci, bağımsız ölçümü: canlı cf defterinin 2.173 plan satırına BUGÜNÜN takvimiyle
`in_blackout` uygulandığında **4** satır (%0,18) `True` döner ve bunların defterdeki kayıtlı
verdict'i GO 1 · REVIEW 2 · NO_GO 1'dir — yani aynı satırın cevabı, defterin yazıldığı GÜNE göre
değişiyordu. Kaldırılan tam olarak budur.

---

## 4. ZORUNLU BEYANLAR (okuma bunlar olmadan yapılamaz)

1. **`bars_integrity` `dataset.load` yoluna BİLEREK bağlı DEĞİLDİR.** Kirli dönemler replay'de
   GÖRÜNÜR; operatör kararı bekliyor. Kanonik tüketici ölçüsü bu turda da doğrulandı:
   defterde **61 sembol**, dışlama **57 sembolde** uygulandı, **46.256 satır** ölçümden düştü
   (`cf_backfill.run` çıktısı, iki cf kolunda da birebir; defter rev 1, üretim 2026-07-31T00:01:10).
   Walk-forward kollarında `rows_excluded = 0`'dır — çünkü o yol `measurement_bars`ı hiç çağırmaz
   (`karne_olcum` raporunun ölçtüğü olgu; bu turda kol çıktılarındaki `veri_kapilari.integrity_report`
   ile yeniden görünür).
2. **Survivorship (hayatta-kalan evren).** Replay evreni bugünün sağ-kalan 250 sembolüdür; delist
   olmuş isimler defterde YOKTUR. Yönün ilk ölçülmüş sayısı, EDG-2026-021 kartından (QC
   delist-dahil evren, betimleyici, vekil-delist %18,6 sembol-payı): **@20 tüm +0,48 · hayatta
   +0,54 · delist −1,46** — delist isimler dilimi AŞAĞI çeker. Bu tablodaki getiriler o yanlılığı
   TAŞIR ve büyüklüğü bu veriyle ölçülemez.
3. **Replay iyimserliği ≈ +0,018 (motor sapması).** ROADMAP.md:473'te kayıtlı; backtest skorları
   bu payı içerir. Bu turda yeniden ölçülmedi.
4. **cf sadakat sınırı.** `cf.advance` yalnız `stop_gap / target_gap / stop / target / time_stop`
   simüle eder (`analytics.CF_SIM_EXITS`); canlı motorun 6 çıkış mekanizması (`trail_atr`,
   `breakeven_lock`, `chandelier`, `giveback`, `regime_flip`, `scale_out`) ve 5 friksiyon kalemi
   (`commission_per_share`, `adv_cap`, `price_impact`, `notional_cap`, `derisk_mult`) UYGULANMAZ.
   Ölçülmüş sapma (canlı defter, 2026-07-28): n=89 çift, corr 0,935, ortalama fark **+0,039R**
   (pozitif = simülasyon iyimser).
5. **Canlı-beklenti tavanı ×0,5 okuma kuralı.** `config.LIVE_EXPECTANCY_CAP_MULT = 0,5`: canlıdan
   BEKLENEN tavan = backtest beklentisinin yarısıdır. Yukarıdaki backtest beklentileri bu kuralla
   okunmalıdır. Bugünkü durum `analytics.live_expectancy_ceiling` → **`olculemedi`** (§1e).
6. **İki "geriye dönük kâr" defteri aynı şey değildir** (§1d): walk-forward kolları v3
   parametreleriyle 2022-2026'yı, `trades.jsonl` v4 override'ıyla 2023-2026'yı ölçer.
7. **Holdout skoru dört kolda da `None`** (5-6 kapanmış işlem / 30 asgari) — sıfır değil, tanımsız.
8. **PARA-v3 yasası değişmedi:** `shadowlaw.py` ve `score.py` iki motor arasında **bayt-aynı**.
   Skor farkı yasadan değil, yasaya giren işlem defterinden gelir.

---

## 5. YENİDEN ÜRETİM

```
# 1) Kum havuzu: motor kopyası + state kopyası + bars/research SEMBOLİK BAĞ (salt-okuma)
#    (kosum.py MERIDIAN_ROOT'u kendi dizinine sabitler; config.STATE state_<kol>/'a gider)
cd <sandbox>/motor_guncel && python kosum.py guncel        # SONRA
cd <sandbox>/motor_taban  && python kosum.py taban         # ÖNCE (505603b kopyası)
cd <sandbox>/motor_guncel && python kosum.py heat45        # ısı tanı kolu
cd <sandbox>/motor_atrsiz && python kosum.py atrsiz        # ATR tanı kolu (tek satır sökülü)
python karsilastir.py                                      # -> karsilastirma.json

# 2) cf defteri yeniden türetimi (deponun kendi yolu: cf_backfill.run)
cd <sandbox>/cf_guncel && python cf_kosum.py 2022-01-01 2026-07-30
cd <sandbox>/cf_taban  && python cf_kosum.py 2022-01-01 2026-07-30   # ESKİ veto satırı geri konmuş kopya
python cf_karsilastir.py                                   # -> cf_karsilastirma.json

# 3) ÖNCE sütununun canlı-karne yüzeyi (snapshot KOPYASI üzerinde)
cd <sandbox>/analiz_once && python analiz.py               # -> once.json
```

Bu dizindeki dosyalar: `kollar_imza.json` (dört kolun tam imza/detay bloğu),
`karsilastirma.json`, `cf_karsilastirma.json`, `once_ozet.json`, `kod_damgasi.json`,
`state_parmakizi_sonra.json` ve koşum betikleri (`kosum.py`, `kosum_kanca.py`, `cf_kosum.py`,
`karsilastir.py`, `cf_karsilastir.py`, `analiz.py`).

---

## 6. SALT-ÖLÇÜM KANITI (gerçek `state/`e yazılmadı)

Koşumlardan ÖNCE ve SONRA `state/` ağacının tam parmak izi (dosya yolu → mtime + boyut) alındı:

| | dosya | parmak izi sha256(16) |
|---|---|---|
| önce | 608 | `065b2ad6011d5a81` |
| sonra | 608 | `065b2ad6011d5a81` |

Değişen dosya **0**, yeni **0**, silinen **0** (`state_parmakizi_sonra.json`). Barlar ve
`research/` kum havuzlarına SEMBOLİK BAĞ ile bağlıdır; `dataset.load_cached` ağa çıkmaz ve CSV
yeniden yazmaz. Yazılan her bayt `<sandbox>/state_<kol>/` altındadır. `serve.sh` koşulmadı, ssh
kullanılmadı, git komutu çalıştırılmadı.
