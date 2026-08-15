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
    # cf SIFIR YETKİ (submit/commit/dump_yaml/heartbeat çağrısı yok) ve yalnız kendi
    # iki dosyasını yazar; çözümleme aynı girdide aynı satırları verir.
    "counterfactual":   ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- loop ---
    # Motorun kalbi. korunum+monotonluk zaten vardı (geriye-seans bekçisi + plan korunumu); kalan 4:
    # bir döngü GERÇEKTEN artefakt üretir (regime/data_quality/portfolio/nabız); aynı gün iki kez
    # işlenince defter ÇOĞALMAZ (regresyon kilidi); regime.json İŞLENEN günün tarihini
    # taşır; döngü goal/bounds/strategy/secrets'a ASLA yazmaz + yazdığı dosyalar beyan listesiyle
    # sınırlı. Testler: test_loop_gaps_v48.py (9).
    "loop":             ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # sabit defterde kalibrasyonlar tekrarlanabilir; analytics ölçer, KARAR VERMEZ
    # (commit/dump_yaml çağrısı yok) ve yalnız kendi kalibrasyon dosyalarını yazar.
    "analytics":        ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- adapters.data ---
    # Kaynak-ölçeği dikişi (pin + geçmiş-değişti → rev bump) → determinizm+tutarlilik;
    # satır-kaybı reddi → monotonluk; atomik yazım + evren-küçülme kaydı → korunum;
    # kaynak sağlığı (FMP 429 artık görünür) → uretkenlik; kaynak sabitlemesi → sahiplik.
    # Testler: test_data_audit_v17.py (12).
    "adapters.data":    ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- reflect ---
    # Ship YETKİSİ. determinizm zaten vardı (havuz işçisi load_cached); kalan 5 desen kapatıldı:
    # her DEĞERLENDİRİLEN öneri bir hipotez satırı üretir ve kayıtlı bir terminale ulaşır (guard/
    # kapı/teyit/ship/öğrenme-durdu/kilit); wf önbelleği bar revizyonuna bağlı; ship sürümü İLERİ
    # taşır ve red canlıya dokunmaz; versioning.commit'i çağıran TEK yer burası + süreçler-arası
    # kilit. Testler: test_reflect_gaps_v47.py (10).
    "reflect":          ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # pencereler sabit+sıralı ve env'den ayarlanamaz; fetch_end HER çağrıda bugün
    # (donmuş sabit hatası); load_cached ağ/tazeleme yollarına hiç dokunmaz.
    "dataset":          ["uretkenlik", "determinizm", "tutarlilik", "sahiplik"],
    # --- health + scheduler ---
    # health: nabız ÜRETİLİR + zorunlu alanları taşır; yaş dürüst ölçülür (bozuk/eksik damga = BAYAT,
    # taze değil); zaman ileri gider; halt/learn-halt ayrı kapılar ve nabızla tutarlı.
    "health":           ["uretkenlik", "tutarlilik", "monotonluk", "sahiplik"],
    # scheduler: nabız damgası + işlenen son seans kaydı (tekrar/atlama görünür), ileri-only ilerleme.
    "scheduler":        ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # yetersiz örneklemde SESSİZ kalmaz (skip olayı + w=None + predict_proba None,
    # uydurma p_win yok); aynı veriden aynı katsayılar (saf-numpy GD).
    "shadow_model":     ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # rapor HER çağrıda üretilir ve diske düşer; sabit durumda birebir tekrarlanır.
    "selfreview":       ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # versioning: her commit bir SNAPSHOT üretir (geri alma onsuz çalışmaz — canlıda ısırdı);
    # sürüm numarası geri alma sonrası bile ASLA yeniden kullanılmaz; karne satırları birleşir, ezilmez.
    "versioning":       ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    "watchdog": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # SIFIR YETKİ statik olarak kanıtlandı (yalnız cf defterine yazar; commit/
    # dump_yaml/heartbeat/submit çağrısı YOK), ağa çıkmaz (önbellek CSV), rastgelelik kullanmaz.
    "cf_backfill":      ["uretkenlik", "korunum", "determinizm", "sahiplik"],
    # --- adapters.alpaca ---
    # Taşıma kaydı (yutulan hata görünür) → korunum+üretkenlik; coid birleştirme anahtarı +
    # broker_reconcile tazeliği → tutarlılık; önek süzgeci + close_all onay jetonu → sahiplik;
    # sınırda stop-gevşetme reddi → monotonluk. Testler: test_alpaca_audit_v16.py (14).
    # DETERMİNİZM: aynı plan → aynı emir gövdesi testi var (test_determinism_same_plan_same_body),
    # ama gerçek broker yanıtı deterministik DEĞİL (fill fiyatı) — bu hücreyi dürüstlük gereği
    # 'covered' saymıyorum: kontrol yalnız BİZİM gönderdiğimiz tarafı bağlıyor.
    "adapters.alpaca": ["determinizm", "korunum", "monotonluk", "sahiplik", "tutarlilik", "uretkenlik"],
    # --- adapters.constituents ---
    # ÜRETKENLİK: modülün HİÇ tüketicisi yoktu (üç denetimlik düzeltme ölü kodda) → artık P5'te
    # universe_drift() çağrılıyor + health() watchdog'a bağlı. TUTARLILIK: makullük kapısı +
    # gelecek-tarih reddi (üretim önbelleği test fixture'ıydı: 3 sembol, as_of 2099).
    # Diğer dört desen DÜRÜSTÇE boş: burada monoton nicelik yok, sahiplik/korunum/determinizm için
    # gerçek bir kontrol yazmadım — "baktım, iyi görünüyor" kapsam sayılmaz.
    # Testler: test_constituents_audit_v18.py (13).
    "adapters.constituents": ["determinizm", "sahiplik", "tutarlilik", "uretkenlik"],
    # --- HENÜZ DENETLENMEMİŞ (dönüşümlü denetimin kuyruğu) ---
    # --- adapters.fmp ---
    # Strict mod + kısmi-hata koruması (yarım kazanç takvimi guard'ı FAIL-OPEN yapıyordu) →
    # korunum; günlük kota muhasebesi + 429 soğuması → uretkenlik; anahtar maskesi ve
    # "anahtar tek yerde okunur" testi → sahiplik. Testler: test_fmp_audit_v19.py (7).
    "adapters.fmp": ["uretkenlik", "korunum", "sahiplik"],
    # --- adapters.macro + adapters.news ---
    # macro: DONMUŞ son tarih ("2026-07-10") → her çağrıda bugün + test (tutarlilik); "tüketicisi yok"
    # artık status()'ta yazılı (uretkenlik'in dürüst cevabı, gerçek bir kontrolle: status testi).
    # news: 'anahtar var' ≠ 'çalışıyor' → status() kaynak sağlığını taşır (uretkenlik); 20 sembol
    # üstü SESSİZ kırpma → kayıt (korunum). Testler: test_macro_news_audit_v20.py (7).
    "adapters.macro": ["determinizm", "tutarlilik", "uretkenlik"],
    "adapters.news": ["uretkenlik", "korunum", "determinizm"],
    # --- api ---
    # "Her mutasyon ucu yetki ister" bugün doğruydu ama ZORLANMIYORDU → statik kural testi
    # (19/19 authed, yeni yetkisiz POST eklenirse test kırılır) + yetkisiz GET izin listesi;
    # /metrics yetkisiz olarak öz sermaye/P&L/harcama yayınlıyordu, /halt tünelden açıldığı için
    # bu dışarı bakan bir yüzey → uzak+yetkisiz istekte yalnız canlılık. Testler: test_api_audit_v21 (8).
    "api": ["uretkenlik", "korunum", "tutarlilik", "sahiplik"],
    # --- arming ---
    # Modülün MERKEZİ iddiası ("yalnız ölçer, silahlandırmaz") yazılıydı ama zorlanmıyordu →
    # kaynak + davranış testi (sahiplik). CANLIDA: "ölçülemedi" (candidate OOS undefined)
    # "gate_rejected" diye kaydediliyordu — kurulumu haksızca gömen sahte kanıt; artık
    # gate_undefined ayrı bir terminal (korunum). Testler: test_arming_audit_v22.py (6).
    # rapor HER koşuda diske düşer, aynı kanıtla aynı ölçüm, cf defterinden türer.
    "arming": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- backtest (KAPININ KENDİSİ) ---
    # İleri-dönük sızıntı: docstring'de anlatılıyor, kanıtlanmıyordu → "geleceği kes, geçmiş
    # değişmesin" testi (determinizm); replay + walk_forward tekrarlanabilirliği + girdiye
    # duyarlılık ikizi; SECTORS evreni tam kapsıyor mu + canlıyla AYNI harita mı (tutarlilik).
    # Testler: test_backtest_audit_v23.py (8).
    # replay tam kanıt paketi üretir (işlemler + plan/aday defteri + öz sermaye
    # eğrisi) ve DEĞERLENDİRİLEN her plan bir karar taşır (sessizce düşen plan yok).
    "backtest": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- config ---
    # Boş/bozuk strategy.yaml {} döndürüyordu (motor params={} ile koşabilirdi) → varsayılana
    # düşer + kayıt (korunum); goal/bounds lru_cache uzun ömürlü süreçte DONUYORDU, operatörün
    # elle değişikliği yeniden başlatmaya dek yok sayılırdı → her döngüde reload_config (tutarlilik);
    # VALID_REGIMES ≡ regime.py etiketleri artık test edilir; override yeni knob icat edemez.
    # Testler: test_config_audit_v25.py (12).
    "config": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- broker (SAYILAN P&L) ---
    # Muhasebe özdeşliği: equity == start + Σ pnl_dollars, çok işlemli + kısmi satışlı dizide
    # BİREBİR (çifte-ücretlendirme hatası tam burada patlardı) → korunum; iz süren stop yalnız
    # yukarı + bar stop'u kırdıysa iyimser bankalama yasak → monotonluk. Testler: test_broker_audit_v24 (9).
    # kapanan her pozisyon bir SATIR üretir; aynı bar/plan → aynı dolum ve aynı P&L.
    "broker": ["uretkenlik", "korunum", "determinizm", "monotonluk"],
    # --- earnings ---
    # "in_blackout False" = 'temiz' mi 'HİÇ VERİ YOK' mu ayrılmıyordu; CANLI: 250 evrenin 181'i
    # biliniyor → 69 isimde guard sessizce kapalıydı. known()/coverage() + plan kaydında coverage
    # damgası (korunum). takvim bayatlarsa guard HERKES için kapanır → watchdog 'earnings_calendar'
    # (uretkenlik). Ayrıca dedektörün kendi sessiz hatası bulundu ve kilitlendi.
    # Testler: test_earnings_audit_v26.py (10).
    "earnings": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"], # --- guard ---
    # BULGU: sert zarfın İKİ kopyası vardı ve AYRIŞMIŞLARDI — classify_gate R:R tabanını/ısı
    # tavanını HARD'a çevirmiş, check_trade'deki kopya geride kalmış, canlıda NO_GO olan plana
    # "geçti" diyordu. check_trade artık classify_gate'i çağırıyor (yapısal tek yasa) + 144 senaryo
    # eşdeğerlik testi (tutarlilik). GOAL_KEYS/LIMIT_KEYS ≡ goal.yaml drift testi (sahiplik).
    # Testler: test_guard_audit_v27.py (10).
    "guard": ["korunum", "determinizm", "tutarlilik", "sahiplik"], # --- hermes ---
    # Sistemin MERKEZİ iddiası ("LLM önerir, kapı karar verir") hiçbir yerde zorlanmıyordu →
    # AST tabanlı yetki testi (dump_yaml/bump/save_strategy ÇAĞRISI yok) + davranışsal delege testi +
    # sertifikasız-rejim yan kapısı (sahiplik). Anahtar değeri log/ping cevabında yok (sahiplik).
    # RPD dolunca sessiz açlık değil, günde bir kayıt + deterministik yola düşüş (korunum).
    # Testler: test_hermes_audit_v28.py (11).
    "hermes": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"], # --- hermes_runtime ---
    # Ufuk koşulu İKİ yerde hesaplanıyor (karar + panoya yazılan) → 144 senaryo eşdeğerlik testi
    # (tutarlilik; guard'daki iki-yüzey hatasının aynı sınıfı, burada ayrışma YOKTU). Yeniden
    # başlatmada taban geri sarmaz/sıfırlanmaz — livelock koruması (monotonluk). Tek-yansıma
    # kilidi + arka plan rejimi canlıyı hedeflemez. Testler: test_hermes_runtime_audit_v29.py (10).
    # durum dosyası üretilir, her yansıma sonucu kaydedilir, YALNIZ kendi dosyasını yazar.
    "hermes_runtime": ["uretkenlik", "korunum", "tutarlilik", "monotonluk", "sahiplik"], # --- indicators ---
    # ÖNEK KARARLILIĞI: seriyi kesip hesapla, geçmiş DEĞİŞMESİN — 7 fonksiyon için ileri-dönük
    # kanıtı (determinizm). rs_rating BERABERLİK HATASI BULUNDU: argsort beraberlere keyfî ayrı
    # sıra veriyordu (aynı getiri → RS 50 vs 99) ve rs_rating_min sert eşik olduğu için AYNI kanıt
    # zıt kararlar üretiyordu; ortalama-sıra + sıradan bağımsızlık testi (tutarlilik).
    # Testler: test_indicators_audit_v30.py (23).
    "indicators": ["uretkenlik", "determinizm", "tutarlilik"],
    # --- mcp_server ---
    # "MUTLAK: yalnız getter" iddiası iki katmanlı kanıtla bağlandı — AST'de yazma çağrısı yok +
    # tüm araçlar koştuktan sonra state klasörünün SHA'ları değişmiyor (sahiplik). Öngörü saflığı:
    # candidate_context r_multiple/pnl/exit_reason DÖNMEZ (korunum — sonuç sızarsa ajanın "tahmini"
    # geriye dönük kusursuz olur). Protokol dayanıklılığı. Testler: test_mcp_audit_v31.py (9).
    "mcp_server": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"], # --- memory ---
    # Kimlik `len+1` idi → defter kısalınca GERİ SARIYORDU (iki hipotez aynı kimlik); artık
    # max(mevcut)+1, tek yönlü (monotonluk). Terfi mandalı + durum damgası yalnız GEÇİŞTE
    # (aylık kota ve kalibrasyon kapısı bunlara dayanıyor) → korunum.
    # Testler: test_memory_audit_v32.py (9).
    # defter + dersler üretilir, dersler defter değişince TAZELENİR, memory canlı
    # stratejiye yazmaz (defter tutar, karar vermez).
    "memory": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"], # --- mirror_stream ---
    # Kaçan tek bir terminal olay sembolü SONSUZA dek karar dışı bırakıyordu (sessiz açlık) →
    # 24 sa bayatlık ufku + kayıt (korunum). BULGU: kopuş yolunda iptal mantığının ikinci
    # kopyası vardı; operatörün emirlerini de iptal ediyor ve `partially_filled` PENDING'de olduğu
    # için KISMEN DOLMUŞ parent'ı iptal edip pozisyonu ÇIPLAK bırakabiliyordu → adaptörün
    # denetlenmiş yoluna delege edildi (sahiplik). Testler: test_mirror_stream_audit_v33.py (10).
    "mirror_stream": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"], # --- notify ---
    # Dışarıya veri gönderen TEK yol; giden metinden bilinen sır değerleri temizlenir (sahiplik).
    # Teslimat başarısızlığı artık kayıtlı — "bildirim gelmedi" ile "alarm yoktu" ayrıldı (korunum).
    "notify": ["korunum", "sahiplik", "uretkenlik"],
    # --- obs ---
    # BULGU: bildirim izin listesinde HALT_ACTIVE, ROLLBACK ve HEARTBEAT_STALE YOKTU — "beni
    # uyandır" sınıfının tamamı sessizdi. Eklendi + her ALARM_* sabitinin sınıflandırıldığı test
    # (unutkanlık değil, karar). Alarm hattı: bildirim çökse bile kayıt düşer (korunum).
    "obs": ["uretkenlik", "korunum", "tutarlilik", "monotonluk", "sahiplik"],
    # --- probgate ---
    # Meta-kalibrasyon YALNIZ sıkıştırır (negatif/dev/bozuk dosya kelepçelenir) → monotonluk;
    # verdikt TOHUMDAN bağımsız (4 tohumda net vakalar aynı karar) → determinizm; aynı/kötü
    # aday asla geçmez; K-cezası monoton. Testler: test_probgate_audit_v35.py (12).
    "probgate": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- oos_pipeline ---
    # Modülün merkezi iddiası ("teyit dilimine arama ASLA dokunmaz") hiçbir yerde kanıtlanmıyordu:
    # dilimleri backtest kuruyor, kapı hazır alıyor. Artık gerçek walk_forward çıktısında AYRIKLIK +
    # kronoloji + sınırı aşan işlemin purge edilmesi test ediliyor (tutarlilik); dilim yoksa sessiz
    # 'geçti' değil dürüst legacy (korunum). Testler: test_oos_pipeline_audit_v36.py (8).
    "oos_pipeline": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- regime ---
    # BULGU: canlı döngü + cf_backfill leading_sectors'ı dolduruyor, BACKTEST doldurmuyordu →
    # guard'ın soft kontrolü kapıda ölü, canlıda diri (aynı yasanın ayrışmış iki uygulaması).
    # Backtest de dolduruyor artık (tutarlilik). Bütçe sert tavan + skor sıralaması (monotonluk).
    # Testler: test_regime_audit_v37.py (11).
    "regime": ["determinizm", "monotonluk", "tutarlilik", "uretkenlik"],
    # --- regime_trigger ---
    # Modülün tek iddiası "KARAR VERMEZ": yalnız sayar, rejim başına BİR kez haber verir, hiçbir
    # bütçe/strateji alanına dokunmaz — üçü de test altında (sahiplik + korunum).
    "regime_trigger": ["uretkenlik", "korunum", "determinizm", "monotonluk", "sahiplik"], # --- rollback ---
    # evaluate_outcomes ile check_and_rollback skorları AYRI hesaplıyor → "geri al" kararının
    # gerçekten geri aldığı uçtan uca test edildi (korunum). Yeni: ebeveyn anlık görüntüsü kayıpsa
    # geri alma sessiz bir uyarıya gömülüyordu; artık ALARM + dürüst "hâlâ canlı" raporu.
    # Rejim ship'i kendi diliminde ölçülür, GLOBAL live_score kirletilmez (tutarlilik).
    # Testler: test_rollback_audit_v38.py (9).
    # sonuç kaydı üretilir (realized_delta + karne), terfi tek yönlü mandal,
    # strateji YALNIZ versioning.revert_to üzerinden değişir (ham yazım yok).
    "rollback": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- run ---
    # BULGU: --replay scoreboard.json'u TEK sürümlük sözlükle EZİYORDU; v2/v3 sonrası bir re-seed
    # tüm öğrenme karnesini yok eder ve rollback'in ebeveyn-skoru geri düşüşünü körleştirirdi. Artık
    # çok sürümlü karne varsa REDDEDER, zorlanırsa ARŞİVLER (korunum + sahiplik: yıkıcı yol açık niyet ister).
    # Testler: test_run_audit_v39.py (7).
    "run": ["korunum", "sahiplik", "uretkenlik"],
    # --- score ---
    # bilinmeyen skor None (0.0 değil); yıllıklaştırma PENCEREYE bağlı — kümeye sıkışmış
    # patlama şişmiyor (regresyon kilidi); M2M drawdown'ı yalnız KÖTÜLEŞTİREBİLİR
    # (açık pozisyon saklanamaz); kuyruk bootstrap'ı ve skorlama deterministik.
    # Testler: test_score_audit_v40.py (12).
    "score": ["uretkenlik", "korunum", "determinizm", "tutarlilik"], # --- secrets ---
    # Yazma izin listesi (PATH/MERIDIAN_MODE panodan ASLA set edilemez) + sınır davranışları;
    # 0600 YAZARKEN uygulanıyordu ama OKURKEN bakılmıyordu → gevşek izin bir kez raporlanır
    # (çalışmayı engellemeden); repo genelinde "sır değeri loga gitmiyor" statik ağı + mask.
    # Testler: test_secrets_audit_v41.py (10).
    "secrets": ["korunum", "determinizm", "tutarlilik", "sahiplik"], # --- skill_evolve ---
    # BULGU: koruma YALNIZ taslak üretimindeydi; apply_revision hiçbir kontrol yapmıyordu —
    # elde taslağı olan KORUNAN bir skill (kapı skill'i dahil) onayla EZİLEBİLİRDİ. BULGU: skill
    # adı doğrudan os.path.join'e giriyordu; '../..' içeren bir ad skills/ DIŞINDA dosya değiştirirdi.
    # İkisi de kapatıldı + reddedişler kayda geçiyor (sahiplik). Otomatik uygulama yok (korunum).
    # Testler: test_skill_evolve_audit_v42.py (15).
    "skill_evolve": ["korunum", "sahiplik", "uretkenlik"], # --- skills ---
    # BULGU: kayıt defteri KİLİTSİZ oku-değiştir-yaz ile İKİ daemon iş parçacığından yazılıyordu
    # (pipeline damgası + pano gölge kararı) — memory.py'deki kayıp-güncelleme deseninin
    # aynısı; bir 'shadow' kararı sessizce geri dönebilirdi. Kilit + eşzamanlılık testi (sahiplik).
    # Korunan skill hiçbir yoldan kapatılamaz; 'koşan' ile 'mevcut' ayrı (korunum).
    # Testler: test_skills_audit_v43.py (9).
    "skills": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "sahiplik"],
    # --- spend ---
    # BULGU: tek global fiyat vardı ve record(model=...) onu YOK SAYIYORDU — ücretsiz Gemini/Nous
    # çağrıları Opus listesiyle fiyatlanıp HARCANMAMIŞ parayla bütçeyi doldurabiliyor ve beyni
    # sessizce kapatabiliyordu. Model başına fiyat tablosu (tutarlilik). defter UTC'ye alındı.
    # Testler: test_spend_audit_v44.py (9).
    "spend": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk", "sahiplik"],
    # --- sprint + sprint_run ---
    # İzolasyon üç ayağa dayanıyordu (kopyalama, MERIDIAN_ROOT, SKIP_COPY) ve hiçbiri test
    # edilmiyordu → üçü de kilitli; _reset_sandbox_state'in CANLI deftere dokunmadığı davranışsal
    # olarak kanıtlandı (sahiplik). pencereler sabit ve AYRIK — env'den ayarlanamaz (p-hacking
    # koruması, tutarlilik). Eğitim sonucu canlı kalibrasyona karışmıyor. HALT/sırlar
    # kum havuzuna kopyalanmıyor. Testler: test_sprint_audit_v45.py (11).
    "sprint": ["korunum", "sahiplik", "tutarlilik", "uretkenlik"],
    "sprint_run": ["korunum", "sahiplik", "uretkenlik"], # --- store ---
    # Bozuk state dosyası SESSİZCE varsayılana düşüyordu — portfolio.json bozulursa defter BOŞ
    # görünür ve motor pozisyonlar yokmuş gibi davranır (sistemin en tehlikeli sessiz hatası).
    # Append atomik değil; yarım satır sessizce atlanıyordu. İkisi de artık dosya başına bir kez
    # KAYDA geçiyor (korunum) + atomik yazım/numpy temizliği kilitli (determinizm).
    # --- strategy — sinyal determinizmi + stop tetiğin altında + trail sert stopu gevşetmez.
    # --- validation_report — yalnız KAYITLI kanıtı gösterir, kendi ölçümünü yapmaz.
    # Testler: test_store_strategy_audit_v46.py (10).
    "store": ["uretkenlik", "korunum", "determinizm", "sahiplik"],
    "strategy": ["uretkenlik", "korunum", "determinizm", "tutarlilik", "monotonluk"],
    "validation_report": ["determinizm", "tutarlilik", "uretkenlik"],
}

# =============================================================================================
# UYGULANABİLİRLİK
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
