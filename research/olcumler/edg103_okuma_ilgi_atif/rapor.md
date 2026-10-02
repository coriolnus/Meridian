# EDG-2026-103 sayım — 2026-09-25T10:33:10+00:00 → 2026-10-02T10:33:10+00:00

**hukum:** GEÇERSİZ — alet doğrulanmadı

τ = 3/20 (0.15) · W = 48 sa · n_min_karar = 5 (hepsi KARTTAN)

## Betimleyici ara rapor — hüküm DEĞİL — betimleyici ara rapor (netleştirme 8: yalnız K1 ve D)

K2–K4 τ'ya bağlıdır ve alet/pencere doğrulanmadan betimleyici olarak da YAYILMAZ

- K1 (betimleyici): 5/8 — dolu günler ['2026-09-25', '2026-09-27', '2026-09-28', '2026-09-29', '2026-10-01']
- D (betimleyici): 80

## PK/NK

tuttu: **False**
- PK (a) okuma: True · (b) ilgi: False ['3/478'] · (c) atıf: True
- NK atıfsız: True · ilgisiz: True
- EK NK (nk-kripto-madencilik 'bankada yok'): True

## Kill-list (kartın metniyle)

1. **TETİKLENMEDİ** — okuma-olayı enstrümantasyonu kart açılmadan önce yazılırsa/mevcutsa (kart-önce ihlali) → geçersiz (EDG-089 kill-list #1 emsali)
2. **TETİKLENMEDİ** — D < n_min_karar (5), pencere üst sınırında (21 gün) hâlâ → 'ölçülemedi/örnek yetersiz', pencere UZATILMAZ, yeni pencere/karar operatöre (kill-list, dolmayan gün pencereyi uzatmaz emsali)
3. **UYGULANDI** — okuma-olayı logu yer tutucu/hata gövdesini (ör. 'Generating content…') OKUNDU sayarsa → o olay sayılmaz, ayrı işaretlenir (EDG-083 16:24Z paralel-set vakası emsali)
4. **TETİKLENMEDİ** — CLAUDE.md §0-5 (oturum-başı okuma zorunluluğu) pencere içinde kaldırılır/uygulanmazsa → K1 'ölçülemedi' değil KALDI (bu kartın ön şartı)
5. **TETİKLENMEDİ** — okuma-olayı logu ya da karar-envanteri çıktısı sır/kimlik değeri taşırsa (notify.scrub süzgeci atlanırsa) → akış KAPATILIR, tek istisna yok
6. **TETİKLENDİ** — PK/NK tutmazsa hiçbir sayı yayılmaz (apparatus doğrulanmamış demektir)
7. **UYGULANDI** — elle/sentetik PK denemesi gerçek K1–K4 sayımına KARIŞMAZ, ayrı işaretlenir
8. **TETİKLENMEDİ** — τ/W kalibrasyonu pencere AÇILDIKTAN sonra değiştirilirse → geçersiz (eşik sonradan değişmez, §5)

## Netleştirme uygulaması

- (1) S = pencere içindeki UTC takvim günleri: `pencere_gunleri`: pencereyle KESİŞEN UTC günleri; açılış ve kapanış yarım günleri DAHİL
- (2) pencere ve D commit/olay damgasıyla [bas, son): `pencerede` (okuma `ts`, karar `zaman` = kaynağının giriş commit'i — dondur.py); kapanış kanıtı yoksa ARA RAPOR
- (3) K2 tanımı `esikler` cümlesi: `kolonlari_hesapla`: K2 = eşleşen okuma / okuma; çift oranı betimleyici
- (4) W=48 sa commit saatiyle kesin: `ilgili_mi`: 0 ≤ Δ < W (saniye çözünürlüğü)
- (5) K4 paydası D — GEÇERSİZ, netleştirme c ile DEĞİŞTİRİLDİ (aşağıda): uygulanmaz; 'taze = okuma anında is_stale=false' kısmı (5a) ile birlikte geçerli
- (6) τ ve sayfa token kümesi tam içerik, değiştirilmeden: `esik_alanlari` (τ karttan) + `sayfa_goruntusu` (normalize_tokens(tam içerik))
- (7) kill #4: kaldırılma; geç/eksik/kısmi okuma K1'de: `kural_kaldirildi_mi` + `dogrulanmis` (kısmi okuma = tam GET kaydı, sayılır)
- (8) kill #6 HARFİYEN: `say`: PK/NK tutmazsa kolon/D üst düzeyde YOK; K1 ve D yalnız 'hüküm DEĞİL' etiketli betimleyici
- (9) sayım kodu bu dizinde: sayim.py + dondur.py; çivi tests/test_edg103_sayim_v610.py
- b (1a) S = pencereyle kesişen 8 UTC günü: `pencere_gunleri` (yarım uç günler dahil)
- b (4a) W yarı-açık 0 ≤ Δ < 48 sa: `ilgili_mi`
- b (5a) taze ölçülemez → K4 None + üst sınır; kıyas yalnız kesinse: `_k4` + `okuma_tazeligi` (şema is_stale taşırsa betik durur)
- b (6a) EK NK kill #6 kapsamında harfiyen: `pk_nk_denetle`: ifade sayfanın BAŞLIK satırında (kartın 'hükmünü taşımalı'sı)
- b (10) girdi/ depoya girer, sır taşımaz: dondur.py yazmadan önce her dosyayı notify desenleriyle tarar, eşleşmede YAZMAZ; sayım kill #5 aynı taramayı `notify_taramasi` ile dondurulmuş her metne uygular
- c (5) DÜZELTME: K4 paydası `esikler`deki 'atıflı kararlar'; D paydası betimleyici: `_k4`: payda = D'de sayfa/recall/memory/kart_benzer atfı taşıyan kararlar (`atifli_karar`); `betimleyici_D_paydasi`; D_ilgili boşsa ÖLÇÜLEMEDİ
