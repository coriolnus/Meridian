# WP-G ÇİFT ÖLÇÜM — SMA-KAPISI (EDG-2026-005) + TURN-OF-MONTH TILT (EDG-2026-006)

*Ölçüm zamanı:* `2026-07-31T07:26:43.513690+00:00` · *Sandbox:* `/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/wpg_olcum`

> SALT-ÖLÇÜM. Depoya ve canlı state'e HİÇBİR yazım yapılmadı; her kol kendi state_<kol>/ dizinine yazdı, barlar canlı önbellekten SALT-OKUNUR okundu (load_cached ağa çıkmaz, CSV yeniden yazmaz).

---

## 0. İKİ HÜKÜM (özet)

| Kart | Aile | Ölçüm hükmü | Operasyonel sonuç |
|---|---|---|---|
| **EDG-2026-005** | SPY 200-SMA yeni-giriş kapısı | **HUKUMSUZ_OLCUM_TASARIMI** | **KAPI_ACILMAZ** |
| **EDG-2026-006** | Turn-of-month maruziyet eğimi | **ARSIV_KILL2** | tilt UYGULANMAZ |

## 1. POZİTİF KONTROL — boru hattı doğrulaması

overlay'siz İKİ koşumun BİREBİR eşitliği. İkiz-1: yamalı motor, knob'lar KAPALI (sma_kapali). İkiz-2: YAMASIZ motor (ref_snapshot) — overlay kodu hiç yok. Aynı barlar, aynı pencere, aynı state. Eşitlik = boru hattı doğrulandı ve yamanın kapalıyken NO-OP olduğu ampirik olarak kanıtlandı.

**Ölçüt:** Search digest EŞİT **ve** Confirm digest EŞİT **ve** on üç sayısal imza alanı eşit. Defter kıyası OOS'un TAMAMINI (Search+Confirm) kapsar; hiçbir dilim kıyasın dışında bırakılmadı.

**GEÇTİ.** İki koşumun işlem defteri imzası BİREBİR aynı:

| Dilim | sma_kapali (yamalı, knob KAPALI) | ref_snapshot (YAMASIZ) | eşit? |
|---|---|---|---|
| Search | `5a826091681e5980…` | `5a826091681e5980…` | EVET |
| Confirm | `50e8c130006e5259…` | `50e8c130006e5259…` | EVET |
| **Search+Confirm (tam OOS)** | `e5d49110bcbc0b3d…` | `e5d49110bcbc0b3d…` | EVET |

Yani overlay kodu KAPALIYKEN motoru hiçbir noktada etkilemiyor; iki kol arasındaki her fark overlay'in KENDİSİNDEN gelir. (Makine hassasiyeti değil, BİT düzeyinde eşitlik.)

#### 1.0.1 `trade_digest_tum` artefaktı — ilk turun YANLIŞ NEGATİFİ (belge)

- **Bulgu:** İlk tur `pozitif_kontrol.gecti=false` verdi ve TEK sebebi `trade_digest_tum` alanıydı. Bu YANLIŞ NEGATİFTİ ve silinmedi, burada belge olarak duruyor.
- **Kök neden:** kosum.py:169 `trade_digest(res.get('_trades_all') or tum_oos)` yazıyor. `_trades_all` anahtarını YALNIZ yamalı motorun walk_forward'ı döndürür (backtest.py:817) ve içinde REPLAY'İN TAMAMI vardır (2022-01-01 → 2026-07-30, 161 işlem). Yamasız motorda o anahtar YOKTUR, `or` dalı devreye girer ve yalnız OOS dilimi hash'lenir (Search+Confirm, 86 işlem). Yani iki hash AYNI POPÜLASYONU hash'lemiyordu: 161 işlem vs 86 işlem.
- **Düzeltme:** Pozitif kontrol artık Search ve Confirm digest'lerinin AYRI eşitliğine bakar; `trade_digest_tum` kıyastan çıkarıldı ama kayıttan çıkarılmadı.

| Alan | değer |
|---|---|
| `sma_kapali.trade_digest_tum` (161 işlem) | `995f1d33a8b8a71932b5f6d7cb0d86e39261878013b8f1aca17f04c21f7c47f1` |
| `ref_snapshot.trade_digest_tum` (86 işlem) | `e5d49110bcbc0b3d956f1e43f5a3f53a6628538fdd6533d93c3aedd503d0c6a8` |
| `sma_kapali` Search+Confirm digest'i (86 işlem) | `e5d49110bcbc0b3d956f1e43f5a3f53a6628538fdd6533d93c3aedd503d0c6a8` |

*ref_snapshot'ın `trade_digest_tum`u, sma_kapali'nin search+confirm digest'iyle BİREBİR AYNIDIR — artefaktın 'yamasız motor OOS dilimini hash'liyor' açıklamasının doğrudan kanıtı.* — `n_trades_total` iki kolda da 161 / 161, yani defterler zaten aynıydı.

### 1.1 Ölçüm sırasında depo DEĞİŞTİ (kontrolün neden yeniden kurulduğu)

