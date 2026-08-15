"""integrity_registry.py — bileşen × değişmez-desen kapsam kaydı: "nereye bakmadık?" tablosu.

Sessiz hatalar bileşen değişse de DESEN olarak tekrar eder ve hepsi mevcut testlerden geçer;
çözüm her modüle özel test icat etmek değil, modülleri altı değişmez-deseniyle çaprazlamaktır
(`PATTERNS`):
  ÜRETKENLİK  — çıktı üretiyor mu?                    (kanıt defteri ömrü boyunca boş kalabilir)
  KORUNUM     — giren, kayıtlı terminale ulaşıyor mu? (silahlı plan kayıtsız buharlaşabilir)
  DETERMİNİZM — aynı girdi aynı sonucu mu veriyor?    (işçiler barları yeniden yazabilir)
  TUTARLILIK  — türev, kaynağından taze mi?           (tüketici binlerce satırı görmeyebilir)
  MONOTONLUK  — ileri-only nicelik geri gidiyor mu?   (kitap geriye sarabilir)
  SAHİPLİK    — yazan, sahibi olmadığı alanı eziyor mu? (nabız ezilmesi sınıfı)
Amaç bilinmeyen yüzeyi SONLU ve GÖRÜNÜR kılmak: "nereye bakmadık?" sorusunun cevabı tahmin değil,
bir tablodur.

GİRİŞLER: `COVERED` (bileşen → GERÇEK bir kontrol/test altındaki desenler; hücre gerekçeleri satır
içi yorumlarda), `APPLICABLE` (desenin o bileşen için SORULABİLİR olduğu hücreler — ham payda
yanıltıcıdır, gerçek kapsam = dolu/uygulanabilir), `gaps` (uygulanabilir ama boş hücreler:
denetimin gerçek kuyruğu), `coverage_report` (iki paydalı kapsam tablosu; pano tüketir),
`next_audit_target` (dönüşümlü denetim: en uzun süredir denetlenmemiş bileşen önce),
`record_audit` (denetim tarihini damgalar — "denetledim sanıyordum" hatasını engeller).

DÜRÜSTLÜK KURALLARI: bir hücre ancak GERÇEK bir kontrol/test varsa 'covered' işaretlenir — iyi
niyet saymaz; şüphe varsa desen UYGULANABİLİR sayılır (muhafazakâr). Okur/yazar: yalnız
integrity_audit_log.json (bileşen → son denetim tarihi); kapsam matrisi kodda güncellenir."""
from __future__ import annotations

from . import store

PATTERNS = ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"]

