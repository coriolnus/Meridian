# TEŞHİS — "öğrenme ve antrenman çalışmıyor" · 2026-08-21

**Operatör bildirimi:** *"öğrenme ve antrenman da çalışmıyor bunlar da çalışsın."*

## HÜKÜM: İKİSİ DE BOZUK DEĞİL — İKİSİ DE TASARIM GEREĞİ BEKLİYOR

Hiçbir kod değişmedi, hiçbir şey onarılmadı. Ölçüm, "arıza" sanılan şeyin iki ayrı **kapı** olduğunu
gösterdi ve ikisi de doğru çalışıyor.

### 1 · ANTRENMAN (`meridian-sprint`) — saat penceresi, 7 dakika kalmıştı

    sprint.should_run() → kos=False · sebep="saat_dilimi_disinda"
    saat=21 · pencere=[22, 6]        (ölçüm anı 21:53 UTC)
    gecen_gun=6 · taze_hipotez=3 · n_hipotez=60   ← DİĞER ŞARTLAR SAĞLANMIŞ

Sprint 22:00–06:00 UTC bakım penceresinde koşar. Ölçüm 21:53'te yapıldı; birim `inactive`
görünüyordu çünkü penceresi **7 dakika sonra** açılıyordu. `_arama_durumu` da temiz
(`mesgul=false`), yani sprint'i bloke eden bir arama yok.

### 2 · ÖĞRENME (`meridian-learn`) — 30 günlük aşırı-uydurma ufku

Birim **çalışıyor**: 2026-08-16'dan beri `active`, **0 restart**, kalp atışı taze
(`last_poll` 21:50). Düşmüş değil.

    _horizon_progress: {"regime":"trend_up", "trades":6, "trades_needed":5,
                        "span_days":2, "min_days":30, "ready":false}

İşlem sayısı şartı SAĞLANIYOR (6 ≥ 5). Engelleyen **takvim açıklığı**: `REFLECTION_MIN_DAYS=30`
(kod: "Phase 3 overfitting horizon"), eldeki 6 işlem yalnız **2 güne** yayılmış.

Arka plan rejimi dalı da haklı olarak kapalı — canlı tabanlarla ölçüldü:

    chop       taban=887  yeni=0  horizon_ok=False   ← 2026-08-17'de zaten yansıdı
    trend_down taban=0    yeni=0  horizon_ok=False   ← hiç işlem yok
    high_vol   taban=0    yeni=0  horizon_ok=False   ← hiç işlem yok

Son gerçek yansıma **2026-08-17 01:21** (`reflections=1`, `last_reflect_at=887`). Sıradaki
`trend_up` yansıması ~2026-09-16'dan önce açılamaz (30 gün − 2 gün).

**ÖLÇÜM TUZAĞI, KAYDA GEÇSİN:** `_bg_ready_regime`ı taze bir Python sürecinde çağırdığımda
**`chop`** döndü ve bir an "arka plan dalı ateşlemeli ama ateşlemiyor" sandım. Yanlıştı: fonksiyon
rejim başına TABAN kullanıyor ve taze süreçte `_state` boştu, yani 887 işlemin hepsini "yeni"
sayıyordu. Canlı `hermes_status.json` yüklenince cevap **`None`** oldu — doğrusu bu. Süreç-içi
durum taşıyan bir fonksiyonu durumsuz çağırmak, ölçtüğü şeyi uydurur.

## ASIL SORUN BAŞKA: `evaluated=40 · cleared=0`

Isınma sprinti her saat koşuyor ve **40 aday değerlendirip sıfırını geçiriyor**
(`last_result: "no_clearing_candidate"`, `_warm_ticks=1256`). Öğrenmenin beklemesi tasarım;
**hiçbir adayın geçmemesi değil.**

Bunun `Ö-48` ile bağlantısı KUVVETLE MUHTEMEL ama ÖLÇÜLMEDİ: `Ö-48` keşif bütçesinin **%62'sinin
motorda karşılığı olmayan HAYALET DÜĞMELERE** gittiğini ölçmüştü (`bounds.yaml` 32 düğme, canlı
`strategy.yaml` 18, 14 öksüz). Adayların çoğu motorun okumadığı bir düğmeyi deniyorsa, sıfır
geçmesi beklenen sonuçtur. **Bu bir hipotezdir; sonda dağılımı ölçülmeden hüküm verilmez.**

## OPERATÖRE: BEKLENTİ DÜZELTMESİ

"Öğrenme çalışsın" için yapılacak bir şey YOK — çalışıyor. Öğrenmenin ÜRETMESİ için gereken şey
kod değil **kanıt**: 30 günlük takvim açıklığı ve rejim çeşitliliği. Ufku kısaltmak mümkündür ama
o bir EŞİK değişikliğidir (aşırı-uydurma koruması) ve kart-önce açılır — bu belge onu ÖNERMEZ.
