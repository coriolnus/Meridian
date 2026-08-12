# TEŞHİS — "sistem eski rakamlara göre çalışıyor, P&L +20k göstermiyor" (2026-08-13)

Operatör üç iddia/talep getirdi (2026-08-12 gece): (1) bileşenler C+mb @5R'ye göre optimize edilmeli,
(2) işlemler backfill'e alınıp değerlendirme bileşenleri güncellenmeli, (3) sistem hâlâ eski rakamlara
göre çalışıyor ve P&L bunu yansıtmıyor — "geriye dönük +20k beklerdim". Hepsi canlıda ölçüldü.

## 1) +20.685$ NEDİR, NE DEĞİLDİR (en kritik ayrım)

**+20.685$ GERÇEKLEŞMİŞ KÂR DEĞİLDİR.** EDG-032 damgası bir REPLAY (simülasyon) sonucudur:
2022-01-01 → 2026-07-30 arası **4,5 yıl**, 251 sembol, tarihsel barlar üzerinde motorun yeniden
koşturulması. "Bu paketi 2022'den beri koşsaydık ne olurdu" sorusunun cevabıdır.

O 885 işlem **hiç yapılmadı**. Geriye dönük bir hesaba yansıyamaz — yansısaydı sistemin tüm dürüstlük
mimarisi (sim ≠ gerçekleşen) çökerdi. Kâğıt hesap 2026-07-10'da açıldı; paket 2026-08-12 20:13Z'de
canlıya indi. Yani paketin canlı ömrü **bir gündür** ve henüz tek işlem üretmemiştir.

| | replay (EDG-032) | CANLI (gerçekleşen) |
|---|---|---|
| pencere | 2022-01 → 2026-07 (4,5 yıl) | 2026-07-10 → bugün (~1 ay) |
| işlem | 885 | 97 kapanan + 4 açık |
| P&L | +20.685$ (simüle) | **−5.264$** (defter toplamı) · reset sonrası **+278$** |
| paket | C+mb @5R | 08-12 20:13Z'ye kadar ESKİ paket (slot5 · 1,0R · rampa 3/8 · mb dormant) |

Yani canlı −5.264$'lık zararın TAMAMI eski paketle üretildi. Yeni paketin canlı karnesi henüz BOŞ.
Replay'in doğru kullanımı: "bu paket 4,5 yılda pozitif ve daha yüksek sharpe verdi" — bir gelecek
beklentisi, geçmiş bir kazanç değil.

## 2) "Eski rakamlara göre çalışıyor" — KISMEN DOĞRU (bir gerçek split var)

Canlıda ölçüldü (`config.load_strategy()`, `config.goal()`, `strategy.ARMED_SETUPS`):

| bileşen | canlı değer | durum |
|---|---|---|
| position_size_r | **0,5** (strategy.yaml v5) | ✅ YENİ |
| max_open_positions | **20** | ✅ YENİ |
| derisk rampa | **0,15 / 0,36** (kaynak: goal.yaml) | ✅ YENİ |
| ARMED_SETUPS | 4'lü (**mb dahil**) | ✅ YENİ |
| goal.max_drawdown | 0,08 | ⏳ 0,16 kararı alındı, dağıtım bekliyor |
| **scoreboard.current_version** | **3** | ❌ **SPLIT — motor v5, karne v3** |

**SPLIT'İN KÖKÜ:** 08-12 mini-penceresinde `scoreboard.json` scp ile taşındı, ama v234 bayat-defter
migrasyonu dosyayı `.migrated-20260812-201359-p192112` olarak kenara koydu (DB otorite) ve **DB'ye
yazılmadı**. Sonuç: motor v5 parametreleriyle karar veriyor, ama karne/öğrenme/rollback katmanı
"yürürlükteki sürüm 3" sanıyor (`analytics.py:683,2168` · `hermes.py:133` · `recompute.py:292` ·
`rollback.py:355`). Yeni hipotezlerin ebeveyni yanlış, sürüm-bazlı değerlendirme yanlış sürüme
atfediyor. Bu makullük alarmındaki `orphan_state_files` kaleminin de kaynağı.

**Ayrıca:** `equity_curve` son noktası **2026-07-20** (882 nokta, 24 gün donuk) — panodaki P&L eğrisi
bu yüzden hareketsiz (ROADMAP §2-9 kadanslı-yazar planı; artık görünür etkisi var).

## 3) ADAY KURAKLIĞI — ÖLÇÜLDÜ: ARIZA DEĞİL

Canlı döngü çalışıyor (`daily_cycle` 2026-08-12 20:46Z, regime=trend_up, data_ok=true) ama
`candidates: 0, near_miss: 0`. Kuraklık gerçek: son plan 2026-08-07.

Kök ölçümü (canlıda, 80 sembol, barlar geriye kesilerek — "o gün taransaydı"):

| kesim | karşılık gelen seans | aday |
|---|---|---|
| 0-1 bar | 08-11, 08-12 | **0** |
| 3 bar | ~08-07 | 2 (EA breakout_vcp · TTWO pead) |
| 5 bar | ~08-05 | 3 (LLY momentum_burst · CHTR exhaustion_hammer) |
| 10 bar | ~07-29 | 0 |
| 20 bar | ~07-15 | 2 (NVDA · MRNA exhaustion_hammer) |

**HÜKÜM: tarama motoru SAĞLAM.** Aday üretimi 80 sembolde seans başına 0-3 arasında dalgalanıyor ve
bu, trade_plans defteriyle birebir tutarlı (08-05'te 6 plan, 08-07'de 1 plan, sonra sinyalsiz seanslar).
Son 4-5 seans gerçekten sinyalsiz geçmiş — eşik/kod arızası değil, piyasa koşulu. (Bu ayrım EDG-024'ün
"eşikler kanıtla doğrulandı" hükmüyle de tutarlı: gevşetme masada para bırakmıyor.)

Yan bulgu: `finviz_unavailable` — Elite token yok, public scraping otonom döngüde kapalı; evren yalnız
REPLAY_UNIVERSE (251) ile kuruluyor. Bu bir DARALTMA (§3-8 operatör bloğu) ama kuraklığın kökü değil.

## 4) SONUÇ: NE YAPILMALI

1. **scoreboard split'i kapat** (gerçek arıza) — DB'deki `current_version` v5'e, uygulamanın kendi
   yazım kapısından; bakım penceresi gerekir. Ardından `.migrated-*` artığı temizlenir.
2. **equity_curve kadanslı yazar** (§2-9) — pano P&L'i 24 gündür donuk; bu kalem artık öncelikli.
3. **Paket-bağımlı eşik envanteri** — `docs/DENETIM-PAKET-BAGIMLI-ESIKLER-2026-08-13.md` (ayrı tur).
4. **Backfill'in DOĞRU biçimi:** replay işlemleri canlı deftere ASLA yazılmaz (sim≠gerçek yasası).
   Meşru olan: cf defteri / kalibrasyon / öğrenme katmanının replay kanıtıyla beslenmesi — hepsi
   sim-etiketli ve `cf_fidelity` çapasıyla ölçülü. Kapsam ayrı kartla belirlenir.
5. **Beklenti hizalaması:** yeni paketin canlı karnesi bugün başlıyor. Anlamlı bir canlı ölçüm için
   örneklem gerekiyor (N4 eşiği ~200 işlem); replay 4,5 yılda 885 işlem üretti → canlıda yılda ~195
   işlem beklenir, yani ilk ciddi karne birkaç ay sonra.
