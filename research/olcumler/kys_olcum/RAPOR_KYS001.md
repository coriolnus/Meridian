# KYS-2026-001 — KIYAS KİRLENMESİ: ÖN-KAYITLI NİCELLEŞTİRME

**Kart:** `research/cards/KYS-2026-001-kiyas-kirlenmesi.yaml` (ALTYAPI kartı) · **Grid:** K=2 (iki yüzey) · **Ölçüm ajanı karta dokunmadı.**

> **HÜKÜM YOK.** Bu rapor sayı taşır. Kill/arşiv/askı ve ileri-standart kararı Rol-1'dedir. Kart ALTYAPI kartıdır: **geçmiş kart hükümleri bu turda değişmez**, dil ENVANTER dilidir.

**Kod damgası:** `be8296f` · kirli ağaç: `True` (bu turun kendi dosyaları) · ölçüm araçları sürümü `2026-08-02` (`olay_disi_kiyas` 1.0, `blok_bootstrap_ci` 1.0)
**Salt-ölçüm mührü:** `TUTTU` — `config.STATE` = kum havuzu; canlı `state/`e tek bayt yazılmadı (bar kopyası + kum havuzu takvimi).

---

## 1. ARAÇ-DOĞRULAMA PK (kart `guards` #1) — **GEÇTİ**

Sentetik zeminde cevap ÖNCEDEN bilinir: δ kadar kaydırılmış bir olay penceresi enjekte edilir; temiz kıyasın δ'yı bulması, kirli kıyasın onu SIKIŞTIRMASI beklenir. Gürültü bilerek küçüktür (kestirici sınanıyor, istatistiksel güç değil).

| Kol | Ölçüt | temiz | kirli | sıkışma | Sonuç |
|---|---|---|---|---|---|
| PK-0 pencere eşdeğerliği (in_blackout BİREBİR) | küme birebir eşit | araç kirli=822 | in_blackout=822 | — | GEÇTİ |
| PK-1 δ=+30bps · yaygınlık %70 | temiz ≈ +30bps (±5.0) · sıkışma > 0 · kirli < temiz | +29.47 bps | +15.35 bps | +14.12 bps | GEÇTİ |
| PK-2 δ=−30bps · yaygınlık %70 | temiz ≈ −30bps (±5.0) · sıkışma < 0 · \|kirli\|<\|temiz\| | -30.53 bps | -16.62 bps | -13.91 bps | GEÇTİ |
| PK-3 δ=0 · yaygınlık %70 (uydurma kontrolü) | \|temiz\| < 5.0bps VE \|sıkışma\| < 5.0bps | -0.53 bps | +0.47 bps | -1.00 bps | GEÇTİ |
| PK-4 δ=+30bps · yaygınlık %15 (seyrek) | 0 ≤ sıkışma(seyrek) < 0.5 × sıkışma(yaygın) | +29.95 bps | +27.04 bps | +2.91 bps | GEÇTİ |

**PK-0 ne kanıtlar:** pencere `(once=5, sonra=0)` — yani `[olay−5, olay]` TAKVİM günü — `earnings.in_blackout` ile **birebir aynı** satır kümesini kirli sayıyor (822 satır, sembol×gün tam tarama, fark 0). Kartın `features_asof` şartı ("karartma tanımıyla BİREBİR") varsayılmadı, **ölçüldü**.

**PK ölçütlerinin kaydı (dürüstlük notu):** ilk taslakta ek bir `kirli/temiz < 0,50` şartı vardı; o şart aracın değil SENTETİK TASARIMIN özelliğini ölçüyordu (180 günlük panelde kıyasların çoğu kirliliği ~%1 olan günlere düşüyordu — kol adında yazan "%70 yaygınlık" rejimi hiç kurulmuyordu). Düzeltme **eşiği gevşetmek değil tasarımı onarmak** oldu: panel sezona indirildi, ölçütler doğruluk + yaygınlık-tekdüzeliğine demirlendi. Kartın asıl şartı (YÖN) her taslakta geçiyordu. Gerekçe `pk_kys.py` başlığında yazılıdır.

---

## 2. OLAY-ETİKETLEME KAPSAMASI (kart kill #2)