Ölçüm sürerken (2026-07-31) WP-E ajanı depoda broker.py, guard.py, loop.py ve adapters/alpaca.py dosyalarını DEĞİŞTİRDİ (E1 giriş-icra yasası). Bu yüzden depo motorunu çağıran ref_repo kolu benim motorumla AYNI MOTOR DEĞİLDİR ve pozitif kontrol olarak kullanılamaz. Kontrol, 01:35 anlık görüntüsünün yamasız ikizi (ref_snapshot) ile yapıldı — backtest.py'ye WP-E dokunmadığı hash ile doğrulandı.

| Kol | motor | oos_score | PARA | oos_n | işlem |
|---|---|---|---|---|---|
| ref_repo (depo, WP-E sonrası) | — | 0.0579 | 0.1605 | 130 | 201 |
| ref_repo_noearn (depo, earnings.csv YOK) | — | 0.0579 | 0.1605 | 130 | 202 |
| ref_snapshot (01:35 ikizi, YAMASIZ) | — | 0.0699 | 0.0856 | 88 | 161 |
| *r1_baseline (2026-07-30 14:38, referans)* | — | 0.0749 | 0.1005 | 90 | — |

*r1_baseline.py (2026-07-30 14:38) — o sandbox'ta earnings.csv YOKTU (kazanç karartması NO-OP).*

---

## 2. EDG-2026-005 — SPY 200-SMA YENİ-GİRİŞ KAPISI

### 2.1 Ön bulgu: kapı REPLAY yolunda hiç bağlı değildi

Kart “KOD ZATEN VAR (regime.spy_sma_gate, default-off, guard'a kablolu) — bu kart yalnız ÖLÇÜM” diyor. Ölçüm sırasında çıkan yapısal bulgu şudur:

- `regime.spy_sma_gate` VAR ve doğru çalışıyor (yasa + ısınma koruması yerinde).
- `guard._y3_entry_gates` bu hükmü `regime` sözlüğünün **`entry_gates`** anahtarından okuyor (`guard.py:413`).
- Bu anahtarı üreten TEK yer `api.py:855` — yani **canlı/pano yolu**. `regime.build_regime_json` onu ÜRETMİYOR.
- `backtest.py` replay döngüsü rejim sözlüğünü `build_regime_json`'dan alıyor → **replay yolunda kapı, knob açılsa bile hiç ateşlenmiyor.**

Sonuç: “sandbox'ta knob'u aç” talimatının açacağı bir knob backtest'te YOKTU. Bu ölçüm, kapının **yasasını yeniden yazmadan** (`regime.spy_sma_gate`'in kendisi çağrılarak) replay giriş zincirine taşıyan bir sandbox yamasıyla yapıldı. Yama yalnız sandbox kopyasındadır.

### 2.2 İmza tablosu — ikiz koşum (R1 geometrisi, PARA-v3, aynı barlar/pencere/tohum)

| Metrik | kapı KAPALI | kapı AÇIK | Δ |
|---|---|---|---|
| OOS bileşik skor | 0.0699 | 0.0806 | +0.0107 |
| **PARA-v3 (Search)** | 0.0856 | 0.1254 | +0.0398 |
| OOS işlem sayısı | 88.0000 | 90.0000 | +2.0000 |
| Search işlem sayısı | 71.0000 | 76.0000 | +5.0000 |
| toplam işlem | 161.0000 | 153.0000 | -8.0000 |
| ortalama R | 0.0780 | 0.0990 | +0.0210 |
| kazanma oranı | 0.4090 | 0.4220 | +0.0130 |
| **Sharpe** | 0.2830 | 0.4060 | +0.1230 |
| maxDD (işlem defteri) | 0.0699 | 0.0707 | +0.0008 |
| toplam getiri | 0.0339 | 0.0481 | +0.0142 |
| IS skor | 0.0616 | -0.0349 | -0.0965 |
| holdout skor | — | — | — |

### 2.3 Portföy riski — MTM özkaynak eğrisinden (Search penceresi)

İşlem-defteri maxDD'si ile portföyün gerçek mark-to-market düşüşü AYRI şeylerdir; kart risk aracı iddiasında olduğu için ikincisi belirleyicidir.

| Metrik | kapı KAPALI | kapı AÇIK | Δ |
|---|---|---|---|
| gün sayısı | 400.000000 | 400.000000 | +0.000000 |
| **günlük vol** | 0.004212 | 0.004607 | +0.000395 |
| yıllık vol | 0.066864 | 0.073128 | +0.006264 |
| **MTM maxDD** | 0.068860 | 0.067144 | -0.001716 |
| toplam getiri | 0.060011 | 0.066951 | +0.006940 |
| günlük ort. getiri | 0.000155 | 0.000173 | +0.000018 |

### 2.4 Tarih-kümeli CI — eşleştirilmiş günlük getiri farkı

*açık − kapalı, AYNI günlerde eşleştirilmiş; 21 günlük hareketli blok bootstrap*

- n = **399 gün**
- ortalama fark (açık − kapalı) = **0.181 bps/gün**
- %95 blok-bootstrap aralığı = **[-1.41, +3.47] bps/gün**
- sıfır aralığın İÇİNDE

### 2.5 Volatilite

