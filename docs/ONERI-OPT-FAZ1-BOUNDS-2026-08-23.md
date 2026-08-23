# ÖNERİ — OPT Faz-1 kablolama: bounds aralık önerileri (OPERATÖR ONAYINA) · 2026-08-23

**Durum: ÖNERİ. `state/bounds.yaml`a HİÇBİR satır yazılmadı** — sınırlar operatör onaylıdır
(ROADMAP WP3-B madde 10 (1)). Bu tur yalnız KABLO döşedi: aday sabitler params-okur oldu,
anahtar yokken bugünkü sabit varsayılan aynen (özdeşlik çivileri:
`tests/test_opt_faz1_kablolama_v276.py`, 13/13 yeşil; komşu çivi suite'leri 240 geçti / 0 kırmızı).

Uygulama-politikası sınıfları WP3-B'deki Rol-1 önerisinden (2026-08-12, operatör onayı bekler):
**HEP-PENCEREYE** = risk-artıranlar (rampa/slot/boyut/ısı) + eşik-gevşetme;
**DONUK-EŞİK-OTOMATİĞE** = çıkış-parametre iyileştirmeleri, skor-ağırlıkları (gölge-doğrulamalı).

---

## 1) WP3-B'nin andığı beşli — ölçülen mevcut konum (envanter)

| Aday | Bugünkü konum | Değer | Okuyucu zinciri | Hüküm |
|---|---|---|---|---|
| derisk bandı | `goal.yaml limits.derisk_full_dd/floor_dd`; fail-safe `broker.py:46-47` | 0.15 / 0.36 | `broker.derisk_ramp()` → `derisk_mult`/`max_positions_at` → loop/backtest fill | **ZATEN KABLOLU** (2026-08-12, test v237). Monkeypatch ihtiyacı bitmiş (`override` argümanı). LIMIT_KEYS üyesi — arama GÖREMEZ, **bounds'a girmesi ÖNERİLMEZ** (HEP-PENCEREYE; yürürlükteki politika `guard.py:59-65` yorumu) |
| max_open | `goal.yaml limits.max_open_positions` (LIMIT_KEYS, `guard.py:51`) | 20 | `loop.py:539/1419/1687/1779`, `intraday_shadow.py:181` | **ZATEN KABLOLU**, operatör kalemi. 25d c-1 damgası: eşzamanlı tepe 13<20 — tavan bugün bağlamıyor; **bounds'a girmesi ÖNERİLMEZ** (slot = risk vanası, HEP-PENCEREYE) |
| position_size_r | `bounds.yaml` satırı VAR (0.1–1.0/0.1) | canlı 0.5 (strategy.yaml) | `strategy.py` 7 okuma (`_f(params,...,1.0)`) → plan boyutu | **ZATEN ARANABİLİR**. Terfisi HEP-PENCEREYE (boyut risk-artıran) — aralık değişikliği önerilmiyor |
| scale_out | `bounds.yaml` `exit.scale_out_r/frac`; `broker.scale_out` params-okur | r 2.0 / frac 0.0 (kapalı) | broker.scale_out → yaşam-döngüsü/kapanış satırı | **KABLO TAM, ALET KAPALI.** Silahlanması **EDG-2026-027 hükmüne tabidir** (027/029 CI-negatif; TCA hükmü güçlendirdi) + **WP1-C zorunluluk şartı** (bankalama-barı trail=entry_fill kusuru önce düzeltilir). Beyan artık kaynak yorumunda ZORUNLU ve çivili (test D1) |
| chandelier | `bounds.yaml` `exit.chandelier_lookback` (0–30/5); `strategy.py manage_position` | 0 (kapalı) | manage_position → trail | **ZATEN KABLOLU/ARANABİLİR** |

Sonuç: beşlinin dördü bu turdan ÖNCE kablolanmıştı (derisk 2026-08-12'de "OPT Faz-1'in İLK
kalemi" olarak); bu tur scale_out'a zorunlu silahlanma beyanını ekledi ve kalan işi kendi
taramasının adaylarına taşıdı.

## 2) Bu turda KABLOLANAN yeni adaylar + önerilen aralıklar

Hepsi fonksiyon-gövdesi sabitiydi; şimdi params-okur (`_f(params, anahtar, bugünkü-sabit)`).
Bounds satırı İNMEDEN Hermes öneremez (guard: "not a tunable in bounds.yaml" — test A1).

| # | Anahtar (varsayılan) | Eski yeri | Önerilen aralık | Sınıf | Riskler / şerhler |
|---|---|---|---|---|---|
| 1 | `exit.trail_arm_r` (1.0) | `strategy.manage_position` — trail ratchet + chandelier silahlanma eşiği "kâr > 1R" (iki kullanım, TEK düğme) | `{min: 0.0, max: 3.0, step: 0.5}` float | DONUK-EŞİK-OTOMATİĞE (çıkış iyileştirme) | 0.0 = trail hemen silahlanır (sıkılaştıran yön); >1 kâr korumasını geciktirir (gevşetme yönü kaybı ölçümle savunulmalı). `exit.breakeven_r` ile etkileşir |
| 2 | `exit.giveback_arm_r` (1.0) | `manage_position` — giveback "zirve kârı > 1R" eşiği | `{min: 0.5, max: 3.0, step: 0.5}` float | DONUK-EŞİK-OTOMATİĞE | **ATIL-EKSEN TUZAĞI:** `exit.giveback_pct=0` (bugünkü canlı) iken düğme yapısal no-op — tek başına aranırsa probgate'in ULP-ayrımı onu "atıl" damgalar; yalnız giveback açıkken ya da bileşik kartla aranmalı |
| 3 | `entry.vol_score_sat` (3.0) | `evaluate_entry` — `min(vr/3, 1)` doyma noktası | `{min: 1.5, max: 6.0, step: 0.5}` float | DONUK-EŞİK-OTOMATİĞE (skor-ağırlığı ailesi, gölge-doğrulamalı) | g2 kanıtı "2.0 üstü monoton-iyi değil" derken doyma eğrisi aranamıyordu. ŞERH: `component_ic.py:204` ölçüm-yüzeyi kopyası 3.0 sabit — satır inerse senkron kararı o turda verilir (aşağıda §4). sat<=0 elle-yazımı işaretli-düşüşle 3.0'a döner (YASA 4) |
| 4 | `entry.rvol_band_center` (1.75) / `entry.rvol_band_halfwidth` (0.75) | `rvol_band_score` modül sabitleri (`RVOL_BAND_CENTER/HALFWIDTH`) | center `{min: 1.0, max: 2.5, step: 0.25}` · halfwidth `{min: 0.25, max: 1.5, step: 0.25}` | DONUK-EŞİK-OTOMATİĞE | Kanıt bandı 1.5–2.0 (+1.84%, n=955 — bounds.yaml g2 notu); merkez/genişlik o kanıtın içinde kalmalı. `entry.w_rvolband=0` (canlı) iken atıl-eksen — w ile bileşik aranmalı. halfwidth<=0 işaretli-düşüşle 0.75'e döner |
| 5 | `entry.rs_dual_pace` (3.0) | `evaluate_entry` — çift-ufuk pro-rata çarpanı `mom_short·3 < mom_long` | `{min: 1.0, max: 5.0, step: 0.5}` float | DONUK-EŞİK-OTOMATİĞE (kenar filtresi katılığı) | ÇİFT-UYKUDA: `entry.rs_dual_horizon=0` (canlı) iken hiç okunmaz → atıl-eksen; yalnız horizon=1 kollarında/bileşikte aranmalı. 3.0 = 63/21 takvim pro-rata'sı — 3'ten sapma "tanım" değil "katılık" olarak okunmalı |

**K-deflate uyarısı (CLAUDE.md 3):** her yeni bounds satırı arama grid'inde K'yı ÇARPARAK
büyütür. Altı anahtarın birden inmesi önerilmez; kanıt-öncelikli alt küme: **önce #3 + #4**
(g2 kanıt tabanı hazır), #1 çıkış-reformu penceresinde, #2/#5 ancak ebeveyn bayraklarıyla birlikte.

## 3) Değerlendirilip ERTELENEN adaylar (ölçülen gerekçeyle)

- **`EXPLORE_MAX_POS/MAX_R/TOTAL_R`** (`loop.py:44-46`, 25d c-4): risk vanası (slot/boyut →
  HEP-PENCEREYE, bounds'a girmez) + kaynak-metin çivisi `test_ops_v11.py:225-230` bilinçli
  taşınmadan kırılamaz + c-4 ölçümü "tavan bağlamıyor, kaynak kurumuş" — kablo bugün değer üretmez.
  İstenirse limits-idiomu (derisk emsali) ayrı turda, Rol-1 kararıyla.
- **`probgate.P_BASE/P_CONFIRM`** (25d c-3 EZEN): kapının kendi ship eşiği arama uzayına
  GİREMEZ — makine kendi kapısını gevşetirdi (öz-referans; CLAUDE.md "eşik sonradan değişmez").
  Operatör kalemi olarak kalır.
- **`guard.DISCIPLINE_MIN_RR`** (25d c-6): disiplin vetosu + watchdog bütünlük çivisi
  (`watchdog.py:2337-2339`). Bounds yolu ZATEN VAR ve daha doğru: `exit.profit_target_r`
  min'inin 2.0 altına bilinçli indirilmesi (bounds.yaml'daki c-6 EZER notu bunu adıyla bekletiyor)
  — operatör kararı, satır değişikliği bu raporun kapsamı dışında.
- **`execution_v2.limit_pct_cap` (0.04)** (25d c-2 EZEN): GOAL_KEYS — icra yasası değişmez
  ("ajan kendi dolum fiyatını seçerdi", guard.py gerekçesi). `limit_atr_mult` ATIL ekseni
  25b-4 damgasıyla beyanlı; dokunulmadı.
- **`momentum_burst`/`hammer` kendi vol sabitleri** (`strategy.py:625` /3.0, `:684` /5.0) ve
  kurulum-içi diğer sabitler: kurulumların ikisi de silahlı değil ya da ayrı seçilim yüzeyi;
  silahlanma-öncesi knob açmak ölçüsüz K şişirir. VCP (silahlı ana yüzey) önceliklendi.
- **`PIVOT_LOOKBACK/ATR_PERIOD/RS_LOOKBACK/MOM_RANK_WINDOW`** modül sabitleri: gösterge-tanımı
  sınıfı — değişimi dataset/ölçüm yüzeylerine yayılır (blast radius büyük), ayrı kart ister.

## 4) Bounds satırı İNDİĞİ GÜN yapılacaklar (satır başına kontrol listesi)

1. `config.default_strategy()["params"]`a tohum değeri ("Every value sits inside bounds.yaml"
   sözleşmesi ancak satır inince kurulur; bugün bilinçli olarak eklenmedi — test A1 çivisi).
2. `exit.*` anahtarları zaten `shadow_lifecycle.LIFECYCLE_READ_DEFAULTS`ta (bu turda eklendi,
   AST çivisi doğruluyor); `entry.*` anahtarları tabloya GİRMEZ (tablonun kendi gerekçesi).
3. `entry.vol_score_sat` inerse: `component_ic.py:204` senkron kararı (ölçüm yüzeyi üretim
   varsayılanında mı kalır, canlı knob'u mu izler) — açık karar, sessiz bırakılmaz.
4. Atıl-eksen çiftleri (#2 giveback_pct'e, #4 w_rvolband'a, #5 rs_dual_horizon'a bağlı) için
   arama kuralı: ebeveyn bayrağı kapalıyken tek-değişkenli öneri probgate'te no-op düşer —
   bileşik kart ya da ebeveyn-açık kolu şart.
5. K sayımı: eklenen her satır K-deflate çarpanına girer; aynı turda inen satır sayısı bilinçli
   sınırlanır (§2 sırası).

## 5) Bu turda değişen dosyalar

- `meridian/strategy.py` — trail/chandelier arm (`exit.trail_arm_r`), giveback arm
  (`exit.giveback_arm_r`), vol doyma (`entry.vol_score_sat`), rvol bant argümanları
  (`entry.rvol_band_center/halfwidth`), çift-ufuk pace (`entry.rs_dual_pace`).
- `meridian/broker.py` — `scale_out` docstring'ine ZORUNLU silahlanma beyanı (EDG-2026-027/029 +
  WP1-C; kod yolu değişmedi).
- `meridian/shadow_lifecycle.py` — `LIFECYCLE_READ_DEFAULTS`a iki yeni exit anahtarı.
- `tests/test_opt_faz1_kablolama_v276.py` — özdeşlik + okuma + pozitif kontrol çivileri (13 test).
- `state/bounds.yaml` / `state/goal.yaml` — **DOKUNULMADI.**
