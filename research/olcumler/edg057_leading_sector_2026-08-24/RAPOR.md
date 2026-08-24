# EDG-2026-057 — `leading_sector` kapısı · ÖLÇÜM RAPORU

**Kart:** `research/cards/EDG-2026-057-leading-sector-kapisi.yaml` (SALT OKUNDU, değiştirilmedi)
**Ölçüm dizini:** `research/olcumler/edg057_leading_sector_2026-08-24/`
**Betik:** `olc.py` — iki TAM koşumda `sonuc.json` bayt-özdeş (`fb42018c2fd8053c…`)
**Kasa:** edg032c donmuş taban · şasi `edg032b/olcum.py` (`75cef79215a7404f…`) · EDG-022 donmuş config'ler
**Koşum:** `.venv/bin/python`, yerel; canlı okunmadı, `state/` altına YAZILMADI, git koşulmadı.

> **BU RAPOR HÜKÜM İÇERMEZ.** Ölçüm ajanı sayı üretir; hükmü Rol-1 işler. Aşağıda "kapı haklı",
> "kapı gerekçesiz" ya da eşdeğeri hiçbir çıkarım YOKTUR.

---

## 1 · KÜNYE DOĞRULAMASI — koşum ÖNCESİ ve SONRASI, ikisi de **GEÇTİ**

| dosya | edg032c taban | ölçüm anı | eşit |
|---|---|---|---|
| `meridian/backtest.py` | `b59c059f43d4e410…` | `b59c059f43d4e410…` | EVET |
| `meridian/broker.py` | `e4c5c91515d8ec35…` | `e4c5c91515d8ec35…` | EVET |
| `meridian/guard.py` | `475e19e7b38f0650…` | `475e19e7b38f0650…` | EVET |
| `meridian/strategy.py` | `d6ae533c8a578f74…` | `d6ae533c8a578f74…` | EVET |

Künye iç tutarlılığı (`kosum1_once` ≡ `kosum2_sonra`) sağlam. Künye `2026-08-24T01:20:15Z`'de
tazelendi (3 girdi; kanıt `edg032c_kunye_tazeleme_2026-08-24/bayt_ozdeslik.json`). Sha koşum
BAŞINDA ve SONUNDA alındı, ikisi de tabanla eşit — koşum içinde motor değişmedi.