- günlük vol: kapalı **0.004212** → açık **0.004607** (oran **1.0937**)
- vol farkı %95 blok-bootstrap = [-0.000009, 0.001115]; P(vol düştü) = **0.027**

### 2.5.1 maxDD farkının CI'si

*açık − kapalı MTM maxDD farkı; 21 günlük eşleştirilmiş blok yeniden örnekleme, her tekrarda iki kolun yolu AYNI blok dizisiyle yeniden kurulur. Yolun zamanlaması korunmaz — bkz. kod yorumu.*

- ortalama Δ maxDD (açık − kapalı) = **+0.009406**, %95 aralık = [-0.016224, 0.038665]
- **P(maxDD düştü) = 0.2387**

### 2.6 PARA-v3 farkının olasılığı (kartın başarı ölçütü)

*Defter kaynağı:* `tani_kapali.json / tani_acik.json (pnl_dollars'lı)`

*Determinizm doğrulaması:* kapalı kol search digest eşit = **EVET**, açık kol = **EVET**. Tanı koşumu ilk turun defterini BİT DÜZEYİNDE yeniden üretmediyse ci_para bu defterden okunamaz — bu bayrak False ise sayı GEÇERSİZDİR.

- **P(ΔPARA < 0) = 0.4267** (kart eşiği: < 0.5 yeterli — risk aracı, alfa değil)
- ortalama ΔPARA = +0.0316, %95 aralık = [-0.4797, 0.5679]
- geçerli tekrar 600, ölçülemeyen 0 (min_sample altına düşen yeniden örneklemeler SIFIR sayılmadı)

### 2.7 Kapının davranışı — açık kaldığı gün oranı ve flip sayısı

| Pencere | gün | SPY SMA200 altında | üstünde | **bloke gün oranı** | geçirgen oran | **kapı flip** | flip başına gün |
|---|---|---|---|---|---|---|---|
| Search | 400 | 42 | 358 | 0.1050 | 0.8950 | 4 | 100.0 |
| Tam OOS | 583 | 55 | 528 | 0.0943 | 0.9057 | 6 | 97.2 |

*“Bloke gün oranı” = kapının YENİ GİRİŞİ kapattığı günlerin payı (SPY < SMA200 **ve** knob açık). “Geçirgen oran” = kapının girişe izin verdiği günler.*

### 2.8 Whipsaw maliyeti

*kapalı kolda kapının BLOKE ettiği günlerde silahlanmış planlar = kapının engellediği girişler. Etkileri KAPALI kolun GERÇEKLEŞMİŞ R'siyle ölçülür; yani 'kaçan girişin ne getireceği' varsayılmaz, ikiz koşumda ne getirdiği okunur.*

| | bloke gün | bloke günde silahlanan plan | gerçekleşen işlem | kazanan | kaybeden | **kaçan toplam R** | ort. R | gecikmeli giren |
|---|---|---|---|---|---|---|---|---|
| Search | 42 | 0 | 0 | 0 | 0 | **+0.0000** | — | yok |
| Tam OOS | 55 | 0 | 0 | 0 | 0 | **+0.0000** | — | yok |

*whipsaw maliyeti = flip SAYISI değil, flip'lerin ürettiği kaçan girişlerin gerçekleşmiş R toplamı. Flip sayısı §2.7'de.*

Kaçan girişlerin toplam R'si **pozitifse** kapı masada para bırakmıştır (whipsaw maliyeti); **negatifse** kapı zarar kesmiştir (whipsaw kazancı).

### 2.9 MEKANİZMA TANISI — OOS farkı kapıya AİT Mİ?

**Soru:** OOS defter ayrışması kapının OOS'taki BLOKAJINDAN mı geliyor, yoksa IS penceresinde değişen ve sınırı GEÇEN portföy durumundan mı?

**Yapısal bulgu:** walk_forward IS ve OOS'u ayrı koşmaz — TEK parça replay [is_start, holdout_end] koşar, dilimleme sonradan yapılır.

    meridian/backtest.py:764 `res = replay(params, bars, index_bars, goal, is_start, holdout_end, …)`

overlay IS'te de aktiftir; broker durumu (equity, peak_equity, açık pozisyonlar) IS→OOS sınırını taşır.

#### 2.9.0 H2'nin (knob açıkken yan etki) YAPISAL elenmesi

`wpg.spy_sma_gate=1`in motorda TEK etki yolu vardır: `_ov['block_new_entries']`. Bloke ETMEDİĞİ bir günde yan etki üretmesi YAPISAL OLARAK mümkün değildir.

- backtest.py `wpg_overlay_day`: SMA knob'unun dokunduğu tek alan `block_new_entries = bool(on_sma and g.get('blocks_new_entries'))`; `tilt_uygulandi`/`min_score_delta` ToM knob'una bağlıdır ve bu kolda 0'dır.
- `regime_mod.spy_sma_gate(...)` İKİ kolda da AYNI argümanlarla çağrılır (knob kapalıyken de hüküm kayda geçsin diye) — çağrı sırası/maliyeti fark üretmez.
- `eff_entry = eff` (tilt kapalı) — tarayıcı ve guard iki kolda AYNI eşiği görür.
- Kapının tek tüketicisi tarama koşuludur: `if bar_i >= no_trade_before and rj['exposure_budget_pct'] > 0 and slots > 0 and not _ov['block_new_entries']`.
- `wpg.*` anahtarları strategy/guard tarafından OKUNMAZ; iki kolda anahtar KÜMESİ aynıdır (yalnız değer 0/1 farkı), dolayısıyla `config.resolve_params` çıktısı da aynıdır.

