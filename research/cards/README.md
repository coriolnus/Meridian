# research/cards — Ön-Kayıt Defteri
Kural (iş emri 2026-07-31): kartsız ölçüm kodu yazılamaz/koşulamaz. Her parametre grid'i K'ya
sayılır; eşikler ölçümden SONRA değiştirilemez. Şema: iş emri §5. Durumlar:
registered → measuring → promoted | archived.

<!-- ENDEKS: ÜRETİLEN BÖLÜM — ELLE DÜZENLEME YOK (ops/kart_endeksi_uret.py) -->

## Kart endeksi (ÜRETİLİR — elle düzenlenmez)

Kaynak: `research/cards/*.yaml` → `status` alanı. Üretici: `ops/kart_endeksi_uret.py`.
Bayat mı diye sor: `python ops/kart_endeksi_uret.py --kontrol` (çıkış 1 = bayat).
Konu ve hüküm cümleleri kartın KENDİ metninden KESİLİR (`…`), özetlenmez.

Toplam **79** kart.

### Kayıtlı — ölçüm bekliyor (11)

- **EDG-2026-019** (`registered`) — Aktif skill kümesinin (yaşam-döngüsü-farkında kaynaktan okunur; sabit sayı YAZILMAZ — C10) aday seçimi ve ötesinde ölçülebilir katkısı olup olmadığı…
  · HÜKÜM: 2026-08-09 Rol-1. (Aşağıya bkz: 2026-08-23 kill#1 kaydı — katman kapatma emri)
  · kart: `EDG-2026-019-skill-gorus-defteri.yaml`
- **EDG-2026-053** (`registered`) — 15d-A2 (taslak docs/TASARIM-15D-PIT-FAKTOR-SETI-2026-08-23.md K2'den AYNEN): İLK-İFŞA filtreli çeyrek gelir (Revenues) YoY büyümesi ve İVMESİ…
  · HÜKÜM: 2026-08-23 Rol-1 — ön-kayıt (ölçüm 050/051'den biri inince sırada)
  · kart: `EDG-2026-053-gelir-momentumu.yaml`
- **EDG-2026-054** (`registered`) — E-turu kararı 1/12 (operatör, 2026-08-23: "kartla ölç"): `bars_integrity` 98 kırık dönem/61 sembol buldu ve kanonik tüketiciler…
  · HÜKÜM: 2026-08-24 Rol-1 — ön-kayıt (E-1 operatör kararı; ölçüm 042-zinciri sonrası)
  · kart: `EDG-2026-054-kirli-donem-dislama.yaml`
- **EDG-2026-056** (`registered`) — WP4 eleme bulgusu (2026-08-24): MNST split teşhisi TAM ama kart ve kod YOK (oran-imza taraması repoda 0 eşleşme).
  · HÜKÜM: 2026-08-24 Rol-1 — ön-kayıt (WP4 eleme ÖLÇ sınıfı)
  · kart: `EDG-2026-056-split-oran-imzasi.yaml`
- **EDG-2026-058** (`registered`) — Çoklu-test cezası `p_req = 1 − (0,20 − extra_p)/K` ile uygulanıyor ve `K = len(planned)`, yani o turda PLANLANAN sonda sayısı.
  · kart: `EDG-2026-058-k-enflasyonu.yaml`
- **EDG-2026-059** (`registered`) — D6 tip-rampası ölçümü (2026-08-07) `DESIGN.md`de yürürlükte duruyor ama ölçtüğü İKİ GİRDİ de değişti: (a) sevk edilen YÜZ Recursive Sans → **Inter**…
  · kart: `EDG-2026-059-d6-tipografi-tazeleme.yaml`
- **EDG-2026-063** (`registered`) — 
  · kart: `EDG-2026-063-skill-llm-ikinci-gorus.yaml`
- **EDG-2026-064** (`registered`) — 
  · kart: `EDG-2026-064-merdiven-duvari-yeniden-sinama.yaml`
- **EDG-2026-065** (`registered`) — 
  · kart: `EDG-2026-065-hindsight-faz1-kurulum-recall.yaml`
- **EXE-2026-009** (`registered`) — B-PENCERE-KAYDIR operatör kararı (2026-08-23 brainstorm 2/7, kanıt EDG-2026-047): canlı sabah tarama/emir tetiği 13:30→13:45 UTC'ye kayar.
  · HÜKÜM: 2026-08-23 Rol-1 — ön-kayıt; uygulama kodu bu karttan SONRA (kart-önce)
  · kart: `EXE-2026-009-pencere-kaydirma.yaml`
- **EXE-2026-010** (`registered`) — 
  · HÜKÜM: ön-kayıt 2026-08-31; uygulama kart-önce kuralıyla sonra
  · kart: `EXE-2026-010-hakem-ts-anahtari.yaml`

### Ölçümde (4)

- **EDG-2026-042** (`measuring`) — Sistemin EN KARAR-KRİTİK bilinmeyen sayısı artık gerçek icra friksiyonunun SEVİYESİ.
  · HÜKÜM: 2026-08-22 Rol-1 — ölçüm kodu yazıldı, İLK (betimleyici) ara-koşum yapıldı.
  · kart: `EDG-2026-042-gercek-friksiyon-tahmini.yaml`
- **EDG-2026-052** (`measuring`) — 13-A1 (tasarım: docs/TASARIM-13-INTRADAY-DOLUM-SOZLESMESI-2026-08-23.md §3-A1): dakika arşivi İCRA ZEMİNİ olarak güvenilir mi?
  · HÜKÜM: 2026-08-23 Rol-1 — İLK KOŞUM BETİMLEYİCİ (n=18<30, seans 8<10; hüküm null,
  · kart: `EDG-2026-052-e2-dakika-dogrulama.yaml`
- **EDG-2026-055** (`measuring`) — WP4 eleme bulgusu (2026-08-24): earnings takvimi kapsamı bugün 216/251 (%86,1) — 35 sembolde fail-open (kazanç-penceresi bilinmediğinde kapı…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-24): **HÜKÜM YOK — ve bu, R1 şerhi olmasaydı YANLIŞ bir kapanış olurdu.** ÖN-SAYIM: `N_giris = 10` (6 kapanmış live_paper + 4 açık pozisyon, giriş…
  · kart: `EDG-2026-055-earnings-fail-open.yaml`
- **EXE-2026-003** (`measuring`) — 4b gölge katmanı yalnız SİLAHLANMIŞ planların dakika-hassas dolumunu yazıyor (6 seansta 4 satır).
  · HÜKÜM: 2026-08-22 Rol-1 — ölçüm kodu yazıldı ve İLK koşum yapıldı; PENCERE DOLUYOR.
  · kart: `EXE-2026-003-golge-planli-kol.yaml`

### Ölçüldü (44)

- **BASE-2026-001** (`measured`) — Defterin tabanı ESKİ motorun tohum-replay'i (95 işlem, 2026-07-2x kod/veri kapılarıyla; net −5.542 USD).
  · HÜKÜM: 2026-08-01 ~19:30 — KARNE HÜKMÜ (Rol-1): CEVAP: "EVET ama ekonomik olarak anlamsız ve TEK YILA BAĞIMLI." Tam pencere (2022→2026-07, 1146 seans, bugünkü motor+canlı v3…
  · kart: `BASE-2026-001-sistem-karnesi.yaml`
- **EDG-2026-003** (`measured`) — De-risk rampası (tepe-DD %3→kıs/%8→sıfırla, kodda sabit) günlerin %92'sinde aktif ve işlem üretimini boğuyor; P3 çıkış paketi (breakeven 2.0 + hedef…
  · HÜKÜM: 2026-07-31 03:19 (6.322s, K=4): P3 PAKETİ ÖLDÜ — kill#1 (P=0,202 gevşek / 0,482 kapalı rampa; ikisi de <0,60): rampa suçlu DEĞİLMİŞ, tam serbestlikte bile paket kendini…
  · kart: `EDG-2026-003-rampa-p3.yaml`
- **EDG-2026-009** (`measured`) — Uzun-ufuk trend kolu (N=10 seçim, +13,1p/yıl vs EW-evren, t=3,69; edge SEÇİMDEN geliyor, chandelier çıkışı maliyetli; medyan tutuş 63g; 2021-26…
  · HÜKÜM: 2026-07-31 ~15:30 — HÜKÜM (Rol-1): 0) POZİTİF KONTROL BİREBİR (fazla 13.1450%, t 3.6907 — fark 0.000000; şasi geçerli).
  · kart: `EDG-2026-009-trend-kolu-rafine.yaml`
- **EDG-2026-016** (`measured`) — EDG-013 tanısı (CI'sız, K korunarak) turnover ANA etkisinin momentum-koşulundan bağımsız ve daha büyük olduğunu gösterdi (q4 @20 +0,651% tanı vs…
  · HÜKÜM: 2026-08-01 ~16:00 — SUCCESS (üç kill de tetiklenmedi; Rol-1 onaylı): üst-%20 dilim evren-fazlası @10 +0,31% CI[+0,15,+0,49], @20 +0,65% CI[+0,34,+1,01]; ARTIK üç…
  · kart: `EDG-2026-016-turnover-ana-etkisi.yaml`
- **EDG-2026-021** (`measured`) — EDG-016 (turnover ana-etkisi, YAŞAYAN) sağkalan-evrende ölçüldü ve şerhi kalıcıydı: "hayatta-kalma yanlılığı pozitif bulguda yukarı-çarpıtır, bu…
  · HÜKÜM: 2026-08-03 ~08:55 UTC — KOŞULDU (defter v3, QC FREE, DUR=None, PK GEÇTİ IC=0.0265 n=335k) HÜKÜM (Rol-1, kill#1 DALI): @20 üst-%20 evren-fazlası +0,48% CI[−0,78%,+1,85%]…
  · kart: `EDG-2026-021-qc-delist-dogrulama.yaml`
- **EDG-2026-022** (`measured`) — Sistemin kârlılık darboğazı "dar evren → az aday → az işlem → az kanıt" diye okunuyor ve WP-U'nun gerekçesi bu.
  · HÜKÜM: de-risk+tavan BİRLİKTE %65.84 (CI 58.73–72.14, tamamı >%50) BASKIN → success_metric kuralınca FINVIZ token harcaması GEREKÇESİZ.
  · kart: `EDG-2026-022-evren-baglayici-kisit.yaml`
- **EDG-2026-023** (`measured`) — EDG-2026-022 ölçtü: işlem kıtlığının baskın kökü de-risk rampası (tavan_sifir %57.5 + derisk_bagladi %8.3 = %65.8 CI>%50).
  · HÜKÜM: Taban tavan_sifir %71.3 ≠ 022-çivisi %57.5±2 — AMA şasi SAĞLAM: config/bar sha'ları birebir, iki koşum aynı-motor (sha-eşit), bütünlük temiz (frame_miss=0, dup=0).
  · kart: `EDG-2026-023-derisk-rampa-bandi.yaml`
- **EDG-2026-024** (`measured`) — Giriş eşiklerinin ikisi (hacim>=1.5x, RS>=70) aday ölümlerinin ezici kısmını üretiyor (2026-07-20 darboğaz turu; 2026-08-12 huni aynası:…
  · HÜKÜM: KILL#1 UYGULANDI: üç hücrede de eklenen-işlem ort-R CI'sı 0'ı kapsıyor (hacim_125 −0.017 [−0.218,+0.157] n=106 · rs_65 +0.094 [−0.444,+0.568] n=28 · ikisi −0.069…
  · kart: `EDG-2026-024-esik-retro-kanit.yaml`
- **EDG-2026-025** (`measured`) — momentum_burst DORMANT ve kanıtı ÇELİŞKİLİ: cf defteri +0.092R (n=1080, N4 Aşama-1 ölçümü) POZİTİF derken skill-görüş defterinin İLK KURU-KOŞUMU…
  · HÜKÜM: ÜÇÜ BİRDEN şarttı → OTOMATİK SİLAHLANMA YAPILMAZ; momentum_burst DORMANT kalır.
  · kart: `EDG-2026-025-momentum-burst-karne.yaml`
- **EDG-2026-026** (`measured`) — Operatör kararı (2026-08-12 pencere): pozisyon tavanı 5→20, pozisyon-başına risk 1.0R→0.5R (nakit matematiği: 1R'de 20 slot fiilen ~6'da tıkanır;…
  · HÜKÜM: C, B'ye HER EKSENDE baskın: işlem 410→772 (CI [+271,+455]), net P&L +775→+9.869$ (12.7×), max-dd DÜŞTÜ 0.1775→0.1235, sharpe 0.018→0.285, avg-R 0.032→0.057, win…
  · kart: `EDG-2026-026-slot20-boyut05.yaml`
- **EDG-2026-027** (`measured`) — B-varyantının (EDG-023) çıkış dağılımı kanıyor: %50 stop, %38 time/regime erken-kesim, yalnız %11 hedef; çıkış aletlerinin yarısı KAPALI…
  · HÜKÜM: 2026-08-12 Rol-1 — DÖRT hücre tamam (F1+F2) + nihai hüküm.
  · kart: `EDG-2026-027-cikis-paketi-oat.yaml`
- **EDG-2026-028** (`measured`) — Portföy ısısı tek sabit (10R tavan — operatör ön-kararı 2026-08-12 'ISI 10R kalsın') yerine piyasa koşuluna duyarlı olmalı: kancalar hazır…
  · HÜKÜM: ÖNERİLMEZ (pencereye böyle gider): T10 C@5'e karşı +110 işlem (CI [+59,+166]) AMA net P&L 9.869→1.266$ (nokta −8.603$; CI 0-içi), sharpe 0.285→0.037, işlem-R 0.057→0.026…
  · kart: `EDG-2026-028-isi-kosul-ayari.yaml`
- **EDG-2026-029** (`measured`) — EDG-027/H1 scale-out'u CI-negatif ölçtü AMA kökü MEKANİKTİ (§2-13): bankalama barında trail=entry_fill kurulunca (entry_fill>open) koşucu AYNI BARDA…
  · HÜKÜM: Scale-out DÜZELTİLMİŞ haliyle bile CI-NEGATİF: F1x(B) −0.0530R CI[−0.1033,−0.0091] · F2x(C) −0.0451R CI[−0.0839,−0.0116].
  · kart: `EDG-2026-029-scaleout-duzeltilmis.yaml`
- **EDG-2026-030** (`measured`) — Seansların %40.8'i rejim kapısıyla TÜMDEN kapalı (EDG-022: rejim_kapali — exposure_budget=0); eşik regime.min_exposure_score=40 HİÇ ölçülmedi.
  · HÜKÜM: %41 karartma KANITLA HAKLI: 30 anlamsız (boş bant), 20 zararlı-eğilimli.
  · kart: `EDG-2026-030-rejim-esigi.yaml`
- **EDG-2026-031** (`measured`) — Turnover skor-bileşeni EDG-016'yla ölçülüp (aylık +0.55% net, artık-IC 0.028) kablolandı (5dfca07) ama ağırlığı 0'da bekliyor — hermes arama uzayında…
  · HÜKÜM: İki ağırlık da benimsenMEZ: w005 ΔP&L −3.520$ (CI [−11192,+3257]), w010 −4.279$ (CI [−12060,+2437]) — CI'lar 0-içi, medyanlar negatif; sharpe her ikisinde düşüyor…
  · kart: `EDG-2026-031-turnover-agirlik.yaml`
- **EDG-2026-032** (`measured`) — Karar penceresi (2026-08-12) C-paketini @5R benimsedi + momentum_burst MANUEL silahlanma onayı verdi.
  · HÜKÜM: 3/3 GEÇTİ (donuk ölçütler, mekanik): (i) ΔP&L CI-üst +40.731 ≥ 0 ✓ · (ii) dd 0.1268 ≤ 0.16055 ✓ · (iii) sharpe 0.521 ≥ 0.20 ✓.
  · kart: `EDG-2026-032-final-paket-dogrulama.yaml`
- **EDG-2026-033** (`measured`) — §2-15a: Debi kolu bitti (9-kart dalgası); kalan kaldıraç sermaye TAHSİSİ.
  · HÜKÜM: İKİ HÜCRE DE DÜŞTÜ (başarı-koşulu ΔP&L CI-alt>0 sağlanmadı): h1 yukarı-asimetri ΔP&L −7.624$ (CI [−22.410,+7.380]), sharpe 0.285→0.053 · h2 tam-modülasyon Δ−8.897$ (CI…
  · kart: `EDG-2026-033-rejim-kosullu-boyut.yaml`
- **EDG-2026-034** (`measured`) — §2-15b: EDG-030 mekanizması slot/ısı-çalınmasını gösterdi — kabul tarama-sıralıysa kötü aday iyi adayın slotunu tüketebilir.
  · HÜKÜM: İNERT-KAPANIŞ — hipotez motorda zaten gerçeklenmiş; politika değiştirecek yüzey yok, FAZ-1 dejenere (bit-özdeşlik yapısal, Δ≡0) olduğundan KOŞULMADI (kartın ön-koşul…
  · kart: `EDG-2026-034-skor-sirali-kabul.yaml`
- **EDG-2026-035** (`measured`) — Operatör yönergesi (2026-08-12): "parametreleri aşağı/yukarı oynatıp C+mb @5R'nin en kârlı versiyonunu bulalım".
  · HÜKÜM: ALTI HÜCREDE DE CI-ÜSTÜNLÜK DÜŞTÜ (kartın tek benimseme ayağı) → C+mb @5R YEREL OPTİMUM KANITLA; değişiklik önerisi YOK, pencere kurulmaz.
  · kart: `EDG-2026-035-yerel-duyarlilik.yaml`
- **EDG-2026-036** (`measured`) — Operatör bulgusu (2026-08-13): defterdeki 95 işlem `kaynak=replay_seed` · `strategy_version=4` — yani soğuk-başlangıç tohumu ESKİ paketin (slot5 ·…
  · HÜKÜM: YENİLEME ŞU ARTEFAKTLA YAPILMAZ (kart kuralı: (b) düştü → DUR).
  · kart: `EDG-2026-036-tohum-yenileme.yaml`
- **EDG-2026-037** (`measured`) — Operatör kararı (2026-08-13): "TCA'yı ölç, sonra eşiği tartışalım".
  · HÜKÜM: C+mb'nin GÖRECELİ üstünlüğü (EDG-035: yerel optimum) etkilenmez — tüm kollar aynı friksiyon varsayımıyla ölçüldü.
  · kart: `EDG-2026-037-tca-gercek-friksiyon.yaml`
- **EDG-2026-038** (`measured`) — Operatör kararı (2026-08-13): "ölçütü konsolideye taşı ve çıkış slipajını ölç".
  · HÜKÜM: KANONİK PAYDA = D1 KONSOLİDE AÇILIŞ (feed=sip).
  · kart: `EDG-2026-038-tca-konsolide-cikis.yaml`
- **EDG-2026-039** (`measured`) — Operatör kararı (2026-08-13): "önce kart, sonra karar".
  · HÜKÜM: **SİLAHSIZLANMA ÖNERİLİR — ama gerekçe "çıkarmak kazandırıyor" DEĞİL, KANIT ASİMETRİSİ:** (i) pullback'in ZARARI üç bağımsız kaynakta tutarlı — replay n=6 ort-R −0,787…
  · kart: `EDG-2026-039-pullback-silahsizlanma.yaml`
- **EDG-2026-040** (`measured`) — EDG-037/038 replay motorunun `slippage_bps=5` varsayımını İLK KEZ ölçtü ve iyimser buldu (kanonik ölçütle giriş bacağında medyan +29,0 bps; n=4, CI…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-22): **Ö1 DÜŞTÜ — BENİMSENEN PAKET ÖLÇÜLEN FRİKSİYON MERTEBESİNDE NEGATİF.** Kartın kendi cümlesiyle: bu bir bulgudur, gizlenmez, ROADMAP'e ACİL…
  · kart: `EDG-2026-040-friksiyon-dayaniklilik.yaml`
- **EDG-2026-041** (`measured`) — ROADMAP WP3-A/28a (denetim D2: EN ÜST öncelik): `hermes_bg_proposal_rejected` — arka plan turunda üretilen **47 öneri deftere HİÇ girmedi**; aynı…
  · HÜKÜM: **D3 ELENDİ, D1 + D2 TETİKLENDİ.** D3'ün şartı ("çoğunda `certified is None`") ölçümle ÇÜRÜDÜ: sertifika 47/47'de biliniyordu — yani korkuluk körlükten değil,…
  · kart: `EDG-2026-041-gorunmez-suzgec.yaml`
- **EDG-2026-043** (`measured`) — B4 operatör kararı (2026-08-22): E1 limit bacağı KAPALI KALIR — gerekçe artık E1'in çürüyen hükmü değil, ÖLÇÜM: kapıyı açmak slip=5 modelinde dört…
  · HÜKÜM: ÖLÇÜM TAMAM, HÜKÜM ASKIDA (Rol-1, 2026-08-22).
  · kart: `EDG-2026-043-friksiyon-kosullu-limit.yaml`
- **EDG-2026-044** (`measured`) — Prefill havuzunun cpu−2 tavanı bir tasarım tercihi değil, 2026-08-03 vakasının YAMASIDIR: iki işçi iki saat %99,9 CPU'da koşup panoyu 8,8-10,4 sn'ye…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **AŞAMA-1 EŞİĞİ KARŞILANMADI — KART KAPANIR, TAVAN KALIR (donuk kural).** Sabit 6-sondalık arama iş yükünde 2-işçi (bugünkü cpu−2) ort 2676,74…
  · kart: `EDG-2026-044-havuz-tavani.yaml`
- **EDG-2026-045** (`measured`) — Replay'in bar-içi stop dolumu TAM eff_stop seviyesinde gerçekleşmiş sayılır (broker.py _touch_exit kademe-2; kademe-1 stop_gap açılışta GERÇEK fiyat…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **Ö1 KURALI ATEŞLEDİ — sıfır-stop-slip varsayımı P&L'i ANLAMLI ŞİŞİRİYOR.** Taban edg032c (+23.806) → stop-slip 5/10/20 bps: +20.721 / +18.109…
  · kart: `EDG-2026-045-stop-slip.yaml`
- **EDG-2026-046** (`measured`) — EDG-040 ACİL kaleminin (b) bacağı. Keşif (2026-08-22, n=13 betimleyici) iki şey gösterdi: |friksiyon| TAHMİN EDİLEBİLİR (menzil% Spearman +0,90 ·…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **MEKANİZMA KANITSIZ — KART KAPANIR (donuk kural, iki-dünya şartı).** Koşul 1 SAĞLANMADI: Δ(cezalı−mevcut | ATR-dünyası) = +11.490,31 ama CI95…
  · kart: `EDG-2026-046-friksiyon-bilincli-secilim.yaml`
- **EDG-2026-047** (`measured`) — WP1-B 23e: "açılış-sonrası 15 dk beklemek friksiyon riskini düşürür" iddiası bugüne dek tek ölçümden geliyor (n=401 sembol-seans, konsolide 15-dk…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **Ö1 ATEŞLEDİ — yakın-pencere daralması BİZİM VERİDE DE ANLAMLI.** Δ%menzil nokta −%42,29, seans-kümeli CI95 [−%44,31, −%40,09]; CI-üst < −%20…
  · kart: `EDG-2026-047-yakin-pencere.yaml`
- **EDG-2026-048** (`measured`) — B-CHOP-BUTCE operatör kararı (2026-08-23): chop kapanması "kazara-aritmetik" sayıldı, yeniden açılma KANIT-KAPILI.
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **NO-GO — ÖLÇÜLMÜŞ RET, KALEM KAPANIR.** Δ(taban60−taban45) = −18.265,65$, CI95 [−47.733,81, +10.589,40] → CI 0-içi (GO şartı CI-alt>0…
  · kart: `EDG-2026-048-chop-tabani.yaml`
- **EDG-2026-049** (`measured`) — K6 operatör kararı (2026-08-23 brainstorm 6/7): uyuyan-kurulum yolu önden bağlı arkadan bağsız — 31 plan / 0 icra (1'i GO).
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-24): **NO-GO, İKİ KAT GEREKÇEYLE — yol "TEŞHİS-KATMANI" damgasıyla kapanır.** (1) Δ(dormant_acik−kontrol) = −3.121,44$, CI95 [−10.780,65,…
  · kart: `EDG-2026-049-uyuyan-kurulum-karsi-olgu.yaml`
- **EDG-2026-050** (`measured`) — 15d-A1 (ARSENAL çıtasına bağlı ilk faktör kartı; taslak docs/TASARIM-15D-PIT-FAKTOR-SETI- 2026-08-23.md K1'den AYNEN): 8-K Item-2.02 duyuru-tepkisine…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-24): **KURAL ATEŞLEDİ — "PEAD SİNYALİ VAR, ARSENAL ADAYI" — AMA ÜÇ ZORUNLU ŞERHLE VE SAĞLAMLIK-TEKRARI ÖN-ŞARTIYLA.** Ölçüm: üst dilim @60g…
  · kart: `EDG-2026-050-pead-8k.yaml`
- **EDG-2026-051** (`measured`) — 28g teşhisinin bıraktığı boşluk: incumbent'ın holdout bozulması GERÇEK, kayıp GENELE YAYILI (4/4 setup, 3/3 ay) ve SPY yükselirken oluştu —…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **BREADTH AYIRMIYOR — hipotez ARŞİVE (donuk kural: CI 0-içi).** ΔortR(dar−genis) = −0,158, CI95 [−0,652, +0,335].
  · kart: `EDG-2026-051-genislik-dilimi.yaml`
- **EDG-2026-057** (`measured`) — `/api/topviews` (2026-08-24) toplulaştırması, planların kapı-reddi kırılımını İLK KEZ tek paydadan gösterdi.
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-24): **GÖZLEM ÇÜRÜTÜLDÜ.
  · kart: `EDG-2026-057-leading-sector-kapisi.yaml`
- **EDG-2026-062** (`measured`) — 
  · HÜKÜM: 2026-08-31 hüküm: verdict_2026_08_31 bloğu
  · kart: `EDG-2026-062-pit-arsiv-baglamasi.yaml`
- **EXE-2026-001** (`measured`) — İç defter (koşulsuz ertesi-açılış dolumu) ile canlı ayna (buy-stop GTC bracket) FARKLI icra modelleri koşuyor ve ayna gap durumunda reddediliyor…
  · HÜKÜM: 2026-08-03 ~15:0x UTC — E1 GRİD KOŞULDU (kanıt: research/olcumler/e1_grid_2026-08-03/; determinizm çift-kapılı)
  · kart: `EXE-2026-001-entry-execution.yaml`
- **EXE-2026-002** (`measured`) — Faz-6 kilit zincirinin ③ numaralı kilidi (`health.faz5_cikisi`) bugün SABİT `False` / `olculemedi` yazılı ve gerekçesi kendi kodunda duruyor: "Faz-5…
  · HÜKÜM: 2026-08-07 Rol-1 — ÖLÇÜM KODU YAZILDI VE KOŞTU (v212, meridian/faz5_cikis.py).
  · kart: `EXE-2026-002-faz5-cikis-olcumu.yaml`
- **EXE-2026-004** (`measured_partial`) — Karşı-olgusal defter (cf) çıkışı BİLEREK statiktir — sert stop / hedef / zaman stopu; trail, scale-out, rejim-dönüşü, giveback, erken-itlaf çıkışları…
  · HÜKÜM: 2026-08-09 Rol-1 — AŞAMA 1 ÖLÇÜLDÜ; Aşama-2 eşiğine ULAŞILMADI (eşikler ölçümden ÖNCE donmuştu, DEĞİŞMEDİ).
  · kart: `EXE-2026-004-cf-cikis-sadakati.yaml`
- **EXE-2026-005** (`measured`) — ROADMAP WP1-B/23c (denetim D5: "kapanmadan HİÇBİR limit-tavanı kararı verilemez").
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-22): kartın sorusu GEÇERLİ ama CANLI YASADA CEVAPLANAMAZ — B kolu örneklemi YAPISAL olarak boş (limit = trigger·1,04 = max_chase tavanıyla birebir;…
  · kart: `EXE-2026-005-dinlenen-limit.yaml`
- **EXE-2026-006** (`measured`) — `EXE-2026-001-R2`nin E1 grid hükmü — **"limit bacağı MONOTON ZARARLI · kaçanlar sistematik KAZANAN"** (2026-08-03) — replay'in kaçan-işlem maliyetini…
  · HÜKÜM: Kartın ölçümden ÖNCE yazdığı kural: *"H1 ve H2'nin İKİSİ de ayakta kalırsa E1 DOĞRULANIR; biri düşerse hüküm YENİDEN AÇILIR."* **H1 DÜŞTÜ · H2 ÖLÇÜLEMEDİ** (yani "ayakta…
  · kart: `EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml`
- **EXE-2026-007** (`measured`) — `trades.jsonl`in `kaynak: live_paper` damgası bir BROKER TEYİDİ DEĞİL, bir KOD YOLU beyanıdır: `loop._persist_trade`ten geçen her satır o damgayı…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-22): ölçüm ajanı ön-ölçümü BİREBİR yeniden üretti (research/olcumler/exe007_broker_teyit_2026-08-22/ — canlı defter A1'den salt-okunur çekildi,…
  · kart: `EXE-2026-007-broker-teyitli-defter.yaml`
- **EXE-2026-008** (`measured`) — B-E1-LIMIT operatör kararı (2026-08-23 brainstorm 3/7): E1 hükmü EXE-006'yla yeniden açık ama düşük-güçlü kaldı (H1 kırık, H2 ölçülemedi, Ö3 CI'ları…
  · HÜKÜM: HÜKÜM (Rol-1, 2026-08-23): **ÜÇÜNCÜ DAL — "İKİ DÜNYADA DA BELİRSİZ"; kalem EDG-2026-042 gerçek-bandına PARK, bacak KAPALI kalır.** H1 DÜŞTÜ: dinlenen kolda eğri monoton…
  · kart: `EXE-2026-008-limit-bacagi-yeni-dunya.yaml`
- **KYS-2026-002** (`measured_partial`) — DSR/PBO sert kapısı (validation.py, 2026-07-30 operatör-onaylı MOD-FARKINDALIKLI tasarım) 2026-08-09'a kadar canlıda fiilen İŞSİZDİ: pencere_id…
  · HÜKÜM: R1 penceresi PBO = 0.6286 (motorun kendi pbo_cscv'si; n_aday=179, n_gozlem=207, 8 blok, 70 kombinasyon, ort_oos_sira=0.4018; deterministik — iki koşum aynı md5;…
  · kart: `KYS-2026-002-pbo-dsr-r1-taban.yaml`

### Arşiv (15)

- **EDG-2026-001** (`archived`) — Fiyatın 52-hafta zirvesine yakınlığı, çapa (anchoring) yanlılığı nedeniyle ileri getiriyi öngörür; yatırımcılar zirveye yakın iyi habere eksik tepki…
  · HÜKÜM: 2026-07-31: 9/9 hücre anlamsız (tarih-kümeli bootstrap; en iyi cf@20 IC=0.037 CI[-0.030,+0.100]); panel tanısı aralık-kısıtı artefaktını dışladı (işaret tez yönünde bile…
  · kart: `EDG-2026-001-52wh-proximity.yaml`
- **EDG-2026-002** (`archived`) — Olağandışı hacim şoku görünürlüğü artırır ve sonraki haftalarda pozitif getiriyle ilişkilidir (Gervais-Kaniel-Mingelgrin).
  · HÜKÜM: 2026-07-31: bant yapısı hayalet-artefaktı DEĞİL (A/B max 0.047pp) AMA 18 hücrenin 0'ı ham rvol20'yi geçemedi (ham @20 IC=0.0645 CI[+0.017,+0.111] ANLAMLI) → canlı…
  · kart: `EDG-2026-002-volume-shock.yaml`
- **EDG-2026-004** (`archived`) — Son 21 günde aşırı yüksek maksimum günlük getiri (MAX) taşıyan "piyango" hisseleri sonraki dönemde underperform eder (Bali-Cakici-Whitelaw);…
  · HÜKÜM: 2026-07-31: iki kill de tetiklendi — yön TERS (yüksek-MAX @20 +1,46pp DAHA İYİ, CI[+0,66,+2,27]); eleme beklentiyi DÜŞÜRÜR (−0,34pp anlamlı; elenen dilim…
  · kart: `EDG-2026-004-max-filter.yaml`
- **EDG-2026-005** (`archived`) — SPY 200-günlük SMA altındayken yeni kırılma girişlerini kapatmak drawdown/vol azaltır (Faber ailesi; alfa değil risk aracı).
  · HÜKÜM: 2026-07-31 tanı turu (ilk "KAPI_ACILABILIR" hükmü DÜŞTÜ — mekanizma kanıtıyla): 1) ÖLÇÜM HÜKMÜ: R1-OOS kıyası HUKUMSUZ_OLCUM_TASARIMI — karşı-olgu kolları…
  · kart: `EDG-2026-005-sma-gate.yaml`
- **EDG-2026-006** (`archived`) — Getiriler ay dönümünde yoğunlaşır (son işlem günü + ilk 3 gün; likidite/maaş-akışı/kurumsal rebalans mekaniği).
  · HÜKÜM: 2026-07-31 06:48: kill#2 ÖN-ADIMDA tetiklendi (ikiz koşum HİÇ AÇILMADI — K tasarrufu): ToM-içi/dışı EW evren getiri farkı R1_OOS'ta −11,79 bps/gün (YÖN NEGATİF; SPY…
  · kart: `EDG-2026-006-turn-of-month.yaml`
- **EDG-2026-007** (`archived`) — 12-1 ay momentumun FF3 (piyasa/boyut/değer) yüklerinden arındırılmış artığı ("residual momentum") ham momentuma benzer prim taşır ama faktör-kaynaklı…
  · HÜKÜM: 2026-07-31 ~07:30: İKİ KILL DE TETİKLENDİ.
  · kart: `EDG-2026-007-residual-momentum.yaml`
- **EDG-2026-008** (`archived`) — Vol-yönetimli maruziyet: piyasa gerçekleşen volatilitesi yüksekken yeni-giriş boyutunu kısmak, düşükken tavana bırakmak, momentum-tipi stratejilerde…
  · HÜKÜM: 2026-07-31 ~14:00: kill#3 — iki pencerede de yönsüz/CI-0-içi (P(vol düştü) p21=0.06 TERS / p63=0.70 eşik-altı; PARA CI'ları 0-içi; Sharpe farkları 0-içi).
  · kart: `EDG-2026-008-vol-scaling-overlay.yaml`
- **EDG-2026-010** (`archived`) — Mevcut kırılma ailesi GÜÇTE giriyor (breakout/momentum-burst).
  · HÜKÜM: 2026-08-01 ~09:15 — HÜKÜM (Rol-1, ölçüt-kusuru itiraflı): LAFZEN "SUCCESS" (ham @10/@20 CI-0-dışı pozitif + Jaccard 0.019-0.024 << 0.3), KANITEN KENARSIZ: ham pozitiflik…
  · kart: `EDG-2026-010-pullback-setup.yaml`
- **EDG-2026-012** (`archived`) — Net hisse İHRAÇ edenler sonraki dönemde düşük, GERİ-ALANLAR yüksek getiri verir (yönetimin zamanlama bilgisi).
  · HÜKÜM: 2026-08-01 ~13:45 — kill#2: YÖN LİTERATÜRÜN TERSİ VE ANLAMLI (MAX deseni): ihraç dilimi fazlası @20 +0,35% CI[+0,10,+0,57], @60 +1,04% CI[+0,33,+1,67]; geri-alım…
  · kart: `EDG-2026-012-net-issuance.yaml`
- **EDG-2026-013** (`archived`) — Kısa-dönem momentum (1 ay) yüksek-TURNOVER hisselerde güçlenir/kalıcılaşır.
  · HÜKÜM: 2026-08-01 ~16:00 GÜNCEL HÜKÜM — EDG-016 kaderi belirledi: ETKİLEŞİM-TEZİ DÜŞTÜ, sinyal TURNOVER ana-etkisi olarak EDG-016'da yaşıyor (momentum koşulu etkiyi yarıya…
  · kart: `EDG-2026-013-mom-turnover.yaml`
- **EDG-2026-014** (`archived`) — Brüt kârlılık (GP/Assets) yüksek şirketler ileri dönemde daha iyi getiri verir (Novy-Marx 2013 "the other side of value").
  · HÜKÜM: 2026-08-01 ~13:45 — kill#1: BİLGİSİZ. Üst/alt dilimler ve yayılım @20+@60 hepsi CI-0-içi; beşli dilim monoton değil; finans-dışı tanı dilimi (165 sembol) aynı.
  · kart: `EDG-2026-014-gross-profitability.yaml`
- **EDG-2026-015** (`archived`) — VCP/kırılma bileşik skorunun bileşen-aileleri TEK TEK arşivlendi (residmom≈rawmom EDG-007, 52wh EDG-001, volshock EDG-002; ham rvol20 tek anlamlı iz).
  · HÜKÜM: 2026-08-01 ~14:30 — kill#1: ÇATI DA BİLGİSİZ; WP-K açık-hipotez listesi KAPANDI.
  · kart: `EDG-2026-015-vcp-decompose.yaml`
- **EDG-2026-017** (`archived`) — EDG-002 (volshock) hükmü bant-tablosunu arşivledi AMA yan gözlem bıraktı: ham rvol>=2.5 bölgesi @20 +1,61% anlamlı-pozitifti ve ÜÇGEN-FORM şartı bu…
  · HÜKÜM: 2026-08-02 ~21:05 TR — ARŞİV (Rol-1 hükmü; ÜÇ kill de tetiklendi): kill#1: bölge fazlası @20 +0,050% CI[−0,200,+0,279] — CI-0-İÇİ (bilgisiz).
  · kart: `EDG-2026-017-rvol-form-revizyonu.yaml`
- **EDG-2026-020** (`archived`) — Kazançı GERÇEKLEŞMİŞ (0 <= t−e <= P; e = olay günü, kamusal geçmiş olgu — PIT-güvenli) sembollerde rvol-koşullu önceliklendirme, aday havuzunun geri…
  · HÜKÜM: 2026-08-03 ~00:55 TR — ARŞİV (Rol-1 hükmü; kill#1 TAM + kill#3 TAM): @20 havuz-fazlası P3 −0,62% [−1,30,+0,51] · P5 −0,73% [−1,23,+0,30] — ikisi de CI-0-içi,…
  · kart: `EDG-2026-020-postevent-inplay.yaml`
- **KYS-2026-001** (`archived`) — EAP ölçümünün yan bulgusu (2026-07-31): herhangi bir olay penceresinde evrenin ort.
  · HÜKÜM: 2026-08-02 ~22:30 TR — ARŞİV (Rol-1 hükmü; kill#1 tetiklendi): İki yüzeyde de fark CI-0-içi VE |fark|<10bps: Y1 @20 −0,06bps [−2,06,+2,60] · Y2 @20 +0,27bps…
  · kart: `KYS-2026-001-kiyas-kirlenmesi.yaml`

### Diğer — kova tanımı yok (YASA 4: adıyla listelenir) (5)

- **EDG-2026-011** (`askida`) — Aynı gün üretilen adaylar arasında "in-play" olanlar (kazanç-katalizörü yakınlığı + yüksek rvol) diğer adaylardan daha iyi ileri getiri/isabet taşır…
  · HÜKÜM: 2026-08-01 ~10:40 — kill#3 ASKI (K HARCANMADI): in-play aday-gün ÜST SINIRI bile 11-12 << 150.
  · kart: `EDG-2026-011-inplay-onceliklendirme.yaml`
- **EDG-2026-018** (`askiya_veri_kapisi`) — İki yaşayan sinyalin (turnover EDG-016 · trend EDG-009) canlı hükmü S&P500 large-cap evreninde ölçüldü.
  · HÜKÜM: 2026-08-02 ~19:30 TR — ADIM-0 DÜŞTÜ (Rol-1 hükmü): (1) KOHORT KURULAMADI: sp500_uyelik_tarihi.csv salt-S&P500 (date,tickers; büyüklük alanı yok; günlük üye 487-507) —…
  · kart: `EDG-2026-018-pit-midcap-ust-sinir.yaml`
- **EDG-2026-060** (`judged`) — OPERATÖR SORUSU (2026-08-25): "sistem son seed'den beri çok gelişti, yeniden bütün planları değerlendirmek gerekmez mi?" ÖLÇÜLDÜ ve soru haklı çıktı:…
  · kart: `EDG-2026-060-cf-tarih-yeniden-yurutme.yaml`
- **EDG-2026-061** (`judged`) — OPERATÖR SORUSU (2026-08-25): "OOS kapısının neden bu kadar az aday geçirdiği hâlâ oturmadı, bunu çözelim." Bir önceki tur şunu KANITLADI ve bu kart…
  · kart: `EDG-2026-061-oos-kapisi-neden-az-geciriyor.yaml`
- **EDG-2026-066** (``) — 
  · kart: `EDG-2026-066-tick-arsiv-pilot.yaml`

<!-- ENDEKS: SON -->

## Retroaktif kayıt kuyruğu (S1 ajanı biçimlendirecek; ölçümler ÖNCE koşmuştu, K-defterine sayılı)
- EAP large-cap [-10,-1] — status: **archived** (2026-07-31: +9,0bps CI[−13,3·+31,9], eşik 30bps;
  12,6-yıl güç-yeterli genişletmede +6,8bps; PK-1 kesin geçti; eşik esnetilmedi)
- Insider CMP (EDGAR 62 çeyrek, opportunistic_frac dahil) — status: **archived** (pozitif-kontrollü 0)
- Short-interest (FINRA 24 ay) — status: **archived** (12 hücre 0; likidite-vekili otopsisi)
- Çıkış paketi P1/P2/P3 (K=3) — status: measured→shadow-accrual (kapı ret; imza doğrulandı)
- Uzun-ufuk mega-cap trend kolu (K=2) — status: **measured→ALIVE/refine** (2026-07-31: N=10
  +13,14p/yıl vs EŞİT-AĞIRLIK-evren [yanlılık-nötr çıta], t=3,69 Bonferroni-geçer; maxDD çıtası
  GEÇİLMEDİ; mekanizma düzeltmesi: medyan tutuş 63g [~3 ay, "yıllar" değil], edge SEÇİMDEN
  [chandelier kapatınca CAGR ARTIYOR — durak maliyet], 2021-26 sessiz. Sonraki ölçüm BULGU-1/2
  veri-onarımı SONRASI; tasarım: seçim-odaklı, ~3 ay tutuş, durak minimal)
- PEAD klasik / rekonstitüsyon / sektör-takvim — status: archived (kaynaklı; kill-list)

## Kart-adayı yeni bulgular (Rol 1 tasarımı bekliyor)
- **KIYAS KİRLENMESİ (EAP ölçümünün yan bulgusu, 2026-07-31):** herhangi bir olay penceresinde
  evrenin ort. %64'ü / medyan %74'ü KENDİ kazanç-öncesi penceresinde — "evren medyanına göre fazla
  getiri" kullanan TÜM ölçümler (component_ic, cf R-tabloları) sistematik sıkıştırılmış. Doğru
  kıyas tasarımı (olay-penceresi-dışı alt-küme) kendi ön-kaydını hak ediyor; düzeltilmiş EAP
  okuması bile (+21,1bps) eşiğin altında — EAP hükmünü değiştirmez, ölçüm-altyapısını iyileştirir.

## Numara notu
- EDG-2026-019: 2026-08-03'te "kasıtsız boşluk, numara emekli" ilan edilmişti; **2026-08-13'te BİLİNÇLİ yeniden kullanıldı** (`EDG-2026-019-skill-gorus-defteri` — numara grep'lenip boş doğrulanarak; tarihçe `test_kart_kimlik_v219` docstring'inde). Emeklilik notu o gün GÜNCELLENMEMİŞTİ — çelişki 2026-08-22'de yakalandı (Ö-49 bayat-beyan sınıfı) ve BU satırla kapatıldı: kart kimliği kalır (yeniden adlandırmak 151-atıf sınıfı kırılma yaratırdı), bayat olan emeklilik beyanıydı.