# Bileşen → o bileşen için OTOMATİK kontrol altında olan desenler (canlı dedektör ya da test).
# Boş liste = HİÇ denetlenmemiş (dürüst başlangıç; dönüşümlü denetim bunları doldurur).
COVERED: dict[str, list[str]] = {
    # --- otomatik dedektörlerin fiilen kapsadıkları ---
    # boşluk turu 5: cf SIFIR YETKİ (submit/commit/dump_yaml/heartbeat çağrısı yok) ve yalnız kendi
    # iki dosyasını yazar; çözümleme aynı girdide aynı satırları verir.
    "counterfactual":   ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- boşluk kapatma turu 2 (2026-07-21): loop ---
    # Motorun kalbi. korunum+monotonluk zaten vardı (geriye-seans bekçisi + plan korunumu); kalan 4:
    # bir döngü GERÇEKTEN artefakt üretir (regime/data_quality/portfolio/nabız); aynı gün iki kez
    # işlenince defter ÇOĞALMAZ (audit #11 regresyon kilidi); regime.json İŞLENEN günün tarihini
    # taşır; döngü goal/bounds/strategy/secrets'a ASLA yazmaz + yazdığı dosyalar beyan listesiyle
    # sınırlı. Testler: test_loop_gaps_v48.py (9).
    "loop":             ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # boşluk turu 5: sabit defterde kalibrasyonlar tekrarlanabilir; analytics ölçer, KARAR VERMEZ
    # (commit/dump_yaml çağrısı yok) ve yalnız kendi kalibrasyon dosyalarını yazar.
    "analytics":        ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- dönüşümlü denetim turu 2 (2026-07-21): adapters.data ---
    # D1 kaynak-ölçeği dikişi (pin + geçmiş-değişti → rev bump) → determinizm+tutarlilik;
    # D3 satır-kaybı reddi → monotonluk; D4 atomik yazım + D5 evren-küçülme kaydı → korunum;
    # D2 kaynak sağlığı (FMP 429 artık görünür) → uretkenlik; kaynak sabitlemesi → sahiplik.
    # Testler: test_data_audit_v17.py (12).
    "adapters.data":    ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- boşluk kapatma turu 1 (2026-07-21): reflect ---
    # Ship YETKİSİ. determinizm zaten vardı (havuz işçisi load_cached); kalan 5 desen kapatıldı:
    # her DEĞERLENDİRİLEN öneri bir hipotez satırı üretir ve kayıtlı bir terminale ulaşır (guard/
    # kapı/teyit/ship/öğrenme-durdu/kilit); wf önbelleği bar revizyonuna bağlı; ship sürümü İLERİ
    # taşır ve red canlıya dokunmaz; versioning.commit'i çağıran TEK yer burası + süreçler-arası
    # kilit. Testler: test_reflect_gaps_v47.py (10).
    "reflect":          ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # boşluk turu 5: pencereler sabit+sıralı ve env'den ayarlanamaz; fetch_end HER çağrıda bugün
    # (audit #41 donmuş sabit hatası); load_cached ağ/tazeleme yollarına hiç dokunmaz.
    "dataset":          ["uretkenlik", "determinizm", "tutarlilik", "sahiplik"],
    # --- boşluk kapatma turu 3 (2026-07-21) ---
    # health: nabız ÜRETİLİR + zorunlu alanları taşır; yaş dürüst ölçülür (bozuk/eksik damga = BAYAT,
    # taze değil); zaman ileri gider; halt/learn-halt ayrı kapılar ve nabızla tutarlı.
    "health":           ["uretkenlik", "tutarlilik", "monotonluk", "sahiplik"],
    # scheduler: nabız damgası + işlenen son seans kaydı (tekrar/atlama görünür), ileri-only ilerleme.
    "scheduler":        ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # boşluk turu 5: yetersiz örneklemde SESSİZ kalmaz (skip olayı + w=None + predict_proba None,
    # uydurma p_win yok); aynı veriden aynı katsayılar (saf-numpy GD).
    "shadow_model":     ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # boşluk turu 5: rapor HER çağrıda üretilir ve diske düşer; sabit durumda birebir tekrarlanır.
    "selfreview":       ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # versioning: her commit bir SNAPSHOT üretir (geri alma onsuz çalışmaz — turu 25'te ısırdı);
    # sürüm numarası geri alma sonrası bile ASLA yeniden kullanılmaz; karne satırları birleşir, ezilmez.
    "versioning":       ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    "watchdog": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # boşluk turu 4: SIFIR YETKİ statik olarak kanıtlandı (yalnız cf defterine yazar; commit/
    # dump_yaml/heartbeat/submit çağrısı YOK), ağa çıkmaz (önbellek CSV), rastgelelik kullanmaz.
    "cf_backfill":      ["uretkenlik", "korunum", "determinizm", "sahiplik"],
    # --- dönüşümlü denetim turu 1 (2026-07-21): adapters.alpaca ---
    # A1 taşıma kaydı (yutulan hata görünür) → korunum+üretkenlik; A2 coid birleştirme anahtarı +
    # broker_reconcile tazeliği → tutarlılık; A3 önek süzgeci + close_all onay jetonu → sahiplik;
    # A4 sınırda stop-gevşetme reddi → monotonluk. Testler: test_alpaca_audit_v16.py (14).
    # DETERMİNİZM: aynı plan → aynı emir gövdesi testi var (test_determinism_same_plan_same_body),
    # ama gerçek broker yanıtı deterministik DEĞİL (fill fiyatı) — bu hücreyi dürüstlük gereği
    # 'covered' saymıyorum: kontrol yalnız BİZİM gönderdiğimiz tarafı bağlıyor.
    "adapters.alpaca": ["determinizm", "korunum", "monotonluk", "sahiplik", "tutarlilik", "uretkenlik"],
    # --- dönüşümlü denetim turu 3 (2026-07-21): adapters.constituents ---
    # ÜRETKENLİK: modülün HİÇ tüketicisi yoktu (üç denetimlik düzeltme ölü kodda) → artık P5'te
    # universe_drift() çağrılıyor + health() watchdog'a bağlı. TUTARLILIK: makullük kapısı +
    # gelecek-tarih reddi (üretim önbelleği test fixture'ıydı: 3 sembol, as_of 2099).
    # Diğer dört desen DÜRÜSTÇE boş: burada monoton nicelik yok, sahiplik/korunum/determinizm için
    # gerçek bir kontrol yazmadım — "baktım, iyi görünüyor" kapsam sayılmaz.
    # Testler: test_constituents_audit_v18.py (13).
    "adapters.constituents": ["determinizm", "sahiplik", "tutarlilik", "uretkenlik"],
    # --- HENÜZ DENETLENMEMİŞ (dönüşümlü denetimin kuyruğu) ---
    # --- tur 4 (2026-07-21): adapters.fmp ---
    # F1 strict mod + kısmi-hata koruması (yarım kazanç takvimi guard'ı FAIL-OPEN yapıyordu) →
    # korunum; F2 günlük kota muhasebesi + 429 soğuması → uretkenlik; F3 anahtar maskesi ve
    # "anahtar tek yerde okunur" testi → sahiplik. Testler: test_fmp_audit_v19.py (7).
    "adapters.fmp": ["uretkenlik", "korunum", "sahiplik"],
    # --- tur 5 (2026-07-21): adapters.macro + adapters.news ---
    # macro: DONMUŞ son tarih ("2026-07-10") → her çağrıda bugün + test (tutarlilik); "tüketicisi yok"
    # artık status()'ta yazılı (uretkenlik'in dürüst cevabı, gerçek bir kontrolle: status testi).
    # news: 'anahtar var' ≠ 'çalışıyor' → status() kaynak sağlığını taşır (uretkenlik); 20 sembol
    # üstü SESSİZ kırpma → kayıt (korunum). Testler: test_macro_news_audit_v20.py (7).
    "adapters.macro": ["determinizm", "tutarlilik", "uretkenlik"],
    "adapters.news": ["uretkenlik", "korunum", "determinizm"],
    # --- tur 6 (2026-07-21): api ---
    # P1 "her mutasyon ucu yetki ister" bugün doğruydu ama ZORLANMIYORDU → statik kural testi
    # (19/19 authed, yeni yetkisiz POST eklenirse test kırılır) + yetkisiz GET izin listesi;
    # P2 /metrics yetkisiz olarak öz sermaye/P&L/harcama yayınlıyordu, /halt tünelden açıldığı için
    # bu dışarı bakan bir yüzey → uzak+yetkisiz istekte yalnız canlılık. Testler: test_api_audit_v21 (8).
    "api": ["uretkenlik", "korunum", "tutarlilik", "sahiplik"],
    # --- tur 7 (2026-07-21): arming ---
    # R1 modülün MERKEZİ iddiası ("yalnız ölçer, silahlandırmaz") yazılıydı ama zorlanmıyordu →
    # kaynak + davranış testi (sahiplik). R2 CANLIDA: "ölçülemedi" (candidate OOS undefined)
    # "gate_rejected" diye kaydediliyordu — kurulumu haksızca gömen sahte kanıt; artık
    # gate_undefined ayrı bir terminal (korunum). Testler: test_arming_audit_v22.py (6).
    # boşluk turu 4: rapor HER koşuda diske düşer, aynı kanıtla aynı ölçüm, cf defterinden türer.
    "arming": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- tur 8 (2026-07-21): backtest (KAPININ KENDİSİ) ---
    # B1 ileri-dönük sızıntı: docstring'de anlatılıyor, kanıtlanmıyordu → "geleceği kes, geçmiş
    # değişmesin" testi (determinizm); B2 replay + walk_forward tekrarlanabilirliği + girdiye
    # duyarlılık ikizi; B3 SECTORS evreni tam kapsıyor mu + canlıyla AYNI harita mı (tutarlilik).
    # Testler: test_backtest_audit_v23.py (8).
    # boşluk turu 5: replay tam kanıt paketi üretir (işlemler + plan/aday defteri + öz sermaye
    # eğrisi) ve DEĞERLENDİRİLEN her plan bir karar taşır (sessizce düşen plan yok).
    "backtest": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- tur 10 (2026-07-21): config ---
    # G1 boş/bozuk strategy.yaml {} döndürüyordu (motor params={} ile koşabilirdi) → varsayılana
    # düşer + kayıt (korunum); G2 goal/bounds lru_cache uzun ömürlü süreçte DONUYORDU, operatörün
    # elle değişikliği yeniden başlatmaya dek yok sayılırdı → her döngüde reload_config (tutarlilik);
    # G3 VALID_REGIMES ≡ regime.py etiketleri artık test edilir; G4 override yeni knob icat edemez.
    # Testler: test_config_audit_v25.py (12).
    "config": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- tur 9 (2026-07-21): broker (SAYILAN P&L) ---
    # K1 muhasebe özdeşliği: equity == start + Σ pnl_dollars, çok işlemli + kısmi satışlı dizide
    # BİREBİR (H1 çifte-ücretlendirme hatası tam burada patlardı) → korunum; K2 iz süren stop yalnız
    # yukarı + bar stop'u kırdıysa iyimser bankalama yasak → monotonluk. Testler: test_broker_audit_v24 (9).
    # boşluk turu 5: kapanan her pozisyon bir SATIR üretir; aynı bar/plan → aynı dolum ve aynı P&L.
    "broker": ["uretkenlik", "korunum", "determinizm", "monotonluk"],
    # --- tur 11 (2026-07-21): earnings ---
    # E1 "in_blackout False" = 'temiz' mi 'HİÇ VERİ YOK' mu ayrılmıyordu; CANLI: 250 evrenin 181'i
    # biliniyor → 69 isimde guard sessizce kapalıydı. known()/coverage() + plan kaydında coverage
    # damgası (korunum). E2 takvim bayatlarsa guard HERKES için kapanır → watchdog 'earnings_calendar'
    # (uretkenlik). Ayrıca dedektörün kendi sessiz hatası bulundu ve kilitlendi.
    # Testler: test_earnings_audit_v26.py (10).
    "earnings": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"], # --- tur 12 (2026-07-21): guard ---
    # GU2 BULGU: sert zarfın İKİ kopyası vardı ve AYRIŞMIŞLARDI — classify_gate R:R tabanını/ısı
    # tavanını HARD'a çevirmiş, check_trade'deki kopya geride kalmış, canlıda NO_GO olan plana
    # "geçti" diyordu. check_trade artık classify_gate'i çağırıyor (yapısal tek yasa) + 144 senaryo
    # eşdeğerlik testi (tutarlilik). GU1 GOAL_KEYS/LIMIT_KEYS ≡ goal.yaml drift testi (sahiplik).
    # Testler: test_guard_audit_v27.py (10).
    "guard": ["korunum", "determinizm", "tutarlilik", "sahiplik"], # --- tur 13 (2026-07-21): hermes ---
    # H1 sistemin MERKEZİ iddiası ("LLM önerir, kapı karar verir") hiçbir yerde zorlanmıyordu →
    # AST tabanlı yetki testi (dump_yaml/bump/save_strategy ÇAĞRISI yok) + davranışsal delege testi +
    # sertifikasız-rejim yan kapısı (sahiplik). H2 anahtar değeri log/ping cevabında yok (sahiplik).
    # H3 RPD dolunca sessiz açlık değil, günde bir kayıt + deterministik yola düşüş (korunum).
    # Testler: test_hermes_audit_v28.py (11).
    "hermes": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"], # --- tur 14 (2026-07-21): hermes_runtime ---
    # HR1 ufuk koşulu İKİ yerde hesaplanıyor (karar + panoya yazılan) → 144 senaryo eşdeğerlik testi
    # (tutarlilik; guard'daki iki-yüzey hatasının aynı sınıfı, burada ayrışma YOKTU). HR3 yeniden
    # başlatmada taban geri sarmaz/sıfırlanmaz — livelock koruması (monotonluk). HR2 tek-yansıma
    # kilidi + HR4 arka plan rejimi canlıyı hedeflemez. Testler: test_hermes_runtime_audit_v29.py (10).
    # boşluk turu 4: durum dosyası üretilir, her yansıma sonucu kaydedilir, YALNIZ kendi dosyasını yazar.
    "hermes_runtime": ["uretkenlik", "korunum", "tutarlilik", "monotonluk", "sahiplik"], # --- tur 15 (2026-07-21): indicators ---
    # I1 ÖNEK KARARLILIĞI: seriyi kesip hesapla, geçmiş DEĞİŞMESİN — 7 fonksiyon için ileri-dönük
    # kanıtı (determinizm). I2 rs_rating BERABERLİK HATASI BULUNDU: argsort beraberlere keyfî ayrı
    # sıra veriyordu (aynı getiri → RS 50 vs 99) ve rs_rating_min sert eşik olduğu için AYNI kanıt
    # zıt kararlar üretiyordu; ortalama-sıra + sıradan bağımsızlık testi (tutarlilik).
    # Testler: test_indicators_audit_v30.py (23).
    "indicators": ["uretkenlik", "determinizm", "tutarlilik"],
    # --- tur 16 (2026-07-21): mcp_server ---
    # MC1 "MUTLAK: yalnız getter" iddiası iki katmanlı kanıtla bağlandı — AST'de yazma çağrısı yok +
    # tüm araçlar koştuktan sonra state klasörünün SHA'ları değişmiyor (sahiplik). MC2 öngörü saflığı:
    # candidate_context r_multiple/pnl/exit_reason DÖNMEZ (korunum — sonuç sızarsa ajanın "tahmini"
    # geriye dönük kusursuz olur). MC3 protokol dayanıklılığı. Testler: test_mcp_audit_v31.py (9).
    "mcp_server": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"], # --- tur 17 (2026-07-21): memory ---
    # ME1 kimlik `len+1` idi → defter kısalınca GERİ SARIYORDU (iki hipotez aynı kimlik); artık
    # max(mevcut)+1, tek yönlü (monotonluk). ME2 terfi mandalı + ME3 durum damgası yalnız GEÇİŞTE
    # (aylık kota ve kalibrasyon kapısı bunlara dayanıyor) → korunum.
    # Testler: test_memory_audit_v32.py (9).
    # boşluk turu 4: defter + dersler üretilir, dersler defter değişince TAZELENİR, memory canlı
    # stratejiye yazmaz (defter tutar, karar vermez).
    "memory": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"], # --- tur 18 (2026-07-21): mirror_stream ---
    # MS1 kaçan tek bir terminal olay sembolü SONSUZA dek karar dışı bırakıyordu (sessiz açlık) →
    # 24 sa bayatlık ufku + kayıt (korunum). MS2 BULGU: kopuş yolunda iptal mantığının ikinci
    # kopyası vardı; operatörün emirlerini de iptal ediyor ve `partially_filled` PENDING'de olduğu
    # için KISMEN DOLMUŞ parent'ı iptal edip pozisyonu ÇIPLAK bırakabiliyordu → adaptörün
    # denetlenmiş yoluna delege edildi (sahiplik). Testler: test_mirror_stream_audit_v33.py (10).
    "mirror_stream": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"], # --- tur 19 (2026-07-21): notify ---
    # N1 dışarıya veri gönderen TEK yol; giden metinden bilinen sır değerleri temizlenir (sahiplik).
    # N2 teslimat başarısızlığı artık kayıtlı — "bildirim gelmedi" ile "alarm yoktu" ayrıldı (korunum).
    "notify": ["korunum", "sahiplik", "uretkenlik"],
    # --- tur 20 (2026-07-21): obs ---
    # O1 BULGU: bildirim izin listesinde HALT_ACTIVE, ROLLBACK ve HEARTBEAT_STALE YOKTU — "beni
    # uyandır" sınıfının tamamı sessizdi. Eklendi + her ALARM_* sabitinin sınıflandırıldığı test
    # (unutkanlık değil, karar). Alarm hattı: bildirim çökse bile kayıt düşer (korunum).
    "obs": ["uretkenlik", "korunum", "tutarlilik", "monotonluk", "sahiplik"],
    # --- tur 21 (2026-07-21): probgate ---
    # PG1 meta-kalibrasyon YALNIZ sıkıştırır (negatif/dev/bozuk dosya kelepçelenir) → monotonluk;
    # PG2 verdikt TOHUMDAN bağımsız (4 tohumda net vakalar aynı karar) → determinizm; PG3 aynı/kötü
    # aday asla geçmez; PG4 K-cezası monoton. Testler: test_probgate_audit_v35.py (12).
    "probgate": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- tur 22 (2026-07-21): oos_pipeline ---
    # Modülün merkezi iddiası ("teyit dilimine arama ASLA dokunmaz") hiçbir yerde kanıtlanmıyordu:
    # dilimleri backtest kuruyor, kapı hazır alıyor. Artık gerçek walk_forward çıktısında AYRIKLIK +
    # kronoloji + sınırı aşan işlemin purge edilmesi test ediliyor (tutarlilik); dilim yoksa sessiz
    # 'geçti' değil dürüst legacy (korunum). Testler: test_oos_pipeline_audit_v36.py (8).
    "oos_pipeline": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- tur 23 (2026-07-21): regime ---
    # RG1 BULGU: canlı döngü + cf_backfill leading_sectors'ı dolduruyor, BACKTEST doldurmuyordu →
    # guard'ın soft kontrolü kapıda ölü, canlıda diri (aynı yasanın ayrışmış iki uygulaması).
    # Backtest de dolduruyor artık (tutarlilik). RG2 bütçe sert tavan + skor sıralaması (monotonluk).
    # Testler: test_regime_audit_v37.py (11).
    "regime": ["determinizm", "monotonluk", "tutarlilik", "uretkenlik"],
    # --- tur 24 (2026-07-21): regime_trigger ---
    # Modülün tek iddiası "KARAR VERMEZ": yalnız sayar, rejim başına BİR kez haber verir, hiçbir
    # bütçe/strateji alanına dokunmaz — üçü de test altında (sahiplik + korunum).
    "regime_trigger": ["uretkenlik", "korunum", "determinizm", "monotonluk", "sahiplik"], # --- tur 25 (2026-07-21): rollback ---
    # RB1 evaluate_outcomes ile check_and_rollback skorları AYRI hesaplıyor → "geri al" kararının
    # gerçekten geri aldığı uçtan uca test edildi (korunum). Yeni: ebeveyn anlık görüntüsü kayıpsa
    # geri alma sessiz bir uyarıya gömülüyordu; artık ALARM + dürüst "hâlâ canlı" raporu.
    # RB3 rejim ship'i kendi diliminde ölçülür, GLOBAL live_score kirletilmez (tutarlilik).
    # Testler: test_rollback_audit_v38.py (9).
    # boşluk turu 4: sonuç kaydı üretilir (realized_delta + karne), terfi tek yönlü mandal,
    # strateji YALNIZ versioning.revert_to üzerinden değişir (ham yazım yok).
    "rollback": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- tur 26 (2026-07-21): run ---
    # RU1 BULGU: --replay scoreboard.json'u TEK sürümlük sözlükle EZİYORDU; v2/v3 sonrası bir re-seed
    # tüm öğrenme karnesini yok eder ve rollback'in ebeveyn-skoru geri düşüşünü körleştirirdi. Artık
    # çok sürümlü karne varsa REDDEDER, zorlanırsa ARŞİVLER (korunum + sahiplik: yıkıcı yol açık niyet ister).
    # Testler: test_run_audit_v39.py (7).
    "run": ["korunum", "sahiplik", "uretkenlik"],
    # --- tur 27 (2026-07-21): score ---
    # SC1 bilinmeyen skor None (0.0 değil); SC2 yıllıklaştırma PENCEREYE bağlı — kümeye sıkışmış
    # patlama şişmiyor (audit #5 regresyon kilidi); SC3 M2M drawdown'ı yalnız KÖTÜLEŞTİREBİLİR
    # (açık pozisyon saklanamaz); SC4/SC5 kuyruk bootstrap'ı ve skorlama deterministik.
    # Testler: test_score_audit_v40.py (12).
    "score": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- tur 28 (2026-07-21): secrets ---
    # SE1 yazma izin listesi (PATH/MERIDIAN_MODE panodan ASLA set edilemez) + sınır davranışları;
    # SE2 0600 YAZARKEN uygulanıyordu ama OKURKEN bakılmıyordu → gevşek izin bir kez raporlanır
    # (çalışmayı engellemeden); SE3 repo genelinde "sır değeri loga gitmiyor" statik ağı + mask.
    # Testler: test_secrets_audit_v41.py (10).
    "secrets": ["korunum", "determinizm", "tutarlilik", "sahiplik"], # --- tur 29 (2026-07-21): skill_evolve ---
    # SK1 BULGU: koruma YALNIZ taslak üretimindeydi; apply_revision hiçbir kontrol yapmıyordu —
    # elde taslağı olan KORUNAN bir skill (kapı skill'i dahil) onayla EZİLEBİLİRDİ. SK2 BULGU: skill
    # adı doğrudan os.path.join'e giriyordu; '../..' içeren bir ad skills/ DIŞINDA dosya değiştirirdi.
    # İkisi de kapatıldı + reddedişler kayda geçiyor (sahiplik). SK3 otomatik uygulama yok (korunum).
    # Testler: test_skill_evolve_audit_v42.py (15).
    "skill_evolve": ["korunum", "sahiplik", "uretkenlik"], # --- tur 30 (2026-07-21): skills ---
    # SL2 BULGU: kayıt defteri KİLİTSİZ oku-değiştir-yaz ile İKİ daemon iş parçacığından yazılıyordu
    # (pipeline damgası + pano gölge kararı) — memory.py'deki audit #19 kayıp-güncelleme deseninin
    # aynısı; bir 'shadow' kararı sessizce geri dönebilirdi. Kilit + eşzamanlılık testi (sahiplik).
    # SL1 korunan skill hiçbir yoldan kapatılamaz; SL3 'koşan' ile 'mevcut' ayrı (korunum).
    # Testler: test_skills_audit_v43.py (9).
    "skills": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- tur 31 (2026-07-21): spend ---
    # SP1 BULGU: tek global fiyat vardı ve record(model=...) onu YOK SAYIYORDU — ücretsiz Gemini/Nous
    # çağrıları Opus listesiyle fiyatlanıp HARCANMAMIŞ parayla bütçeyi doldurabiliyor ve beyni
    # sessizce kapatabiliyordu. Model başına fiyat tablosu (tutarlilik). SP2 defter UTC'ye alındı.
    # Testler: test_spend_audit_v44.py (9).
    "spend": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- tur 32-33 (2026-07-21): sprint + sprint_run ---
    # SR1 izolasyon üç ayağa dayanıyordu (kopyalama, MERIDIAN_ROOT, SKIP_COPY) ve hiçbiri test
    # edilmiyordu → üçü de kilitli; _reset_sandbox_state'in CANLI deftere dokunmadığı davranışsal
    # olarak kanıtlandı (sahiplik). SR2 pencereler sabit ve AYRIK — env'den ayarlanamaz (p-hacking
    # koruması, tutarlilik). SR3 eğitim sonucu canlı kalibrasyona karışmıyor. SR4 HALT/sırlar
    # kum havuzuna kopyalanmıyor. Testler: test_sprint_audit_v45.py (11).
    "sprint": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"],
    "sprint_run": ["korunum", "sahiplik", "uretkenlik"], # --- tur 34 (2026-07-21): store ---
    # ST1 bozuk state dosyası SESSİZCE varsayılana düşüyordu — portfolio.json bozulursa defter BOŞ
    # görünür ve motor pozisyonlar yokmuş gibi davranır (sistemin en tehlikeli sessiz hatası).
    # ST2 append atomik değil; yarım satır sessizce atlanıyordu. İkisi de artık dosya başına bir kez
    # KAYDA geçiyor (korunum) + atomik yazım/numpy temizliği kilitli (determinizm).
    # --- tur 35: strategy — sinyal determinizmi + stop tetiğin altında + trail sert stopu gevşetmez.
    # --- tur 36: validation_report — yalnız KAYITLI kanıtı gösterir, kendi ölçümünü yapmaz.
    # Testler: test_store_strategy_audit_v46.py (10).
    "store": ["uretkenlik", "korunum", "determinizm", "sahiplik"],
    "strategy": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk"],
    "validation_report": ["determinizm", "tutarlilik", "uretkenlik"],
}