*Pozitif kontrol yamanın KAPALIYKEN no-op olduğunu zaten kanıtlıyor; aşağıdaki `oosonly ≟ kapali` kıyası ise yamanın AÇIKKEN AMA BLOKE ETMEDİĞİ günlerde de no-op olduğunu ölçer.*

#### 2.9.1 Kapının fiilî ısırığı hangi pencerede?

| Pencere | kapının bloke ettiği gün | kapalı kolun bloke günde silahlı planı | açık kolun bloke günde silahlı planı |
|---|---|---|---|
| IS 2022-01→2024-01 | 239 | 8 | 0 |
| OOS 2024-01→2026-04 | 55 | 0 | 0 |

*Kapının bu ölçümdeki TEK fiilî ısırığı IS penceresindedir. OOS'ta bloke ettiği günlerde HİÇBİR kolda silahlı plan yoktur — yani OOS'ta hiçbir girişi engellememiştir.*

IS penceresinde kapının engellediği **8 plan** (kapının bu ölçümdeki TEK fiilî ısırığı):

| tarih | sembol | skor | karar | kurulum |
|---|---|---|---|---|
| 2022-08-17 | TJX | 65 | REVIEW | breakout_vcp |
| 2022-08-18 | ON | 76 | REVIEW | breakout_vcp |
| 2022-08-18 | EL | 61 | REVIEW | breakout_vcp |
| 2022-11-15 | TJX | 76 | REVIEW | breakout_vcp |
| 2022-11-18 | DECK | 84 | REVIEW | breakout_vcp |
| 2022-11-22 | DE | 75 | REVIEW | breakout_vcp |
| 2022-12-08 | ZBH | 64 | REVIEW | breakout_vcp |
| 2022-12-13 | OMC | 79 | REVIEW | breakout_vcp |

#### 2.9.2 Karşı-olgu kolları

- `kapali` — kapı yok
- `acik` — kapı tüm replay
- `oosonly` — kapı yalnız OOS'ta bloke eder (IS yolu = kapali)
- `isonly` — kapı yalnız IS'te bloke eder (OOS'ta bloke etmez)

| Kol | OOS skor | PARA | IS skor | işlem | Search digest |
|---|---|---|---|---|---|
| `kapali` | 0.0699 | 0.0856 | 0.0616 | 161 | `5a826091681e5980…` |
| `acik` | 0.0806 | 0.1254 | -0.0349 | 153 | `ecea745f73f7a1b5…` |
| `oosonly` | 0.0699 | 0.0856 | 0.0616 | 161 | `5a826091681e5980…` |
| `isonly` | 0.0806 | 0.1254 | -0.0349 | 153 | `ecea745f73f7a1b5…` |

| Kıyas | Search digest eşit | Confirm digest eşit | Tüm-defter digest eşit |
|---|---|---|---|
| **oosonly ≟ kapali** | EVET | EVET | EVET |
| **isonly ≟ acik** | EVET | EVET | EVET |
| acik ≟ kapali | HAYIR | HAYIR | HAYIR |

*oosonly≡kapali ⇒ kapının OOS'ta DOĞRUDAN etkisi sıfır. isonly≡acik ⇒ acik-kapali OOS farkının TAMAMI IS-yankısıdır.*

#### 2.9.3 IS whipsaw muhasebesi — engellenen girişlerin GERÇEKLEŞMİŞ sonucu

*Kapının IS'te engellediği planların, KAPALI kolda gerçekleşmiş R'si. Toplam POZİTİFSE kapı masada para bıraktı; NEGATİFSE kapı zarar kesti.*

- engellenen plan: **8**, bunlardan kapalı kolda gerçekleşen işlem: **8** (R ölçülemeyen 0)
- **kaçan toplam R = -0.8730**, ortalama R = -0.1091, kazanan 4 / kaybeden 4
- kaçan işlemlerin net dolar K/Z toplamı = **-444.7$**

| bloke tarih | sembol | giriş | çıkış | R | net $ | çıkış sebebi |
|---|---|---|---|---|---|---|
| 2022-08-17 | TJX | 2022-08-18 | 2022-08-22 | -1.009 | -654.21 | stop |
| 2022-08-18 | ON | 2022-08-19 | 2022-08-23 | -0.510 | -386.52 | regime_flip |
| 2022-08-18 | EL | 2022-08-19 | 2022-08-22 | -0.991 | -602.96 | stop |
| 2022-11-15 | TJX | 2022-11-16 | 2022-12-08 | +1.842 | 1374.06 | time_stop |
| 2022-11-18 | DECK | 2022-11-21 | 2022-12-13 | +0.446 | 370.57 | time_stop |
| 2022-11-22 | DE | 2022-11-23 | 2022-12-15 | +0.179 | 133.57 | time_stop |
| 2022-12-08 | ZBH | 2022-12-09 | 2022-12-16 | +0.144 | 92.16 | regime_flip |
| 2022-12-13 | OMC | 2022-12-14 | 2022-12-16 | -0.974 | -771.37 | regime_flip |