**Şasi kimlik çivileri** (şasinin kendi assert'leri AYNEN koşuldu):
`goal.yaml 099590dedee1ccf2` · `strategy.yaml 9f3e4732315abe52` · `bounds.yaml 3e810b547ca95f9a`
(032-cmb kaydıyla bayt-aynı) · `ARMED_SETUPS = (breakout_vcp, exhaustion_hammer, momentum_burst)`
(B1) · motor yamasız · yasaklı modül ithal edilmedi · `DINLENEN_LIMIT = False`.

**Maliyet modeli tabanla AYNI:** `slippage_bps = 5.0`, `commission_per_share = 0.0` — koşum
başında assert'lendi. **Friksiyon/slipaj/komisyon indirimi YOK.**
Hücre: edg032c künyesindeki MERKEZ (`slot 20` · `position_size_r 0.5` · `heat_hard_r 5.0`,
zarf enjeksiyonu yok). Evren 251 sembol, endeks 1408 satır.

---

## 2 · TEST KÜMESİ VE DIŞLAMA KANITI

Eşleştirme yolu `meridian/topviews.py::topviews` içindeki `islem_by_plan` kurgusunun aynısı
(`str(trade.plan_id)` → `str(plan.id)`); ölçüt tespiti `topviews.py::_reddi_et` ile aynı.
**İkinci bir eşleştirme mantığı icat edilmedi.** Defterler yerel: 390 plan / 95 işlem.

| adım | sayı |
|---|---|
| `leading_sector` ölçütünde takılan plan | **217** |
| bunlardan işleme dönmüş plan (ÇIKARILDI) | **52** (→ 52 kapanmış işlem) |
| **TEST KÜMESİ** | **165** |

217 − 52 = 165 (aritmetik doğrulandı). **Sızıntı kontrolü iki yönlü TEMİZ:** 165'in hiçbiri
`islem_by_plan`'da yok; 95 işlemin hiçbirinin `plan_id`'si 165'lik kümede yok.

**Çakışma (kart `beyanli_sinirlar` (3)):** **87** plan yalnızca `leading_sector`da takıldı,
**78** plan başka ölçüt(ler)de de takıldı. Takılan ölçüt sayısı: `1→87, 2→45, 3→18, 4→10, 5→1, 6→4`.

---

## 3 · KARŞI-OLGUSAL KOŞUM — nasıl koşuldu

Faz sırası `backtest.replay` ile **birebir**: OPEN(D) bekleyen çıkış → OPEN(D+1) dolum →
INTRADAY(D) dokunma çıkışı (`broker._touch_exit`) → CLOSE(D) trail/rejim/zaman
(`strategy.manage_position`) → kasa sınırında `eod_markout`/`delisted_markout`.
**İkinci bir çıkış yasası yazılmadı; motorun kendi fonksiyonları çağrıldı.**
Dolum günü = plan gününden sonraki İLK seans (52 gerçek dolumla doğrulandı: gün farkı 1/3/4,
hepsi bir sonraki seans). O seansta bar yoksa plan düşer (replay `armed`ı her gün sıfırlar).

### Beyanlı izolasyon ve yeniden-ölçüm kararları
| karar | gerekçe / kanıt |
|---|---|
| Portföy bağlamı UYGULANMADI (slot/ısı/sektör tavanı, devre kesici, `size_mult=1.0`) | kart tam da bu bağlamı kaldırıp planın kendi beklentisini soruyor |
| `equity` sabit 100.000 (`score.START_EQUITY`) | R ölçek-değişmez; yalnız qty yuvarlaması / ADV / notional tavanı ikinci derece etki bırakır |
| `pivot = 0.0` | plan defteri pivot taşımaz. Donmuş params'ta `exit.early_kill_pivot = 0` olduğu **assert'lendi** → erken itlaf zaten atıl, davranış **birebir** |
| ATR sinyal barında yeniden ölçüldü | kayıtta yok; motorun kendi `indicators.atr`ı, yalnız t'ye dek barlarla. Ölçülemezse `None` (uydurma ATR yok) |
| `bar_low = None` | `DINLENEN_LIMIT = False` — taban dolum kuralı aynen |
| `adv` | motorun kendi `backtest._adv` nedensel fonksiyonu |
| Kasa sağ sınırı `2026-07-30` | edg032c `pencere.end`; orada açık kalan pozisyon tabanın markout kuralıyla kapatıldı |
| Donmuş params'ta atıl olan yollar | `chandelier_lookback=0`, `scale_out_frac=0.0`, `giveback_pct=0.0`, `params_by_regime` dört rejimde de BOŞ (→ `eff ≡ params`) |

### Dolum sonucu
156 plan doldu, **9 dolmadı**: `dolum seansında bar yok` 7 · `max_chase` 1 · `open_below_stop` 1.
(Bunlar motorun kendi ret nedenleri; yutulmadı, sayıldı.)

---

## 4 · SONUÇ — kartın istediği beş büyüklük + CI

### ANA ÖLÇÜM (kohort `leading_sector_ret_islemsiz`, 165 plan → 156 karşı-olgusal işlem)

| büyüklük | değer |
|---|---|
| kohort `n` (karşı-olgusal işlem) | **156** |
| toplam R | **−22.79** |
| **ortalama R** | **−0.14609** |
| stop payı | **0.359** |
| kazanma | **0.4038** |
| **%95 CI (ay-kümeli bootstrap)** | **[−0.26612, −0.02581]** |
| ay kümesi sayısı | 18 |
| eşik (ön-kayıtlı, donmuş) | **0.0** |
| CI ↔ eşik | **CI-ÜST < eşik** |

Bootstrap kurulumu ön-kayıtlı ve uygulandı: **B=5000, seed=20260812, birim=AY**; ay adları
yerine-koymalı çekilir, seçilen ayların tüm gözlemleri havuzlanır (EDG-022/EDG-023 fonksiyonunun
aynısı). **İşlem-düzeyi bootstrap kullanılmadı.** Kümeleme birimi işlemin giriş ayı (`ts_open[:7]`).
Kartın "eşlenik" ibaresi bu deponun standart kurulumunun adıdır; TEK kohortta eşlenecek ikinci kol
yoktur, ölçü ay-kümeli CI'ya indirgenir.

Bootstrap ucu ayrıca sentetik veriyle üç çivide öz-sınandı (determinizm / sıfır-merkezlide CI
sıfırı içeriyor / ay-kümeli CI iid'den geniş) — üçü de geçti.

Çıkış nedeni dağılımı (156): `regime_flip 75` · `stop 48` · `time_stop 17` · `stop_gap 8` ·
`delisted_markout 4` · `target 2` · `target_gap 2`.

### DUYARLILIK (Rol-1 talebi) — 3 `failed_broker_rejection` planı HARİÇ

| | n | ortalama R | %95 CI | stop payı | kazanma |
|---|---|---|---|---|---|
| **ANA (3 dâhil)** | 156 | −0.14609 | [−0.26612, −0.02581] | 0.359 | 0.4038 |
| **duyarlılık (3 hariç)** | 153 | −0.14891 | [−0.26740, −0.02671] | 0.366 | 0.3987 |

İki sayı yan yana; hangisinin "gerçek" olduğu Rol-1'in kararı. K muhasebesi de Rol-1'e aittir —
ölçüm ajanı duyarlılık koşusunun K'ya sayılıp sayılmayacağına karar vermez.

### PLAN-DÜZEYİ PAYDA (betimleyici, **CI ÜRETİLMEDİ**)
165 planın 9'u dolmadı. Dolmayanlar 0R sayılırsa plan-düzeyi ortalama **−0.13812**.
CI bilerek üretilmedi: aynı hipotez için ikinci bir çıkarımsal deneme K'yı gizlice büyütürdü
(kart kill#6). Kart `peek_beyani`'nın (c) maddesi tam da bu payda karışmasını uyarıyor —
**yukarıdaki CI 156 İŞLEMİNDİR, 165 PLANIN değil.**

---

## 5 · PIT ÖZ-SINAMALARI — **3/3 GEÇTİ** (`pit_sinama.json`)

| # | sınama | ne yapar | sonuç |
|---|---|---|---|
| **S1** | tarih kaydırma | her plan +5 iş günü kaydırılmış girişle yeniden koşuldu; koşum giriş tarihini gerçekten okuyorsa sonuç DEĞİŞMELİ | **geçti** — ortak 97 işlemin **92'si (%94,85)** değişti; kaydırılmış ortalama R = −0.22798 |
| **S2** | gelecek-bar erişim assert'i | her karar çağrısına verilen çerçevenin son barı ≤ karar günü; `PITBekcisi` her çağrıda sayarak doğrular, tek ihlalde `PITIhlali` yükseltip koşumu durdurur. Yapısal koruma da var: her çağrıya `.loc[:d]` dilimi verilir, tam çerçeve HİÇ geçilmez | **geçti** — **1504 çerçeve kontrolü, 0 ihlal** |
| **S3** | iki `as_of` özdeşliği | aynı kohort `as_of=2026-07-30` (kasa sınırı) ve `as_of=2026-08-12` (önbellekteki son bar) ile koşuldu | **geçti** — kıyaslanan **152/152 BİREBİR AYNI**, 0 fark (dar pencerede markout'a kesilen 4 plan kıyas dışı) |

---

## 6 · KILL LİSTESİ — altı madde, AYRI AYRI

| # | kural | sonuç | dayanak |
|---|---|---|---|
| 1 | `n < 30` → hüküm YOK | **temiz** | n(işlem) = 156, n(plan) = 165 |
| 2 | edg032c künyesi eşleşmezse geçersiz | **temiz** | 4/4 dosya, koşum ÖNCESİ **ve** SONRASI (§1) |
| 3 | işleme dönmüş plan sızarsa geçersiz | **temiz** | iki yönlü kontrol, 0 sızıntı (§2) |
| 4 | karşı-olgusal koşum gelecek bar okursa geçersiz | **temiz** | S1/S2/S3 üçü de geçti; 1504 çerçeve kontrolü 0 ihlal (§5) |
| 5 | eşik (sıfır) oynatılırsa geçersiz | **temiz** | `ESIK = 0.0` betikte sabit; kart salt okundu |
| 6 | alt-dilim/ikinci eksen eklenirse geçersiz | **temiz** | ANA ölçüm TEK: tek kohort, tek eksen, **tek CI**. Sektör/rejim/yıl alt-kırılımı ARANMADI. Duyarlılık koşusu ve plan-düzeyi payda AYRI etiketli; K muhasebesi Rol-1'de |

---

## 7 · BEYANLI SINIRLAR — Rol-1'in hükmü bunlarsız okunamaz

### (a) Test kümesi fiilen **2025-02-20 → 2026-07-28** dilimidir
| yıl | takılan | işleme dönen | test kümesinde |
|---|---|---|---|
| 2023 | 20 | **20 (%100)** | 0 |
| 2024 | 15 | **15 (%100)** | 0 |
| 2025 | 105 | 11 | 94 |
| 2026 | 77 | 6 | 71 |

Plan defterinin tamamında da 2023 (35/35) ve 2024 (26/26) planlarının hepsi bir işleme bağlı —
o iki yılın plan satırlarının işlem defterinden geriye türetilmiş olabileceğini düşündürür
(ölçülmedi, sayı olarak bildiriliyor). "Dokunulmamış dilim" 2023-2024 rejimini temsil etmez.

### (b) 165'in 3'ü tam anlamıyla dokunulmamış değil
`broker_status`: `None` 162, `failed_broker_rejection` **3**. İşleme dönmediler (kart kuralı
işlem-tabanlı → kümedeler), ama bir mekanizma onları göndermeyi **seçmiştir**. §4'te üçü dâhil
ve hariç iki sayı yan yana verildi; iki CI de aynı tarafta.

### (c) **REJİM BÜTÇESİ AYRIŞMASI — bu turun en ağır sınırı**
Donmuş kasanın rejim hesabı, planların kendi kaydıyla karşılaştırıldı:

| | sonuç |
|---|---|
| rejim ETİKETİ (trend_up/chop) uyuşması | **165/165 AYNI** |
| `exposure_budget_pct` uyuşması | **121/165 aynı, 44 FARKLI** |
| donmuş kasada bütçesi **0** olan plan günü | **52** |

Örnek: `P-2025-02-24-PGR` — canlı kayıtta bütçe 25, donmuş kasada 0. (`build_regime_json`:
`budget = score if score >= 40 else 0`; `regime.min_exposure_score` her iki config'de de 40, yani
fark eşikten değil skor girdisinden geliyor. Canlı strategy.yaml v5, donmuş EDG-022 kopyası v3.)

**Sonucu:** donmuş motorda `regime_ok = regime ∈ (trend_up, chop) VE exposure_budget_pct > 0`.
Bütçe 0 olan günlerde `manage_position` ilk CLOSE'da `regime_flip` döndürür. Ölçülen dağılımda
**75 çıkışın 49'u ilk barda `regime_flip`**. Ayrıca donmuş kasanın kendi replay'i bu planları
**hiç silahlandırmazdı** (`replay` tarama koşulu `rj["exposure_budget_pct"] > 0`) — yani kohortun
bu dilimi, tabanın kendi başına üretmeyeceği bir durumda koşuldu.

**Bu ayrışma için VARYANT HESAPLANMADI** (kill#6: alt-dilim/ikinci eksen). Rol-1 isterse ayrı
kartla ölçülür. Sayı ve mekanizma burada; karar Rol-1'in.

### (d) Karşı-olgusal ≠ gerçek (kartın kendi (2) şerhi) + deponun kendi yasası
Hiç gönderilmemiş planın simüle dolumu gerçek likidite/slipajı görmez. Buna ek olarak
`meridian/counterfactual.py` modül başlığı bu SINIFA depo yasası koyuyor: karşı-olgusal defter
"hiçbir kapı kararına kanıt olamaz" (gerekçe: seçilim yanlılığı + doldurma gerçekçiliği eksikliği),
ve edg032b şasisinin `YASAK` listesi `meridian.counterfactual`ı ithal etmeyi engelliyor.
**Bu ölçüm o modülü KULLANMADI** (yasak koşum başında assert'lendi); motorun kendi replay
ilkelleriyle koşuldu. Yine de o yasanın gerekçesi bu ölçümün sınıfına da uyar — Rol-1'in
tartması gereken bir kalemdir, ölçüm ajanı hüküm vermez.

### (e) Gözetlenmiş hipotez (kartın (1) şerhi)
Kart bir gözlemden doğdu ve bunu `peek_beyani`'nda taşır; bağımsız bir dönemde yeniden
üretilmeden canlıya dokunamaz.

---

## 8 · ÜRETİLEN DOSYALAR

| dosya | içerik |
|---|---|
| `olc.py` | ölçüm betiği; deterministik (iki tam koşumda `sonuc.json` bayt-özdeş) |
| `sonuc.json` | ham sayılar · künye (önce/sonra) · 156 işlem satırı · rejim mutabakatı · kill tablosu |
| `pit_sinama.json` | üç PIT öz-sınamasının tasarımı ve sonucu |
| `kosum.log` | tam koşum çıktısı |
| `state_edg057/` | donmuş kasa sandbox'ı (EDG-022 config kopyaları + `state/bars` sembolik bağı) |
| `RAPOR.md` | bu dosya |

Karta **dokunulmadı** (`status` dahil); `state/` altına **yazılmadı**; git **koşulmadı**;
motor dosyası **değiştirilmedi**; tam suite **koşulmadı**; `-q` **eklenmedi**.
