# WP3 28g/28h/28i — incumbent holdout −0,5366 TEŞHİSİ (ölçüm kaydı, 2026-08-22)

Hüküm YOK — hüküm Rol-1'in. Bu dosya yalnız ölçümdür.

## Bağlam (okundu, ölçülmedi)
- −0,5366'nın kaynağı: **canlı A1 `state/inc_cache.json`**, `eval_regime=None`, aktarım:
  `docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md:472-474` (oos +0,2354 · holdout −0,5366; sapma 0,772; eşik `reflect.HOLDOUT_DIVERGENCE=0,10`; ship'i bloklamaz, `reflect.py:52`).
- Fold-geometrisi elemesi: `ROADMAP.md:1773-1784` madde #47 (v247-B, 2026-08-14) — holdout fold DEĞİL,
  OOS dışı ayrı 91 günlük pencere (2026-04-30 → 2026-07-30); fold'lar holdout skoruna girmez.
- Geometri (inc_cache anahtar): IS 2022-01-01 → OOS 2024-01-01..2026-04-30
  (search 2024-01-11..2025-08-18 · confirm 2025-08-18..2026-04-30, ambargo 10g) → holdout 2026-04-30..2026-07-30.
- Skor yasası (`score.py:148-151`): `kıs(0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c)`;
  goal: hedef_30g 0,07 · **max_dd 0,16 (08-13'te 0,08→0,16)** · min_sharpe 1,2 · min_sample 30.

## Ölçüm tabanı ve bağlam tuzağı
- **Yerel `state/inc_cache.json` −0,5366'yı İÇERMİYOR** (rev ~2026-07-29, TESHIS'ten eski):
  üç girdide de `holdout_score=None` — nedenleri `holdout_detail.reason`: **n=11/30 ve n=5/30**.
  → −0,5366 YERELDE yeniden üretilemez (replay tabanı holdout'ta min_sample altı).
- Canlı A1 SSH okuması sınıflandırıcı tarafından ENGELLENDİ (denendi, yapılamadı).
- Kullanılan vekil taban: `research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db`
  (canlının 2026-08-22 kopyası; 893 işlem 2022-01-07..2026-08-20; SALT OKUMA).
- **Vekil, hedef sayıyı 0,0001 farkla yeniden üretti:** holdout dilimi (backtest `_in_segment` yasasıyla)
  `score_detail` → **−0,5365** (inc_cache: −0,5366; fark ≈ M2M-dd bacağı/yuvarlama). Vekil ≈ asıl popülasyon.

## Hipotez tablosu

| # | Hipotez | Durum | Kanıt |
|---|---------|-------|-------|
| H1 | Holdout penceresi rejim kompozisyonu eğitimden farklı (düşmanca zemin) | **ÇÜRÜDÜ (yön TERS)** | PIT rejim çizelgesi (replay yasasıyla, FETCH_START=2021-01-01 tabanı): holdout 62 günün **54'ü trend_up (%87)**, 8'i chop; SPY **+%3,2**, pencere-içi mdd %4,5. IS: %28 trend_up / %36 chop / %30 high_vol. Kompozisyon farklı ama LEHTE yönde; işlemlerin **87/87'si trend_up** etiketli. `rejim_kompozisyon.json` |
| H2 | Örneklem kuraklığı (learning-loop-parent-baseline sınıfı) | **ÇÜRÜDÜ (canlı ölçüm için)** — yerelde TERSİ geçerli | Canlı-kopya holdout **n=87 ≥ 30**; aylık 30/38/18 — kuraklık yok. YEREL replay tabanında ise holdout **n=5/30 → None**: kuraklık canlı sayının nedeni değil, yerelde yeniden-ölçümün engeli. |
| H3 | Bileşen ayrışması — hangi terim negatifi sürüklüyor | **ÖLÇÜLDÜ** | −0,5365 = 0,5·ret_c(**−0,688**) + 0,3·dd_c(+0,024) + 0,2·sharpe_c(**−1,0 KIRPIK**) → katkılar: **getiri −0,344 (%64)** · **sharpe −0,200 (%37)** · dd +0,007 (nötr). Altta: realized_30d −%4,81 · sharpe −4,90 (kırpılmadan 0,2·(−4,9/2,4)=−0,41 olurdu) · dd 0,156 (0,16 tabanına göre nötr; ESKİ 0,08 tabanıyla skor ≈ −0,83 olurdu — sayı goal değişimine duyarlı). `canli_holdout_islemler.json` |

## Negatifin yapısı (ölçülen ek kırılım — `holdout_kirilim.json`)
- **Tekdüze, tek-olay değil:** ay bazında avg_r 2026-05 −0,33 (n=30) · 06 −0,36 (38) · 07 −0,40 (18);
  setup bazında breakout_vcp −0,40 · momentum_burst −0,34 · exhaustion_hammer −0,28 (hepsi negatif).
- **Çıkış karışımı devrildi (confirm → holdout):** stop+stop_gap payı %48 → **%72**; target payı %13,7 → %8;
  kazanma %39,5 → **%21,8**; `regime_flip` çıkışları +0,86R (n=49) → **−0,03R** (n=12).
- **stop_gap (gece açığı) bacağı:** 11 işlem, ort **−1,34R**, toplam −14,76R (toplam −28,52R'nin yarısı).
  En kötü 8 kaybın 8'i yarıiletken/büyük-teknoloji (AVGO −2,87 · MRVL · TXN · NVDA · MCHP · INTC · AAPL · QCOM), 7'si stop_gap.
- **Yoğunlaşma var ama tek açıklama değil:** yarıiletken kümesi 40/87 işlem (%46), toplamı −15,54R;
  geri kalan 47 işlem de negatif (−12,98R, ort −0,28). SPY +%3,2 iken kayıp genele yayılı —
  endeks-rejimi 'trend_up' derken stratejinin evreninde zemin bozuktu (endeks-türevi rejim bunu görmez).
- Karşıt pencere: OOS-confirm (2025-08-18..2026-04-30, %100 trend_up işlem) avg_r **+0,28**, skor +0,53.

## Ölçülemeyenler (uydurma yasağı)
- Canlı A1 inc_cache'in bugünkü hali: None — SSH engellendi (yerel kopya eski).
- −0,5366'yı üreten REPLAY işlem listesi: None — inc_cache `_trades_*` yalnız arama/teyit saklar, holdout işlemleri saklanmaz; yerel replay tabanı min_sample altı. (Vekil DB dilimi 0,0001 farkla örtüştü — popülasyon ≈ aynı.)
- 08-13 canlı ölçümünde n(holdout): None — doğrudan görünmüyor; skor None DEĞİL olduğuna göre n≥30 (yasa `score.py:113`; çıkarım, ölçüm değil).
- Yerel replay yoğunluk anomalisinin kökü (aynı pencere: yerel fold n=21 vs canlı n=249): None — ayrı iş, bu turda ölçülmedi.

## Koşulmayanlar (bilerek)
- Dar yeniden-koşum (walk_forward) KOŞULMADI: vekil ölçüm hedef sayıyı yeniden üretince gereksizleşti;
  ayrıca yerel tabanda holdout n=5 → koşum None döndürür (ölçemez). Tam grid zaten kapsam dışıydı.