#### 2.9.4 IS penceresi — bu ölçümün TEK nedensel olarak temiz kıyası

İki kol replay'in İLK gününde aynı durumdan başlar (boş portföy, START_EQUITY, peak_equity=START_EQUITY); IS içindeki fark taşınan bir durumdan gelemez, ancak kapının kendi blokajından gelebilir.

| Kol | IS skor | **IS PARA-v3** | IS n | IS toplam getiri | IS maxDD | **IS Sharpe** | IS günlük vol |
|---|---|---|---|---|---|---|---|
| `kapali` | 0.0616 | **-0.0290** | 62 | -0.0163 | 0.0567 | **-0.2540** | 0.003244 |
| `acik` | -0.0349 | **-0.0878** | 53 | -0.0494 | 0.0654 | **-0.8980** | 0.002568 |
| `oosonly` | 0.0616 | **-0.0290** | 62 | -0.0163 | 0.0567 | **-0.2540** | 0.003244 |
| `isonly` | -0.0349 | **-0.0878** | 53 | -0.0494 | 0.0654 | **-0.8980** | 0.002568 |

*span_days=730.0 (IS penceresinin takvim uzunluğu) BEYAN edildi; PARA-v3 pencere uzunluğuna bölündüğü için bu değer OOS PARA'sıyla doğrudan kıyaslanamaz, iki kol arasında kıyaslanır.*

*açık − kapalı, IS penceresinde AYNI günlerde eşleştirilmiş; 21 günlük hareketli blok bootstrap. Bu pencerede iki kol aynı başlangıç durumundan koştuğu için CI kapının NEDENSEL etkisini ölçer.*

- n = **500 gün**; ortalama günlük fark (açık − kapalı) = **-0.829 bps**, %95 CI = [-2.442, 0.932] bps; P(getiri düştü) = **0.7590**
- günlük vol 0.003244 → 0.002568 (oran 0.7918); **P(vol düştü) = 1.0000**
- maxDD farkı ort = -0.001138, %95 CI = [-0.047978, 0.049179]; **P(maxDD düştü) = 0.5447**

*kapali vs acik farkı = kapının IS'teki NEDENSEL etkisi. İşareti hangi yöne bakıyorsa kapının ölçülmüş tek doğrudan etkisi odur.*

#### 2.9.5 Sınırı geçen durum değişkeni

**broker'ın kümülatif portföy durumu — `peak_equity` (tepe-özkaynak) ve ona bağlı `derisk_mult` / `max_positions_at`, artı sınırda AÇIK pozisyon kümesi ve özkaynağın kendisi (backtest.py:271-273)**

`fill_entry(plan, …, eq_now, size_mult=size_mult, …)` pozisyon boyunu eq_now × size_mult'tan hesaplar; `eff_max_open` eşzamanlı slot sayısını kısar. İkisi de YALNIZ (equity, peak_equity) ikilisine bağlıdır ve bu ikili 2022'den itibaren birikir.

| Kol | OOS ilk seans | açılış özkaynağı | `peak_equity` | `size_mult` |
|---|---|---|---|---|
| kapali | 2024-01-02 | 99080.2 | 100731.52 | 1.0 |
| acik | 2024-01-02 | 95527.35 | 100000.0 | 0.7055 |

- OOS'un İLK seansında özkaynak farkı = **-3552.85$**, tepe-özkaynak farkı = **-731.52$** (kapı OOS'ta henüz hiçbir şey yapmadan)
- `size_mult` iki kolda FARKLI olan OOS seansı: **605 / 645**

| Kol | sınırda açık pozisyon | semboller |
|---|---|---|
| `kapali` | 2 | AVGO, LRCX |
| `acik` | 1 | LRCX |
| `oosonly` | 2 | AVGO, LRCX |
| `isonly` | 1 | LRCX |

**TANI: H1 — OOS deltası kapının OOS ETKİSİ DEĞİL, IS-yankısıdır**

EDG-005'in OOS imza farkı kapının OOS'taki davranışına ATFEDİLEMEZ: kapı OOS'ta hiçbir girişi engellemedi ve OOS-only kolu tabanla bit-bit aynı çıktı. Fark, kapının 2022'de (IS) engellediği girişlerin portföy durumunu (özkaynak/tepe-özkaynak/açık pozisyon) değiştirmesi ve bu durumun tek-parça replay'de sınırı geçmesidir.

### 2.10 Kart kriterine göre hüküm

- başarı ölçütü: *maxDD VEYA günlük vol anlamlı düşer VE net PARA DÜŞMEZ (P(ΔS<0) < 0.5 yeter)*
- *'anlamlı düşer' ilk turda ÖLÇÜLMEDEN, yalnız işaretle okunmuştu (maxDD −0,0017 → 'düştü'). Bu tur eşik BEYAN edilir: bir düşüşün anlamlı sayılması için blok-bootstrap altında P(düşüş) ≥ 0,95 olmalıdır.*