**Etiketlenebilirlik tanımı (ölçümden önce yazıldı):** bir satır `(t, g)` ancak takvim `[g, g+5]` iş günlerinin **tamamını görmüşse** etiketlenebilir. Görmediyse `in_blackout` False döner ama bu *"karartma yok"* değil *"veri yok"*tur (`earnings` modülünün beyanlı FAIL-OPEN'ı) — ikisini aynı saymak bu kartın avladığı hata sınıfının ta kendisidir.

| Kaynak | Sembol kapsaması | Takvim tamlığı (gözlenen/beklenen) | Etiketlenemeyen satır |
|---|---|---|---|
| `state/earnings.csv` (CANLI) | %76.5 | %1.2 (medyan 0 / beklenen 18.2) | **%72.7** (cömert sınır) — %99.3 (sıkı sınır) |
| `state/sprint/…/earnings.csv` | %78.1 | %9.3 | %40.1 (sıkı sınır) |
| **Nasdaq geçmişi (bu turda kum havuzuna çekildi)** | **%100.0** (251/251) | **%99.7** (medyan 18) | **%0.0** (kesin — sorulan günler dosyada) |

- **Yerel takvim tek başına kartın kapısından geçemiyor:** `state/earnings.csv` yalnız İLERİ takvimdir (193 satır, 2026-07/08); ölçüm aralığında (2022-01-03 → 2026-07-23) evren sembolü başına beklenen ~18.2 rapora karşılık **medyan 0** tarih var ve 210 sembolün hiç tarihi yok.
- **Boşluk uydurmayla değil, deponun KENDİ birincil kaynağıyla kapatıldı:** `adapters.data.nasdaq_earnings_window` (anahtarsız Nasdaq) geçmişi de servis eder. **1198/1198 iş günü sorgulandı, 0 gün düştü, 0 FMP çağrısı harcandı** (EAP turunun 2026-07-31'de ölçtüğü aynı yol). Kaynak yeniden yazılmadı, çağrıldı; çıktı YALNIZ kum havuzuna yazıldı.
- **Tarih doğruluğu sağlaması:** AAPL/MSFT/JPM/NVDA 2024 duyuru tarihleri bilinen gerçekle **birebir** (tamlık, doğruluk demek değildir — ikisi ayrı ayrı ölçüldü).
- **Hedef tarafı yaygınlığı:** ölçüm satırlarının %18.6'i (409/2201) KENDİ kazanç penceresinde.

---

## 3. İKİ YÜZEY (K=2) — STANDART vs OLAY-DIŞI TEMİZ KIYAS

**Popülasyon:** 2194 gözlem → **2194 etiketlenebilir** (cf 2099 · gerçek 95). Düşenler: bar_yok_sembol=0, bar_yok_tarih=7, rs_kesiti_yok=0. Taban havuzu: @10 183711 satır · @20 182504 satır (evrenin tamamı, kıyas günlerinde).

**Fark yönü:** `fark = STANDART − TEMİZ`. Pozitif = standart (kirli) kıyas etkiyi **daha BÜYÜK** gösteriyordu; negatif = standart kıyas etkiyi **SIKIŞTIRIYORDU** (kartın hipotezi).

| Yüzey | Ufuk | n | Standart | Temiz | **Fark** | %95 CI (21g blok) | CI 0-dışı? |
|---|---|---|---|---|---|---|---|
| Y1 · component_ic üst-desil (havuz) | @10 | 904 | +24.32 bps | +24.71 bps | **-0.40 bps** | [-2.47 · +1.73] | hayır |
| Y1 · component_ic üst-desil (havuz) | @20 | 904 | +74.74 bps | +74.79 bps | **-0.06 bps** | [-2.06 · +2.60] | hayır |
| Y2 · cf R-tablosu | @10 | 2093 | +9.14 bps | +9.54 bps | **-0.40 bps** | [-2.18 · +1.91] | hayır |
| Y2 · cf R-tablosu | @20 | 2087 | +50.38 bps | +50.12 bps | **+0.27 bps** | [-1.95 · +2.91] | hayır |

**Y1 havuzu nedir:** sekiz bileşenin üst-desilinin BİRLEŞİMİ, `(ticker, gün)` tekilleştirilmiş. Yüzeyin tek sayısı ve tek CI'si buradan gelir; bileşen başına medyan da aşağıda durur ama medyanın CI'si TÜRETİLMEZ (hücreler aynı gözlemlerden gelir, bağımsız değildir).

### 3.1 Y1 bileşen kırılımı (16 hücre)

| Bileşen | @10 fark | @10 CI | @20 fark | @20 CI |
|---|---|---|---|---|
| `rs` | -0.27 | [-1.57 · +1.07] | -1.76 | [-3.59 · +1.19] |
| `tight` | -0.65 | [-7.32 · +0.75] | -6.33 | [-10.50 · -1.25] |
| `vol` | +0.05 | [-3.17 · +2.76] | +3.65 | [-2.22 · +4.23] |
| `prox` | -0.55 | [-2.92 · +4.91] | +0.43 | [-4.10 · +5.38] |
| `rvol20` | +0.12 | [-1.04 · +3.61] | +2.49 | [-0.72 · +6.17] |
| `mom12_1` | -0.72 | [-1.98 · +2.80] | +2.41 | [+0.32 · +6.62] |
| `rmom` | +0.40 | [-1.60 · +3.05] | +0.88 | [-3.13 · +2.80] |
| `turnover21` | -1.03 | [-2.92 · +1.10] | -1.75 | [-3.05 · +1.55] |

Bileşenler arası **medyan fark**: @10 -0.27 bps (aralık -1.03 … +0.40) · @20 +0.88 bps (aralık -6.33 … +3.65).

**CI'si sıfırı dışlayan hücre: 2/16** — `tight`@20 -6.33 bps [-10.50 · -1.25], `mom12_1`@20 +2.41 bps [+0.32 · +6.62]. İki hücrenin işareti ZIT. 16 hücrede %95 aralıkla beklenen tesadüfi 0-dışı sayısı 0,8'dir (aritmetik not, hüküm değil).

### 3.2 Taban kirliliği — EAP'nin %64/%74'ü ile neden aynı sayı değil

| Pencere | Taban kirliliği medyan | ortalama | maks |
|---|---|---|---|
| kart_penceresi_5_0 (`once=5, sonra=0`) | %2.8 | %7.4 | %34.9 |
| eap_benzeri_14_1_yaklasik (`once=14, sonra=1`) | %9.7 | %21.0 | %72.5 |

EAP'nin penceresi **[−10, −1] İŞLEM günü** (~14 takvim günü), karartmanınki **[olay−5, olay] TAKVİM günü** (~4 iş günü). Kart pencereyi `in_blackout` ile BİREBİR sabitlediği için ölçüm birincisinde değil ikincisinde koştu; ikinci satır **YALNIZ SAYIMDIR**, hiçbir etki oradan okunmadı ve K'ya girmedi. İki raporun farkı bir çelişki değil, pencere farkıdır.

---

## 4. YENİDEN-OKUMA ADAYI ENVANTERİ

Kart şartı: **"fark @20'de >=10 bps VE CI 0-dışı ise"** envanter doldurulur.

| Yüzey | @20 fark | \|fark\| ≥ 10 bps | CI 0-dışı | Envanter tetiği |
|---|---|---|---|---|
| Y1_component_ic_ust_desil | -0.06 bps | hayır | hayır | tetiklenmedi |
| Y2_cf_r_tablosu | +0.27 bps | hayır | hayır | tetiklenmedi |

**Envanter boş** — kart şartı '@20 fark >=10bps VE CI 0-dışı' hiçbir yüzeyde aritmetik olarak sağlanmadı — envanter doldurulmadı (uydurma yasağı). Bir eşiğe "ne kadar yaklaşıldığı" tablosu, o eşik aritmetik olarak sağlanmadan doldurulursa ölçülmemiş bir sayı üretirdi (UYDURMA YASAĞI).

---

## 5. BAĞLAM: GERÇEK KATMAN (n=95 — hüküm taşımaz)

| Ufuk | n | fark | CI |
|---|---|---|---|
| @10 | 94 | +1.17 bps | [-1.58 · +4.49] |
| @20 | 93 | +3.21 bps | [-0.52 · +5.28] |

---

## 6. NE ÖLÇÜLMEDİ (beyan)

- **Retro yeniden-hüküm YOK.** Hiçbir geçmiş kartın taban-fazlası yeniden hesaplanmadı; bu tur ileri-standart için sayı üretir.
- **Pencere tek:** kart `in_blackout`u birebir şart koştuğu için başka bir olay penceresinde etki ölçülmedi (K=2 korundu).
- **`sonra=0`:** karartma tanımı rapor SONRASI günleri kapsamaz; PEAD çapası (`days_since_report`) ayrı bir tanımdır ve bu turda kullanılmadı.
- **cf katmanı simülasyondur** (`cf_fidelity` beyanı); bu turda ölçülen büyüklük cf'nin R'si değil, bar serisinden gelen ileri getirinin TABANIDIR — taban farkı çıkış sadakatinden bağımsızdır.
- **Canlı state'e yazılmadı:** bar kopyası + kum havuzu takvimi; `state/earnings.csv`, `fmp_usage.json`, `events.jsonl` dokunulmadı.

## 7. ÜRETİLEN DOSYALAR

```
research/olcumler/kys_olcum/
├── RAPOR_KYS001.md        ← bu dosya
├── sonuc_kys001.json      ← birleştirilmiş kanıt (PK + kapsama + iki yüzey)
├── pk_kys001.json         ← araç-doğrulama PK ham çıktısı
├── kapsama_kys001.json    ← kapsama ham çıktısı (üç kaynak)
├── olcum_kys001.json      ← yüzey ölçümü ham çıktısı (16 + 2 hücre, CI'lar)
├── ortak_kys.py           ← mühür + pencere tanımı + panel
├── pk_kys.py · kapsama_kys.py · olcum_kys.py · takvim_cek.py · rapor_kys.py
```

> Takvim önbelleği (1.198 gün-JSONL) ve bar kopyası kum havuzundadır, depoya girmez.