# =============================================================================================
# UYGULANABİLİRLİK (2026-07-21, ilk tam turdan sonra)
#
# %33 sayısı YANILTICIYDI ve bunu kayıt üretti: payda 49×6=294, yani HER bileşende HER desenin
# doldurulması gerekiyormuş gibi. Oysa bazı sorular bazı modüller için ANLAMSIZ:
#   * score.py saf bir fonksiyon — "monoton nicelik geri gidiyor mu?" sorusunun öznesi yok.
#   * indicators.py hiçbir şey YAZMAZ — "sahibi olmadığı alanı eziyor mu?" sorulamaz.
#   * guard.py bir doğrulayıcıdır, ÜRETMEZ — "çıktısı var mı?" yanlış soru.
# Bu hücreleri "eksik" saymak, ölçüyü bir NOT'a çeviriyor ve gerçek boşlukları gürültüye gömüyor.
#
# Kural (muhafazakâr): şüphe varsa UYGULANABİLİR say. Aşağıdaki liste her bileşen için desenin
# SORULABİLİR olduğu hücreleri verir; gerçek kapsam = dolu / uygulanabilir.
#   uretkenlik  → modül kalıcı bir çıktı/artefakt üretiyor mu?
#   korunum     → içine giren sayılabilir bir şey var mı (plan, çağrı, satır)?
#   determinizm → hesap bizim tarafımızda mı (uzak yanıt değil)?
#   tutarlilik  → bir kaynaktan TÜREYEN bir şey tutuyor mu?
#   monotonluk  → ileri-only bir nicelik var mı?
#   sahiplik    → durum/dosya/dış kaynak YAZIYOR mu?
# =============================================================================================
_ALL = tuple(PATTERNS)
APPLICABLE: dict[str, tuple[str, ...]] = {
    "adapters.alpaca":       _ALL,
    "adapters.constituents": ("uretkenlik", "determinizm", "tutarlilik", "sahiplik"),
    "adapters.data":         _ALL,
    "adapters.fmp":          ("uretkenlik", "korunum", "sahiplik"),
    "adapters.macro":        ("uretkenlik", "determinizm", "tutarlilik"),
    "adapters.news":         ('uretkenlik', 'korunum', 'determinizm'),
    "analytics":             ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "api":                   ('uretkenlik', 'korunum', 'tutarlilik', 'sahiplik'),
    "arming":                ("uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"),
    "backtest":              ("uretkenlik", "korunum", "determinizm", "tutarlilik"),
    "broker":                ("uretkenlik", "korunum", "determinizm", "monotonluk"),
    "cf_backfill":           ("uretkenlik", "korunum", "determinizm", "sahiplik"),
    "config":                ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "counterfactual":        _ALL,
    "dataset":               ('uretkenlik', 'determinizm', 'tutarlilik', 'sahiplik'),
    "earnings":              ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "guard":                 ('korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "health":                ("uretkenlik", "tutarlilik", "monotonluk", "sahiplik"),
    "hermes":                ("uretkenlik", "korunum", "tutarlilik", "sahiplik"),
    "hermes_runtime":        ("uretkenlik", "korunum", "tutarlilik", "monotonluk", "sahiplik"),
    "indicators":            ('uretkenlik', 'determinizm', 'tutarlilik'),
    "loop":                  _ALL,
    "mcp_server":            ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "memory":                _ALL,
    "mirror_stream":         ("uretkenlik", "korunum", "tutarlilik", "sahiplik"),
    "notify":                ("uretkenlik", "korunum", "sahiplik"),
    "obs":                   ('uretkenlik', 'korunum', 'tutarlilik', 'monotonluk', 'sahiplik'),
    "oos_pipeline":          ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik'),
    "probgate":              _ALL,
    "reflect":               _ALL,
    "regime":                ("uretkenlik", "determinizm", "tutarlilik", "monotonluk"),
    "regime_trigger":        ('uretkenlik', 'korunum', 'determinizm', 'monotonluk', 'sahiplik'),
    "rollback":              _ALL,
    "run":                   ("uretkenlik", "korunum", "sahiplik"),
    "scheduler":             _ALL,
    "score":                 ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik'),
    "secrets":               ('korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "selfreview":            ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "shadow_model":          ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "skill_evolve":          ("uretkenlik", "korunum", "sahiplik"),
    "skills":                ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
    "spend":                 _ALL,
    "sprint":                ("uretkenlik", "korunum", "tutarlilik", "sahiplik"),
    "sprint_run":            ("uretkenlik", "korunum", "sahiplik"),
    "store":                 ('uretkenlik', 'korunum', 'determinizm', 'sahiplik'),
    "strategy":              ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'monotonluk'),
    "validation_report":     ("uretkenlik", "determinizm", "tutarlilik"),
    "versioning":            _ALL,
    "watchdog":              ('uretkenlik', 'korunum', 'determinizm', 'tutarlilik', 'sahiplik'),
}


def gaps() -> list[dict]:
    """UYGULANABİLİR ama HÂLÂ BOŞ hücreler — denetimin gerçek kuyruğu. (N/A hücreler burada YOK;
    onlar 'yapılmadı' değil 'sorusu yok' demek.)"""
    out = []
    for comp, app in sorted(APPLICABLE.items()):
        cov = set(COVERED.get(comp, []))
        missing = [p for p in app if p not in cov]
        if missing:
            out.append({"component": comp, "missing": missing, "covered": sorted(cov)})
    return out


AUDIT_LOG = "integrity_audit_log.json"      # {bileşen: son denetim ISO tarihi}


def coverage_report() -> dict:
    """Kapsam tablosu. İKİ payda birden verilir çünkü ham payda (49×6) YANILTICI:
      * cells_total    — tüm ızgara (tarihsel kıyas için)
      * cells_applicable — sorunun ANLAMLI olduğu hücreler (gerçek payda)
    coverage_pct artık uygulanabilir paydaya göre; ham oran raw_pct'te durur."""
    total_cells = len(COVERED) * len(PATTERNS)
    filled = sum(len(v) for v in COVERED.values())
    applicable = sum(len(v) for v in APPLICABLE.values())
    unaudited = sorted(k for k, v in COVERED.items() if not v)
    by_pattern = {p: {"covered": sum(1 for v in COVERED.values() if p in v),
                      "applicable": sum(1 for v in APPLICABLE.values() if p in v)}
                  for p in PATTERNS}
    g = gaps()
    return {"components": len(COVERED), "patterns": len(PATTERNS),
            "cells_covered": filled, "cells_total": total_cells,
            "cells_applicable": applicable,
            "cells_na": total_cells - applicable,
            "coverage_pct": round(100 * filled / applicable, 1) if applicable else 0.0,
            "raw_pct": round(100 * filled / total_cells, 1),
            "open_gaps": sum(len(x["missing"]) for x in g),
            "components_with_gaps": len(g),
            "unaudited": unaudited, "unaudited_n": len(unaudited),
            "by_pattern": by_pattern, "next_target": next_audit_target()}


def next_audit_target() -> str | None:
    """Dönüşümlü denetim: EN UZUN süredir denetlenmemiş bileşeni seç (hiç denetlenmemişler önce).
    Böylece kapsam tahminle değil, sırayla ve ölçülebilir biçimde büyür."""
    log = store.read_json(AUDIT_LOG, {}) or {}
    never = sorted(k for k, v in COVERED.items() if not v and k not in log)
    if never:
        return never[0]
    if not log:
        return sorted(COVERED)[0]
    return min(COVERED, key=lambda k: log.get(k, ""))


def record_audit(component: str, patterns_now_covered: list[str] | None = None) -> dict:
    """Bir bileşen denetlendiğinde çağrılır: tarihi damgalar (kapsam matrisi kodda güncellenir).
    Kayıt tutmak, 'denetledim sanıyordum' hatasını engeller."""
    from . import memory
    log = store.read_json(AUDIT_LOG, {}) or {}
    log[component] = memory.now_iso()
    store.write_json(AUDIT_LOG, log)
    return {"component": component, "at": log[component],
            "covered": patterns_now_covered or COVERED.get(component, [])}