#### 2.10.1 ADIM 0 — atıf kapısı

- **İki kolun OOS imza farkı KAPIYA atfedilebilir mi?**
- kapının OOS'taki doğrudan etkisi sıfır mı: **EVET**
- atıf geçerli mi: **HAYIR**
- Kapı OOS'ta hiçbir girişi engellemedi ve kapıyı YALNIZ OOS'ta bloke ettiren karşı-olgu kolu tabanla BİT-BİT aynı defteri üretti. Dolayısıyla ölçülen OOS farkı kapının OOS davranışının değil, IS penceresinde değişip sınırı geçen portföy durumunun ürünüdür; kart ölçütü bu fark üzerinden UYGULANAMAZ.

#### 2.10.2 ADIM 1-2 — kart koşulları (atıf geçerliymiş gibi okunursa)

| Koşul | Ölçüm | Sağlandı? |
|---|---|---|
| net PARA düşmüyor (P(ΔS<0)<0.5) | ΔPARA=+0.0398, P=0.4267 | EVET |
| günlük vol **anlamlı** düştü (P≥0.95) | oran=1.0937, P(düştü)=0.0272 | HAYIR |
| maxDD **anlamlı** düştü (P≥0.95) | 0.068860 → 0.067144 (Δ=-0.001716), P(düştü)=0.2387 | HAYIR |
| **risk koşulu** (vol VEYA maxDD) | — | HAYIR |
| *kill:* net Sharpe düştü mü | 0.2830 → 0.4060 | HAYIR |

KILL (OOS, atıfsız): **HAYIR** · atıf varsayılsaydı karar: `KAPI_ACILMAZ_OLCUT_SAGLANMADI`

#### 2.10.2b ADIM 1b — kill#1'in ATFEDİLEBİLİR pencerede okunuşu

OOS kill'i atıfsızdır (yukarıda). Kartın kill#1'i (*net Sharpe/PARA düşüyorsa kapı açılmaz*) ancak nedensel-temiz pencerede okunabilir: **IS 2022-01-01 → 2024-01-01 (tek nedensel-temiz pencere)**.

| Metrik | kapı KAPALI | kapı AÇIK | düştü mü? |
|---|---|---|---|
| **Sharpe** | -0.2540 | -0.8980 | EVET |
| **PARA-v3** | -0.0290 | -0.0878 | EVET |
| toplam getiri | -0.0163 | -0.0494 | — |
| maxDD | 0.0567 | 0.0654 | P(düştü)=0.5447 |
| günlük vol oranı | — | 0.7918 | P(düştü)=1.0000 |

**kill#1 tetiklendi: EVET**

Okumanın sınırları (kendi aleyhine):

- Kart kill#1'i 'net Sharpe/PARA DÜŞÜYORSA' diye yazılmıştır — nokta kıyası, CI şartı YOK. Tetikleme bu metne göre okundu.
- Günlük getiri farkının %95 aralığı sıfırı içeriyorsa, kapının getiriyi düşürdüğü NOKTA tahmini vardır ama gürültüden ayrılmış DEĞİLDİR. Kill'i tetikleyen şey işaret; kanıtın gücü bu satırda.
- Kapının IS'te fiilen engellediği giriş sayısı: 8. Hüküm bu kadar küçük bir doğrudan ısırığın portföy yolunda ürettiği kelebek etkisine dayanıyor.
- Kartın TEZİ bu pencerede DOĞRULANDI: vol anlamlı düştü (oran 0.791754, P(vol düştü)=1.0). Kapı vol'ü düşürüyor — ama maxDD'yi düşürmüyor ve bedeli Sharpe/PARA.
- günlük getiri farkının %95 aralığı sıfırı içeriyor mu: **EVET**

#### 2.10.3 NİHAİ KARAR

- **ölçüm hükmü:** `HUKUMSUZ_OLCUM_TASARIMI`
- **operasyonel sonuç (knob):** `KAPI_ACILMAZ`

Ölçüm tasarımı IS-taşımasını AYRIŞTIRAMIYOR: walk_forward tek parça replay koştuğu için overlay IS'te de aktif ve broker durumu sınırı geçiyor. Kapının OOS'taki DOĞRUDAN etkisi ölçüldü ve SIFIR çıktı. Ölçülen fark kapı değil, 2022'de değişen portföy yolunun 2024-2026'ya taşınan yankısıdır. Atıf geçerli SAYILSAYDI kart ölçütünün okunuşu: vol anlamlı düştü = False (P(vol düştü)=0.0272); maxDD anlamlı düştü = False (P(maxDD düştü)=0.2387); PARA koşulu = True (P(ΔPARA<0)=0.4267); kill = False → KAPI_ACILMAZ_OLCUT_SAGLANMADI. Ayrıca vol DÜŞMEDİ, anlamlı biçimde ARTTI — kartın risk-aracı gerekçesinin ölçülen yönü TERSTİR.

Knob KAPALI kalır. Birbirinden bağımsız yollar: (a) kapının OOS'taki doğrudan etkisi ölçüldü ve SIFIR — R1 OOS penceresinde knob'u açmanın defterde HİÇBİR karşılığı yok; (b) tek nedensel-temiz pencerede (IS 2022-2024) kartın kill#1'i TETİKLENDİ: Sharpe -0.254 → -0.898, PARA-v3 -0.029 → -0.0878; (c) atıf geçerli sayılsaydı bile OOS'ta kart ölçütünün risk koşulu sağlanmıyor.

---

## 3. EDG-2026-006 — TURN-OF-MONTH TILT

**Eşik şiddeti beyanı (grid YOK):** `entry.min_score` 60 → **65** (Δ=5.0) ToM penceresi DIŞINDA. TEK değer, BEYAN edildi — grid YOK (kart: 'eşik şiddetini TEK değer seç ve beyan et'). ToM üyeliği DOLUM gününde (D+1, XNYS) değerlendirilir.

### 3.1 Ön adım — ToM içi/dışı günlük getiri farkı (bizim evren, bizim dönem)

Kart bu adımı doğrudan bir kill kapısı yapıyor: *“ToM-içi/dışı getiri farkı bizim evren/dönemde işaretsizse kill#2 doğrudan.”* Referans: McConnell-Xu 2008 FAJ, VW **+%0,14/gün** ToM vs **−%0,01** diğer günler.

| Dilim | Seri | ToM günü | diğer gün | ToM ort. | diğer ort. | **fark** | %95 CI | işaret + mi? |
|---|---|---|---|---|---|---|---|---|
| tam_ornek | evren_ew | 266 | 1131 | +3.50 bps | +6.02 bps | **-2.52 bps** | [-16.4, +10.6] | HAYIR |
| tam_ornek | spy | 266 | 1131 | +4.56 bps | +5.68 bps | **-1.12 bps** | [-14.7, +13.0] | HAYIR |
| R1_OOS | evren_ew | 111 | 472 | -3.82 bps | +7.97 bps | **-11.79 bps** | [-31.6, +6.4] | HAYIR |
| R1_OOS | spy | 111 | 472 | +0.86 bps | +8.98 bps | **-8.12 bps** | [-28.3, +12.7] | HAYIR |
| R1_IS | evren_ew | 96 | 405 | +6.84 bps | +0.98 bps | **+5.86 bps** | [-20.6, +31.9] | EVET |
| R1_IS | spy | 96 | 405 | +4.88 bps | -0.20 bps | **+5.08 bps** | [-21.5, +31.8] | EVET |
| R1_holdout | evren_ew | 12 | 50 | +9.33 bps | +9.91 bps | **-0.58 bps** | — | HAYIR |
| R1_holdout | spy | 12 | 50 | +25.40 bps | -0.08 bps | **+25.48 bps** | — | EVET |

*`evren_ew` = 250 sembollük evrenin EŞİT AĞIRLIKLI günlük getirisi (bizim evrenimiz). `spy` = endeks getirisi; McConnell-Xu'nun VW'sinin KABA vekilidir, aynı şey değildir ve adıyla anılır.*

### 3.2 Hüküm

**KARAR: `ARSIV_KILL2`**

Kart kill#2: 'ToM-içi/dışı getiri farkı bizim evren/dönemde İŞARETSİZSE arşiv.' Ön adım BİRİNCİL dilimde (R1 OOS, eşit ağırlıklı 250-sembol evreni) farkı TERS işaretli ölçtü: ToM günleri −3,82 bps/gün, ToM-dışı +7,97 bps/gün, fark −11,79 bps/gün. Literatürün beklentisi (+%0,14/gün) DEĞİL, tersi. Tilt'in varsayımı bizim dönemimizde YOKTUR; ikiz koşum KOŞULMADI çünkü kart bu adımı doğrudan kill kapısı olarak tanımlıyor.

> İkiz koşum bilinçli olarak KOŞULMADI. Sebep bütçe değil YÖNTEMDİR: tilt'in tüm dayanağı “ToM günleri daha iyidir” önermesidir ve bu önerme birincil dilimde TERS işaretle ölçülmüştür. Ters işaretli bir zeminde “ToM dışında eşiği yükselt” kuralı, ölçülmüş olarak **daha iyi** günlerde iştahı kısmak anlamına gelir; koşumun yönü ön adımdan zaten bellidir.

---

## 4. Survivorship notu

- **Evren:** data.REPLAY_UNIVERSE (250 sembol yüklendi; kod 251 sembol tanımlıyor)
- **Durum:** Evren BUGÜNÜN listesidir ve tarihsel üyelik yeniden kurulmaz — as-of endeks üyeliği bu depoda YOK. Kısmî azaltım: listeye bilinçli olarak GERİ KALANLAR (INTC, PYPL, DIS, T, EA, PFE, ENPH, MRNA, MMM, HRL, VFC, F) eklenmiş, yani kapı yalnız bugünün kazananlarına ayarlanmıyor. Ayrıca verisi biten sembol 'delisted_markout' ile SON barında kapatılır (denetim #7/#46) — pozisyon sessizce buharlaşmaz.
- **Bu ölçüme etkisi:** SMA kapısı ENDEKS seviyesindedir; hangi hisselerin evrende olduğuna değil SPY'ın kendi serisine bakar. Dolayısıyla kapının HÜKMÜ survivorship'ten etkilenmez; etkilenen şey kapının ENGELLEDİĞİ işlemlerin getirisidir (evren yukarı yanlıysa kaçan girişlerin getirisi de yukarı yanlıdır → kapının maliyeti OLDUĞUNDAN BÜYÜK görünür, yani bulgu kapı LEHİNE değil ALEYHİNE muhafazakârdır).

## 4.1 Ölçümün sınırları (kendi aleyhine kayıt)

### `bars_integrity_defteri_sandbox_state_dizinlerinde_YOK`

- **bulgu:** Kolların state dizinlerinde `bars_integrity.json` YOKTUR (bulunan: hiçbiri). `adapters.data.bars_integrity` defteri `store` üzerinden, yani `config.STATE`e göre okur; sandbox state'inde defter olmadığı için FAIL-OPEN dalı işler ve 'ölçüm için güvensiz dönem' DIŞLAMASI hiçbir kolda uygulanmamıştır.
- **etkisi:** A/B kıyasına etkisi YOK — dışlama TÜM kollarda aynı biçimde (hiç) uygulanmadı, kollar arası fark bu kanaldan gelemez. Etkilenen şey MUTLAK seviyedir: depo state'iyle koşulan bir ölçümün sayıları bu kolların sayılarıyla birebir kıyaslanamaz.
- **ne_yapilmadi:** Defter sandbox'a KOPYALANMADI; kopyalamak koşumları yeniden koşmayı gerektirirdi ve bulgu A/B'yi değiştirmiyor.

### `depo_state_dosyasi_degisti`

- **gozlem:** Ölçüm sürerken depoda `state/bars_integrity.json` dosyasının mtime'ı 2026-07-31 10:19'a güncellendi.
- **benim_kollarim_mi:** HAYIR — kanıt: (1) kollar `config.STATE`i sandbox'a çevirir, `store` yalnız oradan yazar; (2) depo `state/events.jsonl`in son satırı 2026-07-30T23:59, yani kollarım depo defterine HİÇ yazmadı; (3) bu dosyayı yazan tek yol `barrepair.yaz_envanter` ve `bars_integrity_written` olayı depo defterinde YOK; (4) `adapters.data` bu dosyayı yalnız OKUR.
- **destekleyen_gozlem:** Aynı pencerede depoda `CLAUDE.md`, `ROADMAP.md`, `meridian/store.py`, `loop.py`, `analytics.py`, `run.py`, `watchdog.py`, `shadow_model.py`, `intraday_cycle.py`, `ledgerstamp.py`, `shadow_lifecycle.py`, `versioning.py`, `storage.py` dosyaları da değişti — depoda eşzamanlı BAŞKA ajan(lar) çalışıyor.
- **hüküm:** Eşzamanlı başka bir ajan. Sessizce yutulmadı, kayda geçti.

## 5. Maliyet modeli

- 10 bps gidiş-dönüş — goal.yaml slippage_bps=5 × iki bacak, MOTORUN İÇİNDE uygulanır (broker.PaperBroker), rapor sonrası eklenen bir düzeltme DEĞİLDİR.
- commission_per_share goal.yaml'dan; ADV tabanlı likidite tavanı ve fiyat etkisi de motorda etkin (Hard Rule 7).

## 6. Kod-sürümü damgası

Sandbox motoru, deponun `meridian/` ağacının **87 .py dosyalık** kopyasıdır (2026-07-31 01:35 anlık görüntüsü).

Ölçüm bitiminde depoyla FARKLI olan dosyalar: `adapters/alpaca.py`, `backtest.py`, `broker.py`, `guard.py`, `loop.py`

Bunlardan `backtest.py` **benim ölçüm yamamdır**; diğerleri ölçüm sürerken **WP-E ajanının depoda yaptığı değişikliklerdir** (bkz. §1.1). Tam SHA-256 listesi: `kod_damgasi.json`.

### Ölçüm dosyaları

| Dosya | Rol |
|---|---|
| `on_adim_tom.py` / `on_adim_tom.json` | EDG-006 ön adımı (kill#2 kapısı) |
| `kosum.py` / `kol_*.json` | tek-kol ikiz koşum sürücüsü + ham sonuçlar |
| `tani_kosum.py` / `tani_*.json` | tanı turu: `pnl_dollars`'lı defter + karşı-olgu kolları (`oosonly`, `isonly`) + durum defteri |
| `analiz.py` / `sonuc.json` | birleştirme, CI'lar, whipsaw, mekanizma tanısı, hükümler |
| `rapor.py` / `RAPOR.md` | bu rapor (her sayı `sonuc.json`'dan okunur) |
| `kod_damgasi.json` | dosya hash listesi |
| `meridian/` | yamalı sandbox motoru |
| `ref_snapshot/meridian/` | YAMASIZ ikiz (pozitif kontrol motoru) |
