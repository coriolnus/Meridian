# MERIDIAN YOL HARİTASI — tek kaynak

Koda gömülü faz planlarını, oturum kararlarını ve operatör tercihlerini TEK dosyada toplar; yeni
faz/iş kalemi buraya işlenir, "konuşmada kaldı" diye kaybolmaz. **Düzen (2026-08-09 yeniden
örgütleme — §0-6 mimarisi, operatör onaylı):** işler birbirine girmez, her bilginin TEK doğru yeri
vardır. §0 sözleşme + yasalar + kuzey yıldızı · §1 aktif WP'ler (açık cepheler) · §2 öneri havuzu
(backlog) · §3 operatör blokları · §4 kanıt/kartlar · §5 karar günlüğü (kronolojik, yeni giriş EN
ÜSTE) · §6 arşiv (tamamlanan WP'ler + oturum snapshot'ları). _(Bu tur öncesi düzen §1-7 idi; taşıma
haritası §5'in tepesindeki 2026-08-09 kaydında.)_

---

## §0 SÖZLEŞME — nasıl okunur, yasalar, kuzey yıldızı

**NASIL OKUNUR — her iş türü nereye yazılır (TEK doğru yer):**
- Yeni fikir / iyileştirme önerisi → **§2 ÖNERİ HAVUZU** (biçim: gerekçe · tahmini boyut · bağımlılık · öncelik).
- Olgunlaşan / başlanan açık cephe → **§1 AKTİF WP** (biçim: durum · kapsam · açık kalemler · dosya-sınırı · kanıt-kartı bağı) + Task açılır.
- Operatör kararı / kimliği / parası / bakım penceresi bekleyen → **§3 OPERATÖR BLOKLARI**.
- Ölçüm ön-kaydı / hüküm → **§4 KANIT/KARTLAR** (`research/cards/` indeksi; kartsız ölçüm kodu yok).
- Neden-kaydı (kronolojik, tarihli) → **§5 KARAR GÜNLÜĞÜ** (yeni giriş EN ÜSTE).
- Tamamlanan WP / bayat status snapshot → **§6 ARŞİV** (tarihçe-koru; silme yok).
- Bir bilginin nereye gideceği belirsizse **§5'e not düşülür, SİLİNMEZ**.

**YAŞAM DÖNGÜSÜ:** öneri (§2) → olgunlaşınca §1'e taşınır + Task açılır → bitince §6'ya arşivlenir;
kartı §4'te, kararı §5'te, operatör kalemi §3'te kalır. §1'deki her WP'nin NET SINIRı vardır
(dosya-ayrıklık sözleşmesi); açık kalanı §1'de, tarihçesi §6'da.

**DURUM İŞARETLERİ (§1/§4/§6 boyunca):** ✅ kapalı · 🔄 koşuyor · 🕐 kuyruk · 🔒 bağımlı/bilet ·
📋 sırada · 🔴 aktif/öncelik · 🔶 aktif araştırma · 🆕 yeni · 🔓 kilit açık.


### KUZEY YILDIZI (EDGE VERDICT + SONUÇ HÜKMÜ + yönetici ilke + operatör tercihleri)

**Kuzey yıldızı:** EDGE VERDICT — BEŞ ölçüt (gerçek-katman IC + SPY-üstü + tahmin isabeti + rejim
edge + **KUYRUK**, 5. ölçüt 2026-07-30'da indi). Canlı hüküm: **"1/5 sağlandı (1 zayıf, 2
sağlanmadı, 1 ölçülemedi) — edge kanıtlanmadı."** İKİZİ: **SONUÇ HÜKMÜ** (dolar merceği,
`analytics.result_verdict`) — canlı: **"0/4 sağlandı — para kanıtlanmadı."**
Yönetici ilke: **edge kanıtlanmadan rafineriye (emir bacağı, otonomi, sermaye) yatırım yok** —
rafineri kararları EDGE'e, **sermaye/silahlanma İKİ hükme birden** bakar (R birimi geniş stopa
yapısal önyargılı; dolar merceği olmadan sermaye kararı verilemez).
Operatör tercihleri (2026-07-27 röportajı): eksenler sıralı değil ÖRGÜLÜ; pano ana yüzey; kanıt
gövdesi replay+cf yoğunluğu, gerçek/sim etiketi her yerde açık; kalibrasyon yetkileri eşik dolunca
otomatik açılır; tempo çağrı-üzerine + kritik anlar.

### YASALAR VE KESİŞEN KURALLAR (anayasal — tüm işleri bağlar)

- **NOUS SİSTEM-DEĞERLENDİRME KATMANI (kalıcı anayasal kayıt — WP-konsolidasyonunda düşmüştü,
  F4 sürüklenme testi yakaladı, geri kondu):** Katman A-D haftalık öz-değerlendirme; **Katman D
  anayasal çekirdek KAPALIDIR** — hakim kendi yasasına dokunamaz (CORE_FILES/CORE_CONCEPTS,
  CekirdekIhlali + AUTHORITY_CHANGE alarmı, AST çivisi; nous_eval docstring'i ile aynı söz).

- **Ölçüm-önce:** hiçbir değişiklik ölçümsüz canlıya girmez; kapı (reflect._gate_eval) TEK hakem;
  knob hipotezleri tek-değişken (guard), mimari reform beyanlı bileşik ölçümle (k_probes = denenen).
- **YASA 4** sessiz yutma yasak (kaçış: `# sessiz-yutma: <neden>`) · **YASA 6** üretilen her alanın
  dış tüketicisi olmalı (okuma api.py üzerinden pano) · **UYDURMA YASAĞI** ölçülemeyen None kalır;
  alan adları canlı dosyadan doğrulanır; retro damga yok.
- **Canlı güvenlik:** state/'i yalnız worker yazar; ölçümler sandbox kopyada (config.STATE
  yönlendirme + mtime parmak izi kanıtı); restart'ı operatör koşar (`./ops/stop-worker.sh && ./serve.sh`).
- **Süreç:** turda tek konsolide-brief'li tek Opus implementasyon ajanı; tam suite turda BİR kez,
  ÖN PLANDA senkron (ajan-içi waiter/arka plan bekleyici YASAK — iki kez arıza çıkardı); uzun
  deterministik işler ana oturumdan harness-izlemeli arka planda; hermes SYSTEM statik (AST çivili).
- **Okuma düzeltmeleri:** replay iyimserliği ölçüldü ~+0.018 (motor sapması) — backtest skorları bu
  düzeltmeyle okunur · R-birimi geniş stopa yapısal önyargılı (boyut R-nötr küçülür, kazanan R'leri
  daralır) — çıkış reformu kararları Hafta 3'ün dolar merceğini bekler · McLean-Pontiff: yayınlanmış
  etkinin en fazla YARISI beklenir · cf sadakat sınırı: cf.advance yalnız stop/target/time_stop
  simüle eder (trail/BE/chandelier/giveback/regime_flip/scale_out ve komisyon/ADV/impact YOK —
  makine-okunur sabitlerle beyanlı, v108 canlı-kaynak testi çivili).

_Aşağıdaki sıra 2026-07-31 gecesinden; güncel öncelikler §1 GÜNCEL DURUM'dadır (bayat referans, tarihçe)._
### SIRALAMA (güncel): mevcut dalga (BT-1→WP-E · WP-D-r2 · 1.2/1.4) → sabah konsolidasyon+dağıtım →
**WP-R** → 1.1+1.3+1.5 (S2) → WP-G SMA kartı → WP-U (PIT) → WP-K → WP-M + WP-H sürekli-serpiştirilmiş.
Sprint çıkışı = DoD + testler yeşil + K-defteri güncel; kapanmadan sonraki sprinte geçilmez.

## §1 AKTİF WP'ler — açık cepheler

_Aşağıdaki GÜNCEL DURUM anlık yönelim; ardından uniform ÖZET TABLOSU (her WP tek biçim); sonra WP
detayları (tam metin). Kapanan alt-kalemler ✅ WP içinde tarihçe olarak kalır; tamamlanan WP'ler §6'da._

> **GÜNCEL DURUM — 2026-08-09 ~09:00 UTC (GECE+SABAH DÖRT DAĞITIM İNDİ, son commit `964696b`):**
> Sistem canlı ve sağlıklı — broker `alpaca_paper`, birimler active, otoriter suite YEŞİL (v196
> son iki kırmızıyı kapadı). **4 motor pozisyonu KORUMALI:** broker'da 4 açık `P-KORUMA-…-0835`
> OCO (gtc, sınıf=koruma — NUE/EMR/BKNG/AMGN, submit 08:35:44Z). Gecenin+sabahın dört dağıtımı:
> WP-N kanıt-hızı dalgası (v216-v219) · koruma×süpürücü kök düzeltmesi (v220+v221) · dalga-2
> sahte-yeşil avı (v222-v226) · null-sıfır kapısı (v196). Koruma kalemi (WP-S) canlıda
> ARTEFAKTTAN doğrulandı (alpaca.py yerel↔canlı md5 birebir + 4 OCO broker'da); davranışsal
> EOD-süpürme kanıtı Pazartesi 13:30 UTC sonrası ilk gerçek süpürmede. **EN ACİL OPERATÖR KALEMİ:
> BİLDİRİM KANALI (N1)** — token boş, fail-notify her koşuda NO-OP; teslim edilmemiş sev-1
> birikmiş (korumasız 40 · MIRROR_DRIFT 34 · NAKED_POSITION 8). BAĞ: kanal açılmadan ÖNCE systemd
> exit-143 (WP-S2) düzeltilmeli, yoksa her restart "FAILED" bildirir. Ayrıntı:
> `docs/SABAH-TRIYAJI-2026-08-09.md` + `docs/DEVIR-TATBIKATI-2026-08-09.md`.
> _(Aşağıdaki 2026-07-31 gece-vardiyası kaydı tarihçe olarak korunmuştur.)_

### AKTİF WP ÖZET TABLOSU (uniform biçim: durum · kapsam · açık kalemler · dosya-sınırı · kanıt-kartı)

| WP | durum | kapsam | açık kalemler | dosya-sınırı | kanıt-kartı |
|---|---|---|---|---|---|
| **WP-E** İcra Gerçekliği | 🔴 aktif | iki-motor icra sadakati · E1 giriş · E2 slipaj defteri | ~~ayna-dolum teşhis~~ **✅ TEŞHİS BİTTİ (2026-08-10, 8 boşluk sınıfı — docs/TESHIS-WPE-AYNA-DOLUM):** **#3+#4 koruma-ailesi ✅ DÜZELTİLDİ (v232: iptal→kapat sırası + koruma_dolumu kitaba; Pazartesi riski kapandı)**; KALAN 6: #1 karar-çıkışı dolum körlüğü (~%38 kapanış, slipaj yanlı) · #2 tek-atış yaması · #5 kısmi-dolum sınıfsız · #6 fill_eq_now anakronizmi · #7 pencere boşlukları · #8 motor_yetimi kabul-yolu · E2 canlı-geçiş + E3/E4/E5 örneklem | `loop.py` · `adapters/alpaca.py` · `analytics`(cf) | EXE-2026-001(+R1/R2) · EXE-2026-002 |
| **WP2** Referans-Verisi | 🟢 borç yok | EDGAR PIT fundamentals adayları | ~~turnover kablolama~~ **✅ ZATEN İNMİŞ (5dfca07, 2026-08-03; 2026-08-10 doğrulama 58/0)** — açık borç YOK; yeni PIT-aday özniteliği ancak KART-önce açılır | skor bileşeni + `bounds.yaml` | EDG-2026-016(SUCCESS) · 012/013/014 |
| **WP-U** Evren/PIT | 🔶 aktif (stratejik ana cephe) | survivorship-serbest evren · PIT üyelik · delist-bar | EDG-022 ölçüldü→FINVIZ gerekçesiz (§4) · PIT mid-cap üst-sınır (EDG-018 veri-kapısı) · delist-bar kaynağı + FINVIZ operatörde (§3) | `research/pit_universe/` · `adapters/data.py` | EDG-2026-018/021/022 |
| **WP-S** Sermaye/Koruma | 🔴 aktif | koruma×süpürücü · sermaye defter bütünlüğü · boyut makbuzu | koruma DAVRANIŞSAL EOD kanıtı (Pazartesi 13:30 UTC+) · SB-2 `drift_sinifi` · melez pozisyonlar + dormant setup icra (operatör §3) | `adapters/alpaca.py` · `store.py` · `obs.py` | EXE-2026-001-R1/R2 · EXE-2026-002(+R1) |
| **WP-S2** Ölçüm/Görünürlük Borçları | 📋 aktif | beyanlı ölçüm/görünürlük borçları | ~~artefakt turu~~ **✅ TUR BİTTİ (2026-08-10, docs/TUR-WPS2-ARTEFAKT): 163 SAĞLAM/1 ŞÜPHELİ/0 BAYAT; yasa 0 ihlal, kart→kanıt 24/24; 'provenance ÖLÜ-ADAY' iddiası Rol-1 doğrulamasında ÇÜRÜDÜ (conftest.py:846 koşullu yazar); tek eylem .locks budama→§2-5** · kill#4 uygulama · ajan-git (§3) | `api.py` · `web/app.js` · `guard.py` | EXE-2026-002-R1 |
| **WP-M** Metodoloji/Yasa | 📋 aktif | ölçüm altyapısının kendisi | ~~M1~~ **✅ ZATEN ARŞİV (KYS-001 kill#1, 2026-08-02: yanlılık pratik-önemsiz <10bps CI-0-içi; keşif bayat kayda güvendi, kart otoritesi kapattı — 2026-08-10)** · **M2 PBO-yarısı ✅ ÖLÇÜLDÜ (KYS-002, 2026-08-10): R1 tabanı PBO=0.6286 → kapı her iki modda BLOKLAR (ilk gerçek taban; kapı damgalamayla gerçek iş yapıyor); DSR-yarısı araç-şartlı (kill#2, §2 önerisi)** · M7/M8/M9 ucuz-tur (ajan uçtu) · M11 · 2B/2C/2D/A4 | `analytics` · `reflect` · `dataset` | KYS-2026-001(ARŞİV) · KYS-2026-002(measured_partial) |
| **WP-D** Veri Bütünlüğü | 🔄 aktif | karantina/bütünlük kapıları · türetilmiş artefaktlar | türetilmiş artefakt güvensiz-dönem-dışlamalı yeniden üretim · seans-içi boşluk tespiti · earnings kapsama+fail-open · `dataset.load↔bars_integrity` bağlama (operatör §3) | `adapters/data.py` | — |
| **WP-H** Mühendislik Dayanıklılığı | 🟡 H9 bitti | sürüm kontrolü · atomik yazım · sertleştirme | **H9 A/B/C ✅ İNDİ (2026-08-10, 12 kapı-dışı yazım store kapısına; `auth._write` zero-byte-lockout kök kusuru kapandı; `_write_bars` hot-path dosya-başına kilit)** · AÇIK: H3 tur-2 seccomp · LoadCredential+OCI aktivasyon (operatör §3) | `store.py` · `auth.py` · `hermes.py` · `deploy/` | — |
| **WP-QC** QuantConnect | 🆕 aktif | platform-içi ölçüm + LEAN yerel motor (asla arşiv-kaynağı değil) | **toolchain ✅ (colima+docker+lean 1.0.227 kuruldu 2026-08-10)**; C2-4 `lean init` QC-login-bloklu (§3) VEYA dotnet-CLI'sız L-boyut · **⑤ RETIRED 7/8 ✅ (§4)** · FREE fizibilite ②③④⑥⑦ · notebook koşumu (operatör §3) | `research/qc_dogrulama/` | EDG-2026-021/022 |
| **WP-UX** Yeniden-Tasarım | 🟡 frontend~bitti | pano yüzey/IA (D0-D6 ✅ §6; **F5 ✅ v230**) | frontend temiz-yetim AÇIK yok — kalan F-kartlar: backend(F3/F4/F11/F12) · zaten-yüzeyde(F9/F10/F13) · viz(F6/F7) · okuyucu-gerekli(F8→§2, F15) · D3-c: C2-1/2/3 ✅, **C2-4**(Task-4)/**C2-5**(operatör)/6.çalışma AÇIK | `web/app.js` · `api.py` | harita: §1 WP-UX detay |
| **WP-P** Pano/Operatör Arayüzü | 🟡 alarmlar bitti | kontrol-odası doktrini + RUNBOOK | **13 ALARM JETONU ✅ (2026-08-10): 12 kod-kanıtlı gerçek prosedür + GOAL_FAILURE dürüst-açık (operatör mandası); sentinel 31→16** · KALAN: 15 bekçi mekanizması + halt_learning (aynı desen, ayrı tur) | `docs/RUNBOOK.md` · `MERIDIAN_ENGINEERING_LOG.md` | — |
| **WP-L** Öğrenme/Ölçek Merdiveni | 📋 tetik-şartlı | meta-labeling → ML sıralama → Faz-6 BEŞ KİLİT | kodla açılabilir kilit YOK; işlem birikimi / evren genişlemesi / operatör bekler · Faz-6 INTRADAY_ARM operatörde (§3) | — | — |

### AKTİF WP DETAYLARI (tam metin — kapanan alt-kalemler ✅ tarihçe olarak korunur)

### WP-E — İcra Gerçekliği 🔴 ÖNCELİK YÜKSELDİ (2026-08-03 karne-tazeleme bulgusu; kart: EXE-2026-001)
- **BULGU (research/olcumler/karne_tazeleme_2026-08-03/):** güncel motorla geriye-dönük defter
  TERSİNE DÖNDÜ — replay net +2.493$→−1.182$, PARA-v3 0,1605→−0,0037, oos 0,0579→0,0196, n 201→147.
  TEK-DEĞİŞKEN ATIF: farkın TAMAMI E1 giriş-limitinin ATR bacağı (dolum 237→176; limit daralınca
  kaçan dolumlar kârlı girişler). Diğer adaylar ölçülüp elendi: replay-PIT 1 plan/0 skor · ısı-5R
  0 · fail-closed/turnover/kardeş-PIT yapısal 0. OKUMA: eski artı büyük ölçüde replay-dolum
  iyimserliğiydi; canlı-ödeme-0,97-vs-Search-1,53 payda-uyumsuzluğunun ana açıklaması bu (E4
  sorusunun yarısı kapandı). E1 varsayılan noktası (0,5·ATR, %1 tavan) ÖLÇÜLMEMİŞ bir seçimdi ve
  defteri çeviriyor → E1 grid ölçümü (0,25/0,005 · 0,5/0,01 · 1,0/0,015 + limitsiz-MOO kolu)
  programın EN ÖNCELİKLİ ölçümü; BT-1 beklemesi bu kalem için KALKTI — ve AYNI GÜN KOŞULDU:
  **E1 GRİD ✅ ÖLÇÜLDÜ (e1_grid_2026-08-03/): limit-bacağı MONOTON ZARARLI** (net$ A −7,2k · B −1,2k ·
  C −2,9k · LİMİTSİZ +2.957$/+1.959$-E3; kaçanlar sistematik kazanan; kill#1 yok; gap-bacağı
  replay'de yapısal-ölçülemez — canlı/gölge noktaları kayıtlı; skor-para ayrışması B/C kayıtlı).
  ~~KARAR OPERATÖRDE~~ **✅ KARAR VERİLDİ (2026-08-07, kart `EXE-2026-001-R2`, K += 1):** işletim
  noktası REF·limitsiz rejimi — `execution_v2` canlıda `limit_atr_mult: 100,0` / `limit_pct_cap:
  0,04`, yani limit tavanı hiçbir gerçek barda bağlamıyor ve bağlayan tek şey `MAX_ENTRY_GAP_PCT
  = %4`. Bu ÖLÇÜLMEMİŞ dördüncü bir nokta DEĞİL: grid'in `ref_limitsiz` kolu da (`1000·ATR/%10`
  → limit tetik×1,10 > max_chase tetik×1,04) tam bu rejimdi — sayılar farklı, DAVRANIŞ AYNI.
  Rol-1 bunu önce "kanıtsız sapma" diye okudu ve YANILDI; kanıt kartın kendi grid'indeydi.
  Canlı doğrulama (08-06, dört pozisyon): AMGN +1,78% · EMR +1,60% · BKNG +1,55% kovalandı,
  ödül/risk 2,50→1,50/1,76/1,90 indi; NUE tetiğin ALTINDA doldu (2,63). **Eski B noktasında bu
  dördün ÜÇÜ hiç açılmayacaktı** — ölçüm, atlanan işlemlerin maliyetinin kovalama aşınmasından
  BÜYÜK olduğunu söylüyor (`entry_missed_limit`: A 38 · B 23 · C 12 · REF 0).
  `counterfactual.advance` AYNI sabiti okuduğu için canlı ile cf hâlâ aynı stratejiyi ölçüyor.
  E2 defteri gerçek dolumla dolmaya devam eder; canlı-geçiş kapısında E2 kanıtıyla yeniden hüküm. Ayna-dolum akışının boşluğu (E2'nin öbür yarısı) ayrı teşhis kalemi. Şerhler raporda (bars_integrity dışlaması
  yok · survivorship · +0,018 replay-iyimserliği · cf-sadakat +0,039R).
- E1 iki-motor mutabakatı (iç MOO-tarzı vs ayna buy-stop GTC + gap-red kökü) + marketable stop-limit
  grid + gap-risk vetosu · E2 slipaj defteri (yüzey hazır, E1'e bağlı) · E3 kötümser maliyet bandı
  (açılış-spread ~20bps) → PARA-v3 net-kötümser sütun · E4 gece/gündüz PnL ayrıştırması (join;
  BT-1 damgası sonrası) · E5 gecikmeli-giriş A/B (E2 verisi sonrası, opsiyonel).
- EMİLDİ: eski Y2 TCA/shortfall defteri (=E2/E3) · canlı-TCA rezervasyonu (canlıya geçişte,
  denetim YÜ-1) · payda-uyumsuzluğu sorusu (canlı ödeme 0,97 vs Search-OOS 1,53 — E4+E1 açıklayacak).


### WP2 — Basit Referans-Verisi Adayları 🔓 KİLİT AÇILDI (2026-08-01 — EDGAR, operatörsüz)
- 2.4 EAP ✅ KAPALI (güç-yeterli). **2.1 ✅ ÇÖZÜLDÜ: SEC EDGAR companyfacts PIT verisi repo'da**
  (research/edgar_facts/; filed-tarihli — dei ilk-ifşa medyan 7 gün; 250/251 kapsam; FMP/operatör
  bileti DÜŞTÜ). **2.2 EDG-013 ✅ YAŞAYAN-ADAY
  (lafzen success: koşullu @20 +0,32% anlamlı + artımlılık; AMA tanı turnover ANA etkisini işaret
  ediyor → kaderi EDG-016'ya şartlı, entegrasyon bekliyor)** · **2.3 EDG-012 ✅ ARŞİV** (yön ters+
  anlamlı, U-eğrisi; REIT/büyüme yapısal) · **2.5 EDG-014 ✅ ARŞİV** (bilgisiz; finans-dışı da) —
  "PIT'siz ASLA" yasası filed-tabanlı as-of ile İLK KEZ meşru sağlandı · **2.6 EDG-016 ✅ SUCCESS —
  YENİ YAŞAYAN SİNYAL: turnover ana-etkisi** (@20 net +0,55% CI-0-dışı; artık üç yöntemle sağ;
  q5 monoton; survivorship-şerhi kalıcı). 2.2/EDG-013 arşive DEVREDİLDİ (etkileşim-tezi düştü).
  ~~SIRADAKİ ADIM 📋: turnover kablolama~~ → **✅ ZATEN İNMİŞ (`5dfca07`, log:414 2026-08-03 dalgası) —
  2026-08-10 doğrulama turu sözleşmeyi kaynak-doğruladı (58/0):** indicators.py:156 `turnover21` (kart
  formülü birebir) · strategy.py:452 bileşik-skor terimi (w_to>0 ∧ not-None; ölçülemeyende FAIL-OPEN) ·
  `entry.w_turnover` bounds.yaml:46 {0–0.40}, strategy.yaml TAŞIMIYOR → canlı etki 0 (default-0 bit-bit
  regresyonlu, test_turnover_kablolama_v149) · gölge-okuyucu üç kanal (component_ic + hermes arama-uzayı
  [canlı ret kanıtı: `hermes_bg_proposal_rejected variable=entry.w_turnover`] + shadow_variants). Bu tur
  ROADMAP bayattı, kod gerçeği önde — kalem KAPANDI; **WP2'de kablolama borcu kalmadı** (öğrenme ölçer).


### WP-U — Evren/PIT Cephesi 🔶 (araştırma indi 2026-07-31; stratejik ana cephe)
- **ÜYELİK ÇÖZÜLDÜ (ücretsiz):** S&P500 tarihî üyelik 1996→bugün repo'da
  (`research/pit_universe/sp500_uyelik_tarihi.csv`, 2.719 satır, MIT — fja05680). S&P400/600 için
  hazır ücretsiz set BULUNAMADI (yfiua desteklemiyor — araştırma iddiası düzeltildi); alternatif:
  SEC 13(f) resmî listesi (2004Q1→, likidite-evreni; CUSIP→ticker emeği).
- **SERT KISIT (2026-08-02 SAYILANDI — EDG-018 kapı ölçümü):** delist-bar boşluğu ölçüldü:
  endeksten çıkmış 703 ismin yalnız 12'si arşivde barlı (%1,71); EDG-016 panel-penceresindeki
  çıkışların **%96,57'si SIFIR bar** (338/350) ve 12 barlının hepsi 2024+ (ikinci-seçilim).
  Survivorship şerhi artık kapsama-yüzünde sayı; iki yaşayan sinyalin büyüklüğü delist-bar
  kaynağı gelmeden ölçülemez — operatör kararının fiyat-etiketi bu. Kanıt:
  research/olcumler/wp_u_midcap/. EDG-018 askıda:veri-kapısı. Yollar (2026-08-03 QC-araştırmasıyla YENİDEN ÇERÇEVELENDİ —
  docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md): iki yol RAKİP DEĞİL TAMAMLAYICI. (a) QC platform-içi
  ölçüm hattı — BEDAVA, BUGÜN (EDG-021 deseni kalıcılaşır; ToS verinin dışarı çıkışını kilitler,
  içeride ölçüm serbest); (b) Massive yükseltme — YEREL ARŞİVİN tek meşru yolu (operatör kararı;
  QC bunu ikame edemez — 'internal LEAN use only').
- **⚠ OPERASYONEL BULGU (canlı sondaj):** mevcut Massive planı artık yalnız ~SON 2 AYI veriyor —
  2004'e giden yerel bar arşivi yeniden üretilemez KALINTI; arşiv kaybı = kalıcı kayıp → yedek
  zinciri kritikliği ↑ (VM-içi tar + Mac-pull mevcut; üçüncü kopya değerlendirilebilir).
- Sonrası: PIT-evrenli G1 mid-cap ölçümü (üyelik verisi hazır; bar kısıtı yalnız delist-isimleri
  etkiler — sağ-kalan mid-cap'lerle ÜST-SINIR ölçümü yine mümkün, yanlılık beyanlı) → B-9 (tetik:
  trend kolu ship) · 13F önceliklendirme katmanı.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-U-2026-08-09.md`, salt-ölçüm + plan):** canlı evren **251 =
  REPLAY_UNIVERSE** (aynı küme, fark YOK — "251" zaten `REPLAY_UNIVERSE`'ün kendisi). FINVIZ evren-
  genişletme kolu **%100 ÖLÜ** — `finviz_unavailable` **3.746** / `finviz_universe` (başarılı keşif)
  **0** (2026-07-14→08-09), `FINVIZ_API_KEY` YOK → evren kalıcı 251. **RAKİP KÖK:** de-risk rampası
  günlerin **%92**'sinde pozisyonu 1'e kısıyor (ROADMAP:425) → **"evren +X → işlem +Y" ÖLÇÜLEMEDİ**
  (bilerek uydurulmuyor: aday-havuzu mu, tavan mı bağlıyor belirsiz). ÖNERİ **EDG-2026-022** ("Evren
  bağlayıcı kısıt mı?" — OTONOM/bloksuz; altyapı hazır: `backtest.py` candidate_log + eff_max_open +
  plan_log; yeni bar GEREKMEZ): FINVIZ harcamasını **DE-RISK eder** (evren bağlamıyorsa para boşa).
  PIT fundamentals **EDGAR'la ÇÖZÜLÜ** (evrene bağlı otonom kol, blok değil). Delist-bar: 703 çıkıştan
  yalnız 12'si arşivde barlı (%1,71); EDG-016 penceresi %96,57 sıfır-bar (kaynak kararı §6-9'da).


### WP-S — Sermaye/Defter Bütünlüğü + Koruma 🔴 AKTİF (2026-08-07 gecesi; kaynak: canlı risk turu)

**BU WP'NİN DOĞUŞ SEBEBİ:** 2026-08-06 gecesi dört motor pozisyonu KORUMASIZ kaldı ve sistem
bunu fark etmedi. Kök turları üç ayrı kusur ailesi çıkardı; üçü de aynı sınıfın örneği —
**sistem doğru çalışıyor ama kendini yanlış anlatıyor.** Ayrıntı: `docs/KORUNUM-KOK-2026-08-07.md`,
`docs/BAYAT-SERMAYE-KOK-2026-08-07.md`, kartlar `EXE-2026-001-R1/R2`, `EXE-2026-002` (+R1).

- **✅ KAPANDI — koruma×süpürücü çarpışması KÖK DÜZELTME (v220+v221, 2026-08-09, CANLIDA ARTEFAKTTAN DOĞRULANDI):**
  süpürücü (`cancel_open_entries`, alpaca.py:481-487) korumayı artık YAPISAL tanıyor — **iki kemer,
  tek hüküm noktası:** limit bacağı P-KORUMA AİLE kemeri (`KORUMA_COID_ONEK` öneki, v220) + stop
  bacağı OCO GRUP kemeri (grup üyeliğinden türer, yön değil — v221); ayrıca long-only YÖN kemeri
  (satış-yönlü emir giriş olamaz). Koruma sınıfı emir `kept`e `sinif:koruma` gerekçesiyle düşer —
  süpürülmez. KANIT: `alpaca.py` yerel↔canlı md5 BİREBİR (`549b78e…`); broker'da **4 açık koruma
  OCO'su** (`P-KORUMA-20260809-0835-{NUE,EMR,BKNG,AMGN}`, gtc, sınıf=koruma, accepted/held);
  dağıtım #4 korumayı BOZMADI. Operatör 08:35'te panodan onayladı (İLK deneme tarayıcı önbelleğinden
  ulaşmadı — sıfır POST izi; İKİNCİ geçti). **AÇIK-DAVRANIŞSAL:** fixli süpürücü GERÇEK bir EOD
  süpürmesinde HENÜZ koşmadı (piyasa Cuma'dan kapalı) — mantık+md5+broker doğrulandı, ilk davranışsal
  kanıt Pazartesi 13:30 UTC sonrası (`docs/SABAH-TRIYAJI-2026-08-09.md` §0/§iv). "Bir kalem ancak
  artefaktı canlıda doğrulanınca ✅" dersi TUTTU — bağlamsız N6 devir tatbikatı önceki "✅ KAPANDI"
  beyanının yalanını ARTEFAKTTAN yakalayıp bu çarpışmayı yeniden açmıştı.
- **~~⟳ YENİDEN AÇILDI (2026-08-09, N6 tatbikatı buldu — kapanış ARTEFAKTTAN doğrulanmamıştı)~~ → yukarıda ✅ (tarihçe):**
  operatörün v211'le kurduğu 4 bağımsız koruma OCO'su (coid `P-KORUMA-…`) 2026-08-07T20:32:39Z'de
  `cancel_open_entries()` tarafından SÜPÜRÜLDÜ — koruma emri süpürücünün gözünde "dolmamış motor
  girişi" (P- öneki + açık + filled_qty=0); "koruma bacağına dokunmaz" güvencesi yalnız BRACKET'A
  BAĞLI bacağı tanıyordu, v211'in bağımsız OCO'su o fonksiyon yazılırken yoktu. Broker'da 0 açık
  emir / 5 korumasız pozisyon; 16 sev-1 alarmı kanalsızlıktan teslim edilemedi. KÖK DÜZELTME
  ~~UÇUŞTA~~ İNDİ (v220: yön kemeri + P-KORUMA aile dışlaması + olay coid-sınıfı + idempotans
  çivisi; v221: OCO grup kemeri). DERS ROADMAP DİSİPLİNİNE: bir kalem ancak ürettiği artefakt
  canlıda doğrulanınca ✅ olur.
  (Önceki metin aşağıda, tarihçe olarak duruyor:)
- **~~✅ KAPANDI~~ — koruma ölmüyor (E1-v2, v209-v211, canlıda doğrulandı):** bracket TIF'i emrin
  TAMAMINA uygulanıyordu; `day` seçimi dolmuş pozisyonun stop'unu her kapanışta öldürüyordu
  (ölçüm: 08-06 20:00-20:02Z, dört pozisyon çıplak). TIF `gtc`, `day` beyaz-listeden ÇIKARILDI
  (`ENTRY_TIF_ALLOWED`), bayat tetik günlük `cancel_open_entries()` kadansına taşındı. v209
  koruma bekçisi (300 sn, sev-1, payda-beyanlı) + v211 operatör-onaylı OCO yeniden-kurma yolu.
  Operatör 08-07'de panodan onayladı; dört pozisyonda OCO/gtc doğrulandı.
- **✅ SB-4 — DAMGASIZ YAZIM BEKÇİSİ (KAPANDI v216, dağıtım #2 — içerik-sha≠damga parmak izi, 08-04 fikstürlü; Rol-1 önerisiydi, EN ÖNCELİKLİydi):** ölçüldü ki `portfolio.json`
  `store` kapısı DIŞINDAN değişebiliyor — 08-04'teki kitap yazımında `entity_meta.rev` hiç
  ilerlemedi (o gün yalnız iki `_save_broker`, ikisi de kanıtlı). Yani denetim zincirinin bir
  deliği var ve bugün onu gören hiçbir şey yok. Tasarım: tur başı/sonu `entity_stamp` kıyası →
  "kitap bu tur DIŞARIDAN değişti" alarmı. **Bu kalem bir sermaye kalemi değil, bir DENETİM
  kalemidir** — kitap izsiz değişebiliyorsa hiçbir sermaye ölçümü kendi tabanına güvenemez.
- **✅ SB-3 — `taban_kaymasi` satırı (KAPANDI v216 — ters-onarım gerilemesi çivili; en ucuzdu, SB-4'ten hemen sonra):** `recompute`e dördüncü satır
  `realized_pnl − (Σ trades + ofset)`; + `monotonicity_report` tabanına beyan ölçüsü. 08-04
  vakasında bu satır olsaydı ters onarım ANINDA görünürdü.
- **✅ SB-1 — plan başına BOYUT MAKBUZU (KAPANDI v222 `_save_broker` 14. anahtar `size_law` + v226 pano-bacağı `_yama` kalıcılık, dağıtım #4):** `eq_kaynak` (eq_now|nabiz) · `eq_now` · `peak` ·
  `size_mult` · `kitap_rev` · `beyan_n/ofset`. `entry_law` deseniyle, `_save_broker`ın 14. anahtarı;
  reddedilen planda da yazılır. v226 `api.py._yama` bacağı makbuzun restart'ı atlatmasını sağladı
  (loop bacağı zaten kalıcıydı, eksik olan pano/nabız bacağıydı — 08-06 AMGN vakası).
  Gerekçe: 08-05 sapmasını çözmek üç ayrı deftere bakmayı gerektirdi; makbuz tek satırda söylerdi.
- **📋 SB-2 — `MIRROR_DRIFT`e `drift_sinifi` alanı:** `boyutlama_tabani` / `derisk_carpani` /
  `sermaye_kaynagi` / `kitap_kaydi` / `beyan_kaydi` / `icra` / `olculemedi`. Ölçülen gerekçe:
  08-05 gecesi DÖRT MIRROR_DRIFT alarmı bastı ve HİÇBİRİ sebebi adlandırmadı — belirti görüldü,
  sınıf söylenmedi. Aynı jeton koruma alarmıyla da paylaşılıyor (6 saatlik susturma penceresi
  ortak) → ayrı `NAKED_POSITION` jetonu operatör kalemi (obs.py NOTIFY_TOKENS, bir satır).
- **ÖLÇÜLEMEDİ (kapanmadı, beyanlı):** 08-04 kitap yazımını KİM yaptı. Kanıtın yokluğu ölçüldü
  (damgasız). Dışlananlar: replay_seed · iade betiği · ikinci `sermaye --uygula` · migrated
  kopyası · dağıtım/restart/litestream · hermes/api/arm yamaları. SB-4 bu soruyu GELECEKTE
  cevaplanabilir kılar; geçmiş vaka için kanıt yok ve uydurulmayacak.
- **🔒 OPERATÖR — melez pozisyonlar:** iç defter 54/64/43/33, ayna 25/37/22/22 (ayna hedef riskin
  ~%49'unu taşıyor; taban yerinde olsaydı 51/76/45/45 giderdi). Korumalar DOĞRU tarafa (broker
  adedine) kuruldu. Farkın kapatılıp kapatılmayacağı operatör kararı.
- **🔒 OPERATÖR — uyuyan kurulum yolu:** `dormant_setup` 31 plan üretti, **0 işlem** çıktı, biri
  GO hükmü aldı ve yine işleme dönmedi (kapı geçirdi, arkasında tüketen yok). `conservation.
  unexplained = 14` = 31 uyuyan − 17 NO_GO; hesap tam kapanıyor. İcraya bağlamak SİSTEMİN NE
  ALIP SATTIĞINI değiştirir → ön-kayıt kartı + kill-list gerekir. Seçenekler: (a) icraya bağla,
  (b) tavsiye kalsın ama kapı GO vermesin, (c) geri al. Gözlemlenebilirlik tarafı (terminal
  olay · `dormant_unconsumed` ayrı kovası · panoda payda-beyanlı `0/31`) otonom yapılabilir.


### WP-S2 — Ölçüm/Görünürlük Borçları 📋 (2026-08-07; hepsi BEYANLI, hiçbiri sessiz değil)
- **kill#4 uygulama borcu (kart `EXE-2026-002-R1` ön şartı):** kod eşleşmeyenleri ZATEN
  `sinif_dagilimi` ile ayırıyor (`eod_yok`/`golge_bozuk`/`bps_yok`); kill kapısının yalnız
  BOZULMA sınıflarına daraltılması ayrı tur. Bugün fark yaratmıyor (oran %0), o yüzden acil değil
  — ama `eod_yok` biriktiği gün ölçüm haksız yere susar.
- **✅ `k.olcum` panoda ÇİZİLİYOR (KAPANDI v219 — "beş kilidin `olcum`'u nihayet çiziliyor").** Borç neydi: `app.js`
  yalnız `k.esik` + `k.neden` okuyordu; tam yük `/api/diagnostics` JSON'ında SERVİS EDİLİYORDU ama çizilmiyordu.
  Faz-5 turunda karar sayıları `neden` metnine yazıldı (operatör "4/20"yi görüyor) ama bu bir
  yamaydı; kilit ölçümlerinin kendi kartı yoktu. v219 beş kilit için `k.olcum`'u çizdi (eski
  "beyan bayatlamasın" testi — `"k.olcum" not in appjs` — pano okumaya başlayınca güncellendi).
- **✅ app.js 409-yutması (KAPANDI v219 — boş `catch` 6→0):** borç neydi: `apiFetch` 4xx'te throw etmiyordu,
  `applySkillRec` boş `catch` ile yutuyordu → L1'de onay-kapısı reddi PANODA GÖRÜNMEZ oluyordu
  (operatör basar, hiçbir şey olmaz). Mekanizma düzeyinde YASA 4 zaten tamamdı (olay+gerekçe defterde),
  operatör yüzeyinde değildi. v219 boş catch'leri 6→0 indirdi; N5 app.js turunun parçası.
- **✅ `EV_TR`de `koruma_*` + süpürücü çevirileri (KAPANDI v219 dokuz olay çevirisi + v225 opCancelOpen `siniflar` dökümü):** borç neydi: v209/v211 olayları panoda HAM olay adıyla görünüyordu
  (tam alanlar tıklanan çekmecede). v219 dokuz olayı ÖLÇÜLMÜŞ adlarla cümleye çevirdi; v225 pano
  `opCancelOpen` sonucunda süpürücü sınıf dökümünü (giriş/koruma/yabancı) + 4 süpürücü olay
  çevirisini gösteriyor. N5 app.js turu.
- **Faz-5 örneklem (kendiliğinden dolar):** kilit artık `durum: olculdu` · "ÖRNEKLEM YETERSİZ
  (4/20)". Nokta tahmini −9,69 bps ama `n_kume=1` (dört dolum tek gün) olduğu için CI
  HESAPLANMADI ve `sifiri_disliyor: null`. Kill#2 ancak n≥20 VE CI tamamen negatifken işler.
  Bu kalem KOD İSTEMEZ, İŞLEM İSTER.
- **"BEYAN VAR, ÜRETİCİ/TÜKETİCİ YOK" sınıf taraması (2026-08-07 operatör sorusu üzerine;
  grep-turu yapıldı, sistematik tur AÇIK):** Faz-5 kilidi bu sınıfın bir örneğiydi ("üreten kod
  yok") ve kapandı. Grep'in bulduğu KALAN örnekler: ① `docs/RUNBOOK.md` 31 girdi "henüz
  yazılmadı" (görünür-bilinçli ama borç gerçek) · ② hermes çağrı telemetrisi — veri `/api/hermes`te
  AKIYOR, pano kartı YOK (`hermes.py:2503`, D3-UI kalemi; `k.olcum` borcuyla aynı aile) ·
  ③ cf çıkış-yasası sapması (`analytics.py:1380`): 6 çıkış tipi cf'te modellenmiyor, ölçülmüş
  iyimserlik +0,039R, cf satırları skor havuzunun %96'sı — "ayrı turun işi" denmiş, tur hiç
  açılmamış. DÜRÜST (iş gerektirmeyen) dallar ayrıldı: E3 ampirik bandı ve `_olcut(olculemedi)`
  dalları örneklem bekliyor, sabit taş değil. SINIR BEYANI: grep yalnız İTİRAF EDİLMİŞ borcu
  bulur — bugünün en tehlikeli vakaları (uyuyan-yol tüketicisizliği, koruma yeniden-kurma
  yolunun hiç olmaması) BEYANSIZDI ve `codelaw.artifact_graph`tan da kaçtı (defter yazılıyordu,
  okuyucusu vardı; eksik DAVRANIŞSAL tüketiciydi). Sistematik tur = artefakt/bayrak envanterini
  yürüyüp her birine "üreticin kim, seni kim OKUYOR, okuyan DAVRANIYOR mu?" sormak.
- **✅ SİSTEMATİK TUR KOŞULDU (2026-08-07 gece, dördüncü kova — `docs/ARTEFAKT-TARAMASI-2026-08-07.md`,
  551 satır):** 107 artefakt + 5 bayrak + 53 config anahtarı + 13 kapı-dışı kalem. KALİBRASYON
  KAPISI 3/3 — ama İKİ YÖNTEM ONARIMINDAN SONRA (ilk koşu 1/3; alan-düzeyi merceği + taint
  yayılımı eklendi; raporda beyanlı). Sayım: `davranissal` 92 · `yalniz-gorunurluk` 14 (13 meşru,
  1 şüpheli) · `tuketicisiz` 1 · `ureticisisiz` 0. Sistem BÜYÜK ORANDA KABLOLU — bulgular kenarda:
  (NUMARALAMA NOTU: buradaki B-1..B-7 TARAMA bulgularıdır; WP-S'teki B1-B4 bayat-sermaye turunun
  BEKÇİ önerileridir — iki ayrı dizi, çakışma tesadüfi. Bekçi dizisi bundan sonra SB-1..SB-4
  diye anılır.)
  · **✅ B-1 (KAPANDI 426b998):** `goal.yaml`'da 4 beyansız ölü düğme (`backtest_gate`/`session_tz`/`style`/
    `schema_version`) — tek eşleşme `guard.py:15-17 GOAL_KEYS` üyeliği, değeri kimse okumuyor.
    K1'in (2026-07-30) bulduğu `explore_rate`/`kill_switch_file` sınıfının kaçmış dördü.
    `backtest_gate: true` en ağırı: kapı sözü veriyor, davranış yok. Rol-1 doğruladı.
  · **B-2 (YÜKSEK → İKİ ALT İDDİA ÇÜRÜDÜ, ÇEKİRDEK DOĞRU ÇIKTI VE KAPANDI, v214):** "9 çağrı
    grafikte yok" YANLIŞTI (dokuzunun biçimi zaten çözülüyordu — filtre tabanı sorgulamıyordu);
    "massive_verify haritada yok" YANLIŞTI (hep oradaydı). DOĞRU çekirdek: tarayıcı ÇÖZEMEDİĞİNİ
    SAYMIYORDU — gerçek kör sınıf `store.py` içi 6 çıplak-ad çağrısıydı. Kapama: her erişim ya
    çözülür ya adlandırılmış `UNRESOLVED_REASONS` kovasına düşer + `access_patterns` census;
    unresolved 15→21 (körlük görünür oldu). Rapora DÜZELTME bloğu eklendi; ders: kalibrasyon
    yalnız bilinen-pozitifleri sınıyordu, bilinen-NEGATİF kapısı da gerekir.
  · **✅ B-3 (KAPANDI 426b998, K1 deyimiyle beyanlandı):** `one_variable_only` YAPIŞIK düğme — kural koşulsuz (`guard.py:134`), anahtar
    yalnız hata METNİNDE geçiyor; kapatılamaz bir şeyi düğme gibi beyan ediyor. Rol-1 doğruladı.
  · **✅ B-4 (KAPANDI d1c40e9, v214 `stale_claims()`):** `sieve.json` muafiyet beyanı BAYAT'tı — "tek okuyucusu kendi testi" diyor, oysa
    `api.py:3202→2232` üzerinden TERFİ HÜKMÜNE giriyor; `stale_sinks` bunu yapısal göremiyor.
  · **✅ B-5 (KAPANDI 4d09028, Rol-1 hükmü: yazım SÖKÜLMEDİ):** `state/intraday_bars/<gün>.jsonl` ölü yazımdı (canlı sıcak yolda her
    dakika) — tarihli f-string ad DECLARED_SINKS'e giremiyor; mimari karar Rol-1/operatörde.
  · **✅ B-6 (KAPANDI f253929, v215) / ✅ B-7 (KAPANDI 4d09028):** `approvals.jsonl` onay defterini hiçbir kapı okumuyordu (uyuyan-yol ailesi, L1'de
    patlar) · `shadow_trades.jsonl` tek tüketici bir CLI bayrağı.
  · Taze canlı sayım: uyuyan plan 31→**32** (0 işlem, 1 GO — oran değişmedi). ÖLÇÜLEMEYENLER
    raporda adıyla (7 kalem; en önemlisi: KATMAN-4 alan merceği yalnız `dormant_setup`a
    uygulandı, plan defterinin ~20 kontrol alanı BİR SONRAKİ KOVANIN konusu).
- **✅ ÖLÜ-MEKANİZMA AVININ BEŞİNCİ KOVASI KOŞULDU (2026-08-09 gece — `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md`):**
  dördüncü kova TÜKETİCİSİZ YAZIM (ölü kopya) avlamıştı; beşincisi ÇOK-YAZARLI GERÇEK (ayrık kopya)
  avlar — "aynı gerçeği başka kim bildiğini iddia ediyor, o kopya bugün ne diyor?". 22 gerçek-ailesi
  yüründü, kalibrasyon İLK KOŞUDA 3/3 ve iki-yönlü kapı iki yanlış-pozitifi fiilen durdurdu
  (commit `f456b56`). Salt ölçüm+belge; `meridian/` altında dosya değişmedi.

- **🆕 YENİ AÇIK KALEMLER (2026-08-09, devir tatbikatı + sabah triyajı hasadı — `docs/SABAH-TRIYAJI-2026-08-09.md`):**
  · **systemd `daemon-reload` (P2, kanal-açılışında P1):** `SuccessExitStatus=143` birim dosyasına
    YAZILDI (v225) ama CANLI systemd hâlâ boş `SuccessExitStatus=` ile koşuyor — birim dosyası
    değişikliği reload+restart bekliyor ("kurulu ≠ çalışır" doktrini). N1 bildirim kanalı açılmadan
    ÖNCE inmeli, yoksa her restart "FAILED" sayılıp OnFailure bildirir. Bakım penceresi + elle
    test-ateşleme. *Kalem 1 (SABAH TRİYAJI en ucuz + kanal-kapılayan).*
  · **skill görüş canlı-kanıt (P3, ölçüm-borcu):** N2b/EDG-2026-019 kod indi (v218) ama R-figürleri
    kuru-koşu (`eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi); birkaç EOD penceresi +
    EDG-2026-019 ölçüm kodu bekliyor.
  · **ajan-git MEKANİK kapısı (P2, süreç/araç kararı — operatör):** gece 2 ajan `git stash` koşup
    hasar verdi (hayalet dizin süpürüldü). Yasak yalnız CLAUDE.md sözleşmesi; `dagit.sh` yalnız
    DAĞITIMI kapıyor. `git stash`ın pre-stash kancası YOK → kapı ancak PATH-shim/wrapper'la
    mekanikleşir. Karar operatörde.
  · **kill#4 uygulama (AÇIK — yukarıdaki borç):** kill kapısının yalnız BOZULMA sınıflarına
    daraltılması (kart `EXE-2026-002-R1`); bugün etki %0, `eod_yok` biriktiği gün ölçüm haksız susar.
  · **SB-2 `drift_sinifi` (AÇIK — WP-S):** MIRROR_DRIFT alarmına sebep-adlandırma alanı; 08-05'te
    dört alarm bastı, hiçbiri sebebi söylemedi.


### WP-M — Metodoloji/Yasa Borçları 📋 (ölçüm altyapısının kendisi)
- **YENİ (EDG-010'dan, ders #3): ölçütler HAM getiri okuyamaz** — success/kill her zaman
  taban-fazlası (aynı-gün evren / ilgili alt-evren) üzerinden yazılır; ham pozitiflik piyasa
  sürüklenmesidir (EDG-010 vakası: lafzen-success, kanıten-kenarsız).
- **YENİ (EDG-009'dan): kart eşik-DİLBİLGİSİ standardı** — success/kill metinlerinde her dal
  KENDİ niteleyicisini açıkça taşır ("artar (CI 0-dışı)" gibi); belirsiz niteleyici = muhafazakâr
  okuma + karta ders notu (EDG-009 vakası: "(P>=0.95)" hangi dala ait belirsizdi, hüküm değiştirici).
- **YENİ (WP-G tanısından, SINIF bulgusu): "oosonly" kolu STANDART** — walk_forward tek-parça
  replay koştuğu için IS'e dokunan HER overlay/knob OOS skorunu portföy-durumu kanalıyla
  (peak_equity/derisk/açık pozisyonlar) kirletir; bundan böyle knob ölçümlerinde knob'u
  oos_start'ta devreye alan kol zorunlu (kanıt: EDG-005 tanısı — oosonly≡kapali bit-bit).
- ~~PARA-v3 ①②~~ ✅ (①: 2026-08-01 + zincir-çivisi v178; ②: 2026-08-02 kapı-bacağı — ölçülür,
  veto-bağlamaz [MERIDIAN_DD_MTM_VETO kapalı; bağlama = M2M-σ ölçüm kartı]). ÜÇ KAYIT DA KAPANDI (2026-08-03 uygulama dalgası):
  (i) ✅ probgate birim-karışımı — teşhis: mekanizma muhafazakâr değil ÖLÜYDÜ (para-v3 altında
  yeni çift sayılamaz, extra_p yapısal 0). Rol-1 kararı SEÇENEK-1: rollback para-ikizi
  (realized_detail.delta_para, tek payda span; hüküm BİLEŞİK kaldı — eşik satırı çivili) +
  damga BEYAZ-LİSTESİ (bilinmeyen damga sayılmaz — para_v4-dirilme sınıfı ölü, negatif testli)
  + durum alanı {olculdu/kurak/askida_olcek_borcu} (extra_p askıda/kurakta 0,0 kalır); watchdog
  askıda≠starved ayrımı. 17 yeni test + 169 regresyon. AÇIK KUYRUK: hermes.py:644 ship_calibration
  askıda-durumu beyne taşımıyor (ayrı tur). (ii) ✅ canlı gate_calibration izlemesi — yeni koşumda
  durum alanıyla kendini beyan eder. (iii) ✅ DD_VETO_MARGIN okuma netliği — ledgers sözleşme notu
  (dd_mtm_* ailesi dahil) + analytics._dd_veto_okumasi ölçülü-oran (marj/tavan her çağrıda; mutlak
  çıpa goal.max_drawdown) → pano YASA-6 zinciri api.py:2279. · 2B blok-bootstrap CI standardı · 2C empirical-Bayes küçültme ·
  2D R2 holdout rotasyonu (zamanı gelince) · A4 tahmin-isabeti bandı · KIYAS-KİRLENMESİ düzeltmesi
  (olay-penceresi-dışı kıyas — EAP yan bulgusu; tüm evren-medyanı ölçümleri etkileniyor) ·
  prescreen raporlarına kod-sürümü damgası · PK4/PK5 yol-tutarlılık kontrolleri ölçüm-şablonu
  standardı · K-defteri↔kart senkronu (retro kartlar) · ~~canlı-beklenti tavanı config'e bağlama~~ (2026-08-03 TEYİT: 5fe0c1e'de ZATEN kablolu —
  config.live_expectancy_rule + analytics.live_expectancy_ceiling → pano; kayıt bayattı) · Chen-2022 t-hurdle dengeleme notu (K-cezası
  kalibrasyonu — gevşetme değil referans).
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-M — salt-ölçüm; gece kapananlar v196/v214/
  kart-tekillik düşülmüş):** **11 kalem gerçekten açık** (9 metodoloji/yasa + **PBO/DSR tabanı** [M2,
  M2: damgalama ARTIK ÇALIŞIYOR — kanonik canlı `validation_ledger` **383 satır = 204 damgasız (R1-öncesi,
  retro-damga yasağı gereği sonsuza dek None) + 179 R1-damgalı (R1-sonrası TÜM yeni satırlar)**; oos_erosion
  4 pencere R1 (2026-08-10 Rol-1 salt-okunur canlı ölçüm; önceki gece "831/833" SAYIM HATASIYDI — sprint-sandbox
  kopyalarını da sayıyordu, düzeltildi). Eski "0/204 → NO-OP" dönem bitti: yeni akış %100 damgalı → **M2
  restart-bloğu KALKTI**; kalan otonom = R1 popülasyonunda PBO/DSR taban HESABI (ölçüm kodu → KART gerekir)] +
  **araç-kör-nokta artığı** [M11: KATMAN-4 alan merceği plan defterinin ~20 kontrol alanına genişlemedi]).
  EN YÜKSEK KALDIRAÇ = **M1 KIYAS-KİRLENMESİ** (olay-penceresi-dışı kıyas — TÜM evren-medyanı ölçümlerini
  etkiliyor; yeni WP-K aile ölçümlerinin tabanını temizler). Öneri sıra: bakım penceresinde OB-2 systemd
  → OB-1 kanal → OB-4 restart→PBO damgalama (M2) çapraz-kaldıraç; sonra M7/M8/M9 ucuz, sonra M1 çekirdek.


### WP-D — Veri Bütünlüğü 🔄
- **BULGU-1 ✅ TEYİT-TAM (2026-08-03 bağımsız yeniden-üretim — kanıt research/olcumler/
  wpd_bulgu1_teyit/):** 4/4 vaka bugünkü kapıda KARANTİNA; evren geneli birebir (259 defter /
  1.343.892 satır / yeni-kural 13 yakalar, eski 3); yeni kaçak %0 → karantina-genişletme kalemi
  KAPANDI (uygulanacak kaçak yok). DÜZELTME: eski kaçak payı %29 değil **%77 (10/13)** — sayı
  doğru, pay yanlıştı.
- **bars_integrity ✅ ZATEN-SEVK (2026-07-31 adapters/data.py; teyit 2026-08-03 —
  wpd_bars_integrity_teyit/):** defter 98 kırılma/61 sembol (eski "97" düzeltildi); kanonik
  tüketiciler (component_ic/cf_backfill/trend_shadow) kablolu, 46.256 satır/57 sembol dışlanıyor,
  ayrışma 0; 26 test yeşil. AÇIK BİLET (operatör kararı): `dataset.load` bilerek bağlanmadı —
  walk-forward/prescreen/reflect kirli dönemi hâlâ görüyor.
- türetilmiş
  artefaktların (component_ic/cf/eşik eğrileri) güvensiz-dönem-dışlamalı yeniden üretimi ·
  BMO/AMC alanının ileri-birikimi (data.py `time` alanı — EAP öldü, kalan değer blackout
  hassasiyeti; DÜŞÜK öncelik) · earnings kapsaması 194/251 + fail-open daraltma · 5.3 seans-içi
  kesinti/boşluk tespiti · ~~earnings 2-gün marj~~ (2026-08-02 KEŞİFLE KAPALI: aaa7a40+653c121 türetimli çözmüş, marj=9g, çivi v147'de).


### WP-H — Mühendislik Dayanıklılığı 📋 (2026-07-31 el kitabı turu; kaynak: operatörün 2024-26
araştırma anketi — bizim gerçekle çarpıştırılmış hali. İlke: "AI mevcut disiplini AMPLİFİYE eder;
kapılar+geri-alınabilirlik önce" — bizde kart/yasa/çivi disiplini VAR, eksik olan sürüm kontrolü.)
- **ZATEN VAR (el kitabı istiyor, bizde karşılığı):** wide-event/run = `daily_cycle` olayı ·
  canary/shadow = gölge-v2 + paper-lock · DST-lite yarısı = replay_seed + deterministik backtest ·
  snapshot testleri = çivi dizisi · yedek zinciri = VM-tar + Mac-pull · takvim/UTC = takvim kapısı ·
  iç dead-man = 17 bekçi + tick-watchdog + fail-notify.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-HD-2026-08-09.md`, salt-ölçüm — WP-H + WP-D):** WP-H çekirdeği
  büyük oranda KAPALI; kalan tek adlı OTONOM iş = **H9 Kademe-B ~11 kapı-dışı yazımın** `store.write_text`/
  kilitli-append'e taşınması (kapı HAZIR `store.py:306`). En tehlikeli tekil: **`auth._write` SABİT-TMP-
  ADI** (`auth.py:87-96` — iki süreç aynı `.json.tmp`'ye yazar, atomiklik iddiası biter); sonra kırpma-
  sınıfı düz yazımlar `memory.py:212` lessons.md + `run.py:172` scoreboard. systemd `SuccessExitStatus=143`
  birim dosyasında YAZILI (`meridian.service:82`) ama **CANLIDA DEĞİL** — A1 /etc birimi 08-02 tarihli,
  her restart exit-143 ile "FAILED" (son 3 günde 6 kez, fail-notify NO-OP kurtarıyor); **N1 bildirim
  kanalının ÖN-ŞARTI** (daemon-reload + bakım penceresi + elle test-ateşleme — §6). H10 aşama-2 = saf
  OCI-bucket operatör-bloğu (§6-10). **WP-D'de otonom kod deliği KALMADI gibi** (bars_integrity sevk+
  kablolu, seans-içi boşluk dedektörü kurulu); açık kalan iki kalem OPERATÖR-bloklu (`dataset.load↔
  bars_integrity` bağlama = kapsam kararı + FMP planı). POZİTİF: E2 defteri kilit-8 kod düzeyinde kapanmış görünüyor.
- **H1 Hypothesis invariant paketi ✅ (2026-07-31 tur-2):** 20 property / 5 yasa bölümü (sanitize,
  depo-roundtrip diferansiyeli, kayıpsızlık durum-makinesi, takvim kapısı, defter damgası).
  İLK GÜN GERÇEK KUSUR: SQLite REAL −0.0 işaret kaybı (latent, canlıda 0 örnek; _isaretli_sifir
  kapısıyla kapandı, @example kilitli) — property-testin varlık gerekçesi kendini ödedi.
- **H2 tedarik-zinciri kapısı** ✅ 2026-07-31: `uv audit` temiz (69 paket, 0 zafiyet); dağıtım
  betiğine zorunlu ön-adım olarak kablolu (`dagit.sh` [0/6]) — ajan-önerili her yeni bağımlılık
  kurulum ÖNCESİ lockfile+audit'ten geçer (slopsquatting %19,7).
- **H3 systemd sertleştirme** tur-1 ✅ (2026-07-31): 9.2 UNSAFE → 6.3 MEDIUM (iki servis;
  dosya-sistemi/ad-alanı seti + pano token'ı unit'ten 0600 .dash.env'e taşındı+rotasyon).
  Tur-2 📋: seccomp @system-service + CapabilityBoundingSet; hedef <4
  (NoNewPrivileges/ProtectSystem=strict/PrivateTmp/ProtectHome önce; seccomp EN SON ve dikkatli).
  + `MERIDIAN_DASH_TOKEN` unit dosyasında DÜZ METİN (herkes-okur) → rotasyon + LoadCredential'a
  taşıma AYNI bakım penceresinde.
- **H4 import-linter ✅ (tur-2):** 5 sözleşme 5/5 (506 bağımlılık); tek bilinçli istisna
  adapters.alpaca→broker (WP-E iki-motor yasası); backtest→loop DOLAYLI zinciri ölçüldü (sözleşme
  bölündü); MİMARİ BORÇ KAYDI: en büyük güçlü-bağlı bileşen 20 modül. ops/kapilar.sh zinciri +
  dagit.sh [0c] kapısı canlı.
- **H5 ✅ İLK GERÇEK KARNE (2026-08-01, 14. koşumda — 13 kırıklık saga 4 ortam-sınıfı + 2 araç-yalanı
  dersiyle altyapıya döndü):** 2.698 mutant → öldürülen 1.267 · hayatta 1.305 · testsiz 118 · skor
  **~%49** (hedef %80; NOT: pozitif-seçim alt-kümesinde ölçüldü — tam suite'in dışlanan davranış
  testleri bir kısmını öldürebilir, skor alt-sınır okunur). **AKŞAM GÜNCELLEMESİ — BORÇ
  KAPANDI: 16. koşum resmi skor 2312/2663 = %86,8 (hedef %80 AŞILDI).** 28-ajanlık Workflow turu
  (14 küme, enjeksiyon-kanıtlı) skoru bir öğleden sonrada +38 puan taşıdı; kalan 351'in çekirdeği
  doğrulanmış-eşdeğerler + hedeflenmemiş kuyruk — haftalık ritüel izler.
- **H5-eski kayıt:** yapılandırma + ops/haftalik_mutasyon.sh hazır
  (mutmut 3.7 doğru anahtarlar; sahte-%100 tuzağı belgeli); ilk gerçek koşum bakım ritüelinde.
- **H6 CLAUDE.md** ✅ 2026-07-31 — kısa çalışma sözleşmesi repo köküne yazıldı (log-önce kuralı,
  roller, yasalar, canlı-güvenlik).
- **H7 restore tatbikatı** ✅ İLKİ YAPILDI (2026-07-31): A1 arşivinden çekme 3,1sn + açma 0,3sn,
  64/64 JSON sağlam, sayılar canlıyla birebir. BULGU→ÇÖZÜM: tar "file changed" exit-1'i unit'i
  FAILURE'a boyuyordu + SQLite sonrası ham tar yarışlı olurdu → yedek unit revize (exit<=1
  toleransı + storage.backup_to tutarlı kopya, canlıda doğrulandı). Çeyreklik ritim sürer.
- **H11 ✅ KOD-HAZIR (tur-2; canlıya sonraki pencerede):** coordinate_descent_search süre-tavanı +
  kibar-iptal (YASA-4 olaylı) + warmup'ta sonda-başına çift nabız (warmup_sprint + hermes_poll —
  açlık-alarmı sınıfı ölür); HERMES_WARMUP_MAX_MIN=300 varsayılan; 17 test. Bekçi eşikleri değişmedi.
- **DEV-GRUBU DARALTMA ✅ (2026-08-03):** ops/import_tarama.py (AST, geçişli dev-kümesi, kurulu-
  metadata'dan eşleme) → HÜKÜM DARALT-GÜVENLİ (17 dev dağıtımının 0'ı çalışma yolunda, 95 dosya);
  dagit.sh [0d] KAPISI oldu (dev-paketi-çalışma-yolunda ya da ölçülemedi → ENGEL) + [3] bayrağı
  koşum-anında ölçer (--no-default-groups destekliyse o, değilse --no-dev'e düşer). YAN BULGU:
  `certifi` beyan-dışı (streamhealth.py:84 opsiyonel import) — beyan kalemi mini-tura verildi.
- **H9 KADEME-B ✅ ÇEKİRDEK (2026-08-03):** flock kapıya indi (write_json/write_jsonl kilidi
  kendisi alır; write_text eklendi; db_backed dalında bilerek yok — çift-kilit kilitlenmesi;
  events.jsonl append-only mezar-taşı testli). 14/14 + süreçler-arası flock kanıtı. AÇIK KUYRUK
  (çağrı-noktası taşıma, ayrı tur): ATOMİK-DEĞİL 4 yol (memory.py:212 lessons.md · run.py:172 ·
  hermes.py:1965 · skill_evolve.py:170) + fsync'siz/flock'suz kopya-kalıp 7 yol (auth._write
  ayrıca sabit-tmp-adı — iki süreç çakışır); kapı hazır: store.write_text.
- **DASH-TOKEN LoadCredential HAZIR-BEKLEMEDE (2026-08-03; etkinleştirme OPERATÖR bakım-penceresi):**
  drop-in'ler deploy/oracle-a1/meridian.service.d/ (faz-1 LoadCredential, faz-2 ortam-kanalı-sıfır)
  + dash_token_credential.sh (rotasyon/kurulum/doğrulama/geri-alma; faz-2 farksal ölçümlü).
  LoadCredential ana birime BİLEREK yazılmadı (kaynak-dosya-yokken ilk dağıtım panoyu düşürürdü).
  ÖLÇÜLEN YÜZEY: token bugün her LLM alt-sürecinin ortamında (serve.sh env-devri) — faz-2 kapatır;
  api.py CREDENTIALS_DIRECTORY okuyucusu mini-turda.

- **REDDEDİLDİ (bizim gerçekte):** Litestream/SQLite-PRAGMA/DuckLake (Meridian'da SQLite YOK —
  state dosya+Redis; el kitabının varsayımı yanlış) · Pandera (karantina-v2 + bars_integrity zaten
  ölçülmüş özel koruma) · GE/Temporal/K8s/SBOM/fail2ban/staging (el kitabı da reddediyor) ·
  SDD çerçeveleri (kart+brief disiplini zaten SDD-lite).
- **H8 GİT** ✅ 2026-07-31 (operatör onayıyla): yerel git init, 863 dosya ilk commit `d9c3f24`;
  .gitignore güncel (state/ [goal/bounds hariç] + backups/ + .env dışarıda — sır taşınmaz);
  `dagit.sh`'a kirli-ağaç kapısı eklendi (yarım-iş canlıya gidemez; bilinçli istisna --kirli-gec).
  YENİ SÖZLEŞME: tur başına commit; dosya-ayrıklık artık git-diff ile DENETLENEBİLİR.
- **H9 SQLite defter çekirdeği ✅ CANLIDA (2026-07-31 ~10:56 UTC penceresi; operatör koştu):**
  6/6 varlık parite-digest'le taşındı (shadow_books dahil); app-gözü birebir (95/94457.91/v3);
  WAL aktif; .migrated geri-dönüş arşivleri yerinde; MERIDIAN_DB=off acil anahtarı hazır.
  Kademe A: meridian/storage.py (WAL + synchronous=NORMAL + busy_timeout + foreign_keys) +
  trades/trade_plans/scoreboard/portfolio/equity_curve/shadow_books → state/meridian.db;
  parite-digest'li idempotent migrasyon (dbmigrate --uygula); store.py API'si korunur.
  Kademe B: kalan TÜM JSON yazımlarına merkezî atomik-rename + flock (store.py'de tek kapı —
  "süreç-içi kilit" tehlike sınıfı yapısal kapanır). events.jsonl JSONL KALIR (append-only doğru
  biçim). Öğrenme-katmanı dosyaları (hypotheses/validation_ledger) Kademe C'ye ertelendi.
- **H10 Litestream/PRAGMA/DuckLake hükmü (SQLite onayı sonrası yeniden değerlendirildi):**
  PRAGMA seti → H9 storage.py'ye gömülü (UYGULA) · Litestream v0.5 → UYGULA-AŞAMALI: önce
  file-replica (ikinci disk yolu + mevcut Mac-pull kapsar; RPO günler→dakikalar), OCI Object
  Storage S3-uyumlu bucket + anahtar OPERATÖRDE (→§6; Always-Free 20GB yeter) gelince gerçek
  off-box PITR · DuckDB → ölçüm tarafında OPSİYONEL okuma aracı (sıfır-risk ATTACH) ·
  DuckLake → RED-ŞİMDİLİK (251-sembol EOD'de katalog katmanının çözdüğü sorun bizde yok;
  tetik: bar arşivinin Parquet'e taşınması gündeme gelirse).


### WP-QC — QuantConnect Entegrasyonu 🆕 (2026-08-03; docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md)
- **İlke:** veri platformda serbest/çıkışta kilitli → QC = platform-içi ölçüm + LEAN-yerel motor;
  asla arşiv-kaynağı değil. Tüm ölçümler kart-disiplinli.
- **FREE kuyruk (kart-önce, sırayla):** ① delist-kapsam ✅ ÖLÇÜLDÜ (2026-08-03 EDG-021 v3 koşumu — DUR=None, PK geçti;
  @20 fazla CI-0-içi → kill#1 dalı "ŞÜPHEDE-değerlendirme"; birincil şüpheli evren-kompozisyon
  farkı [günlük üst-250 dilim-medyanı 0,0233 vs full_251 p75 0,0089]; survivorship-yönü ilk
  sayı: hayatta +0,54 vs delist −1,46 @20 betimleyici; ikinci-koşum hakkı tanım-eşitleme —
  operatör kararı; kart hükmü EDG-2026-021'de) · ② EODHD earnings 1998+ tarihsel-dizi fizibilitesi (7-gün-pencere biçim riski) ·
  ③ Quiver insider 2014+ derinlik (2021-öncesi legacy-alan ayrımı) · ④ Morningstar PIT-shares
  (delist isimlerde tarihçe; 45-gün yaklaşıklama şerhi) · ⑤ RETIRED_SYMBOLS çapraz-doğrulama
  (Security Master delist olayları + SPY constituents 2009+) · ⑥ Tiingo+SEC NLP ön-fizibilite
  (R1-4 sınırında küçük örneklem) · ⑦ VIX/SPX rejim-bağlamı (Cash Indices 1998+, CBOE VIX 1990+
  FREE — VIX veri-kilidi kısmen çözülebilir).
- **İkinci-motor pilotu (WP-H kolu):** LEAN Apache-2.0 YEREL (CLI'sız — dotnet/docker; hesap
  gerekmez) + KENDİ Massive/Alpaca barlarımız custom-data ile → tek sinyalde emir-düzeyi
  diferansiyel. + bulut-ikizi FREE B-MICRO (200 bt/gün) elle.
- **Operatör kararları (§6'ya):** katman yükseltmesi (Researcher Seat $10/ay — API/otomasyon
  kilidi; koltuk-tek-başına-yeter-mi belirsizliği hesap-içi doğrulanmalı) · ücretli setler
  (Brain $25 / Estimize $75 / SmartInsider $10 — ancak FREE fizibilite sonrası) · ToS-yorumu:
  yerel-indirme yolu Rol-1 önerisiyle İZLENMEZ.
- **EXPLORER DERİN-OKUMA HÜKMÜ (Ek-D — docs/QC-EXPLORER-DERSLERI-EK-D.md; 473 strateji, API-tam-envanter):**
  Explorer da kazanan-deposu DEĞİL — ÖLÇÜLDÜ: medyan OOS-1Y Sharpe −0,035, %50,8 negatif, SPY'yi
  geçen %5,8 (9 gerçek-kazanan, 4'ü Meridian-yakın: 343 B/M+F-Score · 341 TERS-likidite-value ·
  32 · 342); "score"=3-AYLIK Sharpe (aşırı-uydurma makinesi — 478 istisna değil beklenen çıktı);
  %30 ID silinmiş (sağkalan yanlılığı sayıyla). KART-KUYRUĞU REVİZE (Explorer-teyitleriyle yeni
  öncelik): ① PORTFÖY-düzeyi %4-8 tepe-dip kapısı vs isim-bazlı chandelier (ratchet DD'yi
  YÜKSELTMİŞ 31-26; take-profit en zararlı özellik: medyan −0,70/SPY-geçen %0) · ② rejim-KADRANI
  (kapı popülasyon-düzeyi teyit: medyan↑ ama sağ-kuyruk kesik — SPY-geçen %2,6-vs-%8,0; EDG-005
  bağımsız üretildi) · ③ HRP/korelasyon-küme bütçesi (YENİ — 452 DD %17,9; CF(ρ̄) kartının çalışan
  hâli) · ④ EDG-016 evren-koşulluluk ÜÇ-KOL (341 karşı-örneği: düşük-likidite-value OOS-1Y 1,58 —
  EDG-021 motoruyla) · ⑤ ufuk-uzatma 63g→252g (yıllık-rebalans SPY-geçme 4×) · ⑥ tamsayı bayrak-
  skoru (en iyi strateji 343 tam G-Score kalıbı). META-DERSLER: 3-aylık pencere hiçbir karnede
  birincil-sıralayıcı olamaz (kendi karnemizde kontrol → yoksa kill-list'e) · yorum-sayısı negatif
  sinyal (ρ=−0,591) · trend-t-stat çarpanı Explorer'da da YOK (Ek-B kartı teyitsiz ama açık).
  Açık kapı: kod-düzeyi okuma (klon ister — operatör hesabıyla, istenirse).
- **LEARNING-SÜZGECİ HÜKMÜ (Ek-C — docs/QC-LEARNING-SUZGECI-EK-C.md):** metodolojide ÜSTÜNLÜK
  BİZDE teyit (ön-kayıt/walk-forward/purged-CV katalogda yok; ISL makaleleri p-hacking ders-kitabı
  örneği — "nasıl kodlanır" kaynağı, "kanıt" kaynağı DEĞİL). Taşınan somut değer: R1 evren-yaşam-
  döngüsü + R2 SymbolData kalıbı + BC101 L5/L7 evren/ısıtma dersleri (API-bayatlık şerhiyle —
  docs'la çapraz-doğrulamadan kopyalanmaz). ASIL defter-v3 kaynağı: docs research-environment
  üçlüsü (applying-research + META-ANALYSIS [karne-akışımıza en yakın] + object-store).
  Operatöre: sertifika yok, kurs-kaydı yapılmadı, CV değeri sıfır.
- **BİLEŞEN-DERS KARTLARI (2026-08-03 /strategies taraması — docs/QC-STRATEJI-DERSLERI-EK-B.md;
  Rol-1 öncelik sırası, YAŞAYAN kolun üstünde çalıştıkları için (b)-adaylarından ÖNCE):**
  ① REJİM-KADRANI: SPY 12-ay t-stat [−1,+1] SÜREKLİ maruziyet çarpanı (kapı değil) — EDG-005
  hükmünü "kapı yanlış, modülasyon doğru" diye daraltır ya da rejim ailesini kapatır ·
  ② KORELASYON-ÇARPANI: CF(ρ̄)=√(N/(1+(N−1)ρ̄)) brüt-kısıntı — işlem sayısı korunup maxDD
  düşerse %92-aktif de-risk RAMPASI EMEKLİ EDİLİR (tabu-yok mandası kapsamında) · ③ ÇIKIŞ-
  MİMARİSİ: ratchet-olmayan vol-GENİŞLEYEN eşik (DBII) — chandelier "durak maliyeti"
  bulgusunun mekanizma-açıklaması; gölge-v2 varyant kolu olarak · ④ DİNAMİK-EVREN vs statik-251
  (EDG-016 seçici-mi-sıralayıcı-mı — EDG-021 QC motoruyla AYNI turda koşabilir) · ⑤ ikili-bayrak
  skoru + vol-önce koşullu sıralama (tutarlılık sınavları). (b)-KOVASI (8 aday, tam liste Ek-B):
  ilk-3 = 354 idio-skew (EDG-004'ü AÇIKLAMA potansiyeli) · 16 overnight-ayrışımı (sıfır ek veri,
  ÖZELLİK olarak yaşayan kola) · 269+125 kesitsel-mevsimsellik (tek kart, 125 grid-hücresi).
  AYRI TUR: Strategy Explorer taraması (hesap-kapılı — Rol-1 tarayıcı oturumuyla; OOS-cezalı
  skorla filtrelenmiş GERÇEK kazanan kümesi).
- **RED:** canlı katman (sıfır yeni yetenek) · log/scrape dışa-aktarım (ToS) · K-grid'i QC
  optimizasyonuna devir (kart disipliniyle uyumsuz) · ML-eğitim taşıma (Train kotası sembolik) ·
  Benzinga ($120 — Tiingo FREE dururken) · FREE'de lean-cli (sözleşme ihlali).
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-QC-2026-08-09.md`, salt-ölçüm + plan):** FREE QC hesabı **ZATEN
  AÇIK** (2026-08-03 — proje `Fat Apricot Koala`; hesap-açma bloğu KALKMIŞ, kalan tek blok operatörün
  defteri KOŞMASI, EDG-021 boru hattı hazır — §6-11). En düşük-bloklu kalem **⑤ RETIRED çapraz-doğrulama**:
  yerel yarısı BU TURDA koşuldu, **8/8** emekli sembol (ANSS/DFS/FI/HES/IPG/K/PARA/WBA) SP500-üyeliğiyle
  tutarlı; tek QC-adımı 1-hücrelik Security Master delist-olayı sondası (EDG-021'in ölçmediği erişim yolu,
  ②-④'ün delist-vekilini gerçeğe taşır). **C2-4 LEAN "hesapsız"** (Apache-2.0, dotnet/docker CLI'sız) AMA
  "sıfır-kurulum DEĞİL" — bu makinede **dotnet YOK, docker YOK** (makine-kurulum bloğu, operatör-hesap
  değil; boyut L, ayrı tur). **⑦ VIX/SPX** FREE ama ToS **platform-İÇİ** — canlı `regime.py` VIX kapısını
  AÇMAZ ("kısmen çözülebilir" = ölçüm-içi bağlam, canlı-kapı değil); ekleme K-grid'i ÇARPAR, ön-kayıtta beyan.


### WP-UX — YENİDEN-TASARIM PROGRAMI 🔴 AKTİF (2026-08-07; yön: docs/TASARIM-YONU-2026-08-07.md — operatör onaylı, BAĞLAYICI)
- **Girdi ölçümleri (bitti):** BASELINE-2026-08-06 (25 bulgu, 4×cid-4; araç kör noktası: detect
  app.js'in 7.511 satırında 0 bulgu) · PATTERN-ETUDU-2026-08-06 (11 platform, 81 iş; 22 FIRSAT,
  6 modül adayı, 10 yasaya-aykırı desen elendi) · UX-SADELESTIRME-DENETIMI (23 Nielsen bulgusu).
  HÜKÜM: pano eksik değil BAĞLANTISIZ — dürüstlükte kategoride önde, birleştirmede geride.
- **GİT OTORİTESİ DÜZELTMESİ (2026-08-09 — AŞAĞIDAKİ D0-D6 İŞARETLERİ BAYATTI):** D0-D6 dalgalarının
  HEPSİ git'te İNDİ; hash'ler tek tek doğrulandı (D2-D6 2026-08-07, D3-b `6bb2bb9` 2026-08-09 16:45).
  Kalan AÇIK: **D3-c altı modül** (delist-arşivi/C2-5 Massive kararına bağlı + kart ZORUNLU) +
  **D3-b F3-F13/F15** yüzeyleri. NOT: `docs/KESIF-WP-MKP-2026-08-09.md` §0 "WP-UX D0-D6 İNMEDİ" dedi —
  o BAYAT bu ROADMAP'e güvendi (git yasağı) ve ~16:30'da ölçtü; **git ÇÜRÜTTÜ** ve bu düzeltme onu kapatır.
- ~~**D0 acil doğruluk** 🔄~~ → **✅ İNDİ (v196 `c59dfcc`, 2026-08-07):** mod dört durumda da ölçümden
  basılır · ffill hücre-düzeyinde etiketli · `?? 0` triyajı 30/167 düzeltildi (137 listeli kuyrukta —
  D-serisi dışı kalıntı kuyruk, `?? 0` çıcır tavanı 181). Özgün: mod halted/stale'de kayboluyordu.
- ~~**D1 jetonlar + beş renk rolü** 📋~~ → **✅ İNDİ (v197 `6025d82` + çivi `0220e6b` + D2-a `07deab7`):**
  iki katmanlı jeton mimarisi (hue adı bileşende YOK); mod KENDİ yapısal kanalını aldı; koşulsuz emisyon
  15→0; D1 çivi 7 kırmızı kapandı (iddialar zayıflatılmadan); D1 şablon-içi ters-tırnak P0'ı D2-a kapadı.
- ~~**D2 kart sözleşmesi + yeni IA** 📋~~ → **✅ İNDİ (D2-a v198 `07deab7` + D2-b v199 `c0d8238`):**
  tek kapak anatomisi (özet=hucreGovde), açık kart 77→52; 7 sayfa→5 yüzey (işe göre), 6 olay yüzeyi
  (obs 12 jetonun 12'si), 8 yinelenen çift tekilleşti, 1220 test yeşil. Özgün IA: ①Bugün ②Karar ③Sağlık
  ④Öğrenme ⑤Kilitler; runbook.html EMİLİR, workflow.html EMEKLİ, landing.html KALIR+onarılır (1,53:1).
- **D3 fırsat yüzeyleri + modüller** 🔄 KISMİ İNDİ: D3-UI **✅ (v200 `ac86de9`)** — C1'in on işi 10/10
  defter→uç→pano zinciri TAM, "üretiliyor ama görünmüyor" kovası kapandı · D3-arka üç modül **✅ (v197
  `7b9158a`)** — ajan telemetrisi + ham-iz defteri + vaka sabitleme · D3-b F1/F2/F14 **✅ (v229 `6bb2bb9`,
  2026-08-09)** — kâğıt-canlı ayrışması + sapma kökü + iki-kademeli eşik+NO_DATA. **AÇIK:** D3-b F3-F13/F15
  yüzeyleri + **D3-c ALTI MODÜL** (operatör: hepsi yazılır; delist-arşivi/C2-5 Massive kararına bağlı +
  kart ZORUNLU). Özgün C1 on işi: reddedilen-karar karnesi 4.988 satır · emir yaşam-döngüsü · /api/spend
  SIFIR web çağıranı · canlı zaman çizelgesi · rollback sicili · regresyon kırılımı · denetim izi ·
  "bugün neden hiçbir şey olmadı" · çıkış-nedeni kırılımı [stop_gap 1.973R] · skor olgunlaşması.
- **D3-b F5 ✅ İNDİ (v230, 2026-08-09) + KAPSAM YENİDEN-SINIFLANDIRMASI (WP-UX ajanı KANITLADI):** F5
  alarm-taksonomisi (`watchdog.alarm_gunluk` YASA-6 boşluğu, F1/F2/F14 sınıfı — v192'den üretiliyor,
  hiç okunmuyordu) indi. Nominal "12 F-kart + 6 D3-c modül" frontend dosya-sınırından (app.js, api.py YOK)
  ÇOK büyük; kanıtlı gerçek harita:
  - **(a) frontend-inebilir + temiz yetim veri: YALNIZ F5 ✅** (indi).
  - **(b) BACKEND gerekli (ayrı WP, api.py — WP-UX değil):** F3 pre-flight/what-if · F4 decision-rewind ·
    F11 outage↔return time-series-join · F12 pre-tuning (config.py yazar).
  - **(c) ZATEN yüzeyde → çift-kaynak riski (v191'in savaştığı şey; KAPANDI say):** F9 gate/lock
    (`gatekeeper.plans[].gate_reasons` planRowFull'da) · F10 capacity (`portfolio_heat` app.js:5289) ·
    F13 K-penalty (`deflate` app.js:4719).
  - **(d) viz/etkileşim (ayrı özellik):** F6 saved-queries · F7 agent-path graph (C2-2 v197 zaten indi).
  - **(e) kanonik okuyucu gerekli (uydurmadan inemez):** F8 status-dictionary (→ §2 öneri, en iyi aday) ·
    F15 allocation-history (per-period defter okuyucusu YOK).
  - **D3-c modüller:** C2-1/C2-2/C2-3 ✅ DONE (v197 "D3-arka"); AÇIK: **C2-4 LEAN** (Task-4, LEAN yok) ·
    **C2-5 delist-arşiv** (operatör Massive-kararına bağlı + kart ZORUNLU, veri yok) · 6. çalışma adayı.
  → **WP-UX FRONTEND kısmı ESASEN BİTTİ**; kalanlar backend WP'leri / operatör-blok / viz-özelliği.
- ~~**D4 yazı tipi** 📋~~ → **✅ İNDİ (ölçüm `f8097d0` + uygulama v201 `9cd27de`):** kazanan Recursive
  (Sans+Mono Linear, OFL, binary-ölçümle); üç yüzeyde KENDİ-BARINDIRMALI, CSP SERTLEŞTİ (Google origin
  düştü). Geist EMEKLİ (operatör kararı) uygulandı.
- ~~**D5 sertleştirme** 📋~~ → **✅ İNDİ (git otoritesinde "D5 jeton birliği", v208 `11bdc02` + merge
  `4560362`):** dört yüzey tek sözlük — landing/workflow rol katmanının 40 jetonu + runbook kendi paleti
  tekilleşti; CPL hükmü 92→78 düzeltildi.
- ~~**D6 doğrulama** 📋 (audit/critique önce-sonra, on ilke kanıtlı, devir)~~ → **✅ İNDİ (git otoritesinde
  "D6 tip rampası", `b71f65b` + `64009ca`):** runbook tip rampası gövde-sapması ÖLÇÜLDÜ ve ÇÜRÜTÜLDÜ
  (15/26/18→14/28/20px, telafi panonun KENDİ .md'sinden); D6 kanıt zinciri kapatıldı (korpusu ÜRETEN kod
  da depoda — EDG-016 sınıfı). D6 hükmü t3 korpus-tazeleme kadansında TUTUYOR (`d993bd1`/`e278466`/`8ce3123`:
  satır kaymaları hükmü değiştirmedi, 7 aile yeşil).
- Kapı: her dalgada kapsam testleri → tek otoriter suite → tek dagit → canlı doğrulama.


### WP-P — Pano/Operatör Arayüzü (2026-08-01 UI el kitabı — gerçekle çarpıştırılmış; kontrol-odası
+ finans-izleme kanıt tabanı: HP-HMI/ISA-101, Airbus dark-cockpit, EEMUA 191, Few/Tufte)
- **ZATEN VAR:** tabular-nums (19 kullanım) · dürüstlük-UI (None≠0 = YASA, provenance rozetleri,
  sermaye-köken, nabız-bayat beyanı) · koyu tema · CSP script-src-self · yoğun-uzman düzeni.
- **P1 Sessiz-Hat ✅ CANLI (2026-08-01):** 17 bekçi + kilitler + tazelik TEK toplanmış şeritte — sağlıklı
  = "17/17" sönük tek özet, SAPMADA segment açılır; renk yalnız anomalide (ASM 5× tespit kanıtı;
  klinik alarm-yorgunluğuna karşı toplama KRİTİK).
- **P2 Alarm bütçesi ✅ CANLI:** EEMUA 80/15/5 + <10/10dk tepe + <10 duran-alarm canlı gösterge;
  taşkın-toplama.
- **P3 Gauge yasağı ✅:** mevcut 2 gauge → bullet-graph + gömülü-trend + beklenen-aralık bandı
  (Few spesifikasyonu; tek-hue yoğunluk aralıkları).
- **P4 Tipografi ✅ (slashed-zero ölçülüp-gereksiz):** slashed-zero + sağa-hizalı sabit ondalık taraması.
  **DÜZELTME 2026-08-06 (operatör): "Geist KORUNUR" bir YASA DEĞİL.** 2026-08-01'de reddedilen şey
  el kitabının *Inter* önerisiydi; bu, Geist'i dokunulmaz yapmaz — Geist bugünkü YÜRÜRLÜKTEKİdir,
  bağlayıcı taahhüt değildir. Yazı-tipi değişimi AÇIK kalem (ayrı `typeset` turu). Değişmeyen:
  jeton sözlüğü tekliği, iki-zemin, geometri/ölçek/gölgesizlik ve işlevsel çıta (kendi-barındırma
  [CSP dış font-host'a izin vermez] · açık lisans · tam Türkçe aksan · gerçek tabular rakam ·
  eşlenik mono · iki zeminde küçük-punto okunabilirlik/halation).
- **P5 Belirsizlik ✅ (renksiz kanal):** onarım-dolgu/imputation hücrelerinde belirsizlik-görseli +
  bayatlık-solması standardı (Sarma/Kay).
- **P6 ✅ TAM (gündüz turu 2026-08-02 indi — 9 yüzey tek-katsayı, sıfır saf beyaz; 148-çift yeniden-ölçüm, 0 hüküm değişimi):** #000/#FFF → koyu-gri zemin + kırık-beyaz metin (halation);
  WCAG 2.2 AA UYUMLULUK STANDARDI KALIR (APCA yalnız tasarım-yardımcısı — el kitabının kendi
  düzeltmesi: WCAG-3 onaylı değil).
- **P7 ⌘K paleti ✅ CANLI (933 satır, 25+7 komut, iki-adım onay):** tek eylem yüzeyi; kilit/nav/filtre; kısayol-ipuçları;
  CSP-self uyumlu.
- **P9 ✅ (2026-08-02):** kapsama ısı-matrisi (7×6, None-haritası) + tek-hue sequential + CVD-güvenli diverging; jetonlu, AA-ölçülü.
- **P10 Hareket ✅ (koşulsuz-puls söküldü):** prefers-reduced-motion + ≤300ms puls YALNIZ-anomali; skeleton
  sınırlaması kural olarak (zaten kullanılmıyor).
- **RED/UYARLANDI:** APCA-birincil (red) · Inter (red — Geist kalır) · skeleton yaygınlaştırma
  (red — Viget karşı-kanıtı) · ARIA-live genişletme (dar: yalnız kritik alarm/kilit — tek görüşür
  operatör) · Doherty 400ms (Nielsen 0.1/1/10 esas) · P8 confirmed-state zaten mimaride (E1/mutabakat).
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-P):** yüzey programı **P1-P10 KAPALI**.
  WP-UX'ten AYRI TEK canlı borç = `docs/RUNBOOK.md` **32 "runbook girdisi henüz yazılmadı"** (P-A —
  HEARTBEAT_STALE/ROLLBACK/CIRCUIT_BREAKER/MIRROR_DRIFT/NAKED_POSITION… alarmlarının Çözüm/betik
  prosedürü boş; kaynak-sözleşmeli/oto-üretilmiş `ops/runbook_uret.py`, kapatmak GERÇEK prosedür yazmayı
  ister — yüzey değil içerik). İkinci rol: **WP-P ≠ WP-UX** — WP-P = gereksinim/doktrin (HP-HMI/ISA-101/
  EEMUA-191/Few-Tufte kontrol-odası) = **WP-UX D6 kabul çıtası**; WP-UX = yüzey/icra. WP-P yüzey işi
  YENİDEN AÇILMAZ (WP-UX aynı yüzeyleri düzenler).

### WP-L — Öğrenme/Ölçek Merdiveni 📋 (tetik-şartlı; sırası kendiliğinden gelir)
- Y5 meta-labeling (tetik: işlem birikimi — WP-R rampayı serbestleştirirse hızlanır) · Y7 ML
  sıralama (tetik: evren genişlemesi WP-U) · intraday 4a saha kanıtı (tetik: ilk silahlı plan) →
  4b gölge → Faz 5 kanıt → Faz 6 BEŞ KİLİT (değişmedi) · 6.1 guard-ret oranı izleme.
- **MERDİVEN DURUMU ÖLÇÜLDÜ (2026-08-07, canlı):** 4a defteri 7.541 satır — ama bu DAKİKA BARI
  değerlendirmesidir, "emre dönebilecek karar" DEĞİL (Rol-1 bu paydayı bir kez yanlış okuyup
  "tıkanıklık" sandı; kart `EXE-2026-002` yanlış paydayı adıyla yasaklıyor). 4b gölge defteri
  4 dolum. Faz-6 zinciri **1/5** — açık olan tek kilit operatör onayı (`INTRADAY_ARM`).
- **✅ Faz-5 kilidi artık ÖLÇÜYOR (v212, kart `EXE-2026-002` + R1):** `durum` `olculemedi` →
  `olculdu`. Gerekçe "üreten kod yok"tan "ÖRNEKLEM YETERSİZ (4/20)"ya döndü — birincisi hiç
  dolmaz, ikincisi işlem biriktikçe KENDİLİĞİNDEN dolar. Ölçüm: n_eşleşen 4/4 (kill#4 %0),
  ortalama −9,69 bps / −0,015R; CI **hesaplanmadı** çünkü `n_kume=1` (dört dolum tek gün) —
  tek kümeden aralık üretmek genişliği sıfır bir CI verip kilidi HAK ETMEDEN açardı.
  Tarih-kümeli bootstrap ayrıştırıcı testle kanıtlandı (aynı gün ikizlenen gözlemde kümeli
  aralık %0 değişiyor, düz bootstrap %30 daralıyor). **Bu kalem KOD İSTEMEZ, İŞLEM İSTER.**
- Kalan üç kapalı kilit (edge 1/5 · sonuç 0/4 · DSR 1e-06) KANIT eksikliğinden kapalı; kodla
  açılamaz, kârlı işlem geçmişi ister. Merdivende kodla açılabilecek kilit KALMADI.


## §2 ÖNERİ HAVUZU (backlog) — Claude'un önerileri

Biçim: `gerekçe · tahmini boyut · bağımlılık · öncelik`. Olgunlaşan öneri §1'e taşınır + Task açılır.
Ölçüm önerileri karta (§4) dönüşür; operatör kararı gerektirenler §3'e geçer.

1. ~~**dagit rsync exclude genişletme**~~ → **✅ YAPILDI (2026-08-10, dagit.sh:18):** üç kapsamlı desen
   eklendi (`research/olcumler/*/seanslar.json` · `*/run.stderr.log` · `*/state`), tarihli gerekçe yorumda;
   v204 testi ekleme-toleranslı (yalnız 'backups' varlığını sabitler). Özet `sonuc.json`+`olcum*.py` taşınmaya
   devam eder. *(Öneri-akış yaşam döngüsü: §2'den kapanan ilk madde.)*

2. **Gözlemlenebilirlik/dağıtım iyileştirme adayları (2026-08-02 canlı vaka; tam metin §6 snapshot'ta korunur)** —
   hermes-CLI kalemleri a-e (servis açılışında senkron-doğrulama · pano senkron-sonuç zaman-damgası ·
   bekçi "kota"≠"yapılandırmasız" ayrımı · RPD bütçesi ağa çıkmayan çağrıyı saymasın ·
   `candidate_review_empty_parse` uyarısı) + dagit versiyonlu-state adımı (diff-göster + onaylı-kopya;
   goal/bounds git-izli ama diğer versiyonlu state için). *gerekçe: canlı vaka kökenli sessiz-ölüm/
   görünürlük boşlukları · boyut: S-M · bağımlılık: bakım penceresi · öncelik: düşük-orta.*

3. **F8 pano durum-sözlüğü (WP-UX kalan F-kartlarının en iyi frontend adayı)** — dağınık `durum`
   alanlarını tek kanonik sözlükte toplar. WP-UX ajanı (2026-08-09) F3-F15 içinden frontend-inebilir
   TEK temiz aday olarak işaretledi (F5 indi; F3/F4/F11/F12 backend, F9/F10/F13 zaten yüzeyde, F6/F7
   viz, F15 defter yok). ÖN ŞART: kanonik bir durum-okuyucu — yoksa dağınık alan sentezi UYDURMA riski
   (önce okuyucu tanımı). *gerekçe: YASA-6 (durum dağınık) · boyut: M · bağımlılık: kanonik durum-okuyucu · öncelik: orta.*

4. **DSR girdi-serisi donmuş-çekim aracı (KYS-002 kill#2'nin araç borcu, 2026-08-10)** — kapının taze
   küme-DSR'ı `_ret` (pnl/START_EQUITY, reflect.py:559) serisini ister; validation_ledger `seri`si
   (kapanış-günü, r_multiple) ölçek-eşdeğer DEĞİL (ölçüldü: Sharpe sapması medyan 0.0131). İki yol:
   defter şemasına pnl-serisi damgası (yazar reflect, okuyucu ölçüm-çekimleri) YA DA işlem-düzeyi pnl'li
   yeni donmuş-çekim betiği. Araç inince KYS-002 DSR-yarısı yeniden ölçülür. *gerekçe: M2'nin DSR yarısı
   ölçülemiyor · boyut: S-M · bağımlılık: reflect şema kararı (Rol-1) · öncelik: orta.*

5. ~~**`.locks/` budaması**~~ → **✅ KAPANDI (v234, 2026-08-12):** store.kilit_budamasi + conftest
   sessionfinish (24sa+flock+inode-güvenli; ilk koşu 29 kilit temizledi). *(orijinal madde: 2026-08-10)* — test koşuları
   oturum-düzeyi tmp yolları hash'lenmiş kilit dosyaları bırakıyor (tur ölçtü: tek AST koşusu bile +2;
   25→27 birikiyor, budama yok). DİKKAT: flock semantiği — canlı tutulan kilidi silmek dışlamayı kırar;
   güvenli budama = non-blocking flock alınabilen + eski dosyalar (ops betiği ya da conftest teardown).
   *gerekçe: sınırsız birikinti · boyut: S (flock-dikkatli) · bağımlılık: yok · öncelik: düşük.*

6. ~~**Bayat-defter-kalıntısı tuzağı**~~ → **✅ KAPANDI (v234, 2026-08-12):** db_backed göç-süzgeci
   (idempotent, adli-olaylı, damgasız-dosya-taşınmaz); canlı trades.jsonl kalıntısı bir sonraki restart'ta
   kendiliğinden .migrated olur. *(orijinal madde: 2026-08-11)* — trades defteri 07-31'de
   DB'ye göç etti ama `state/trades.jsonl` DOSYASI 95 satırda donuk kalıntı olarak duruyor (portfolio/
   shadow_books `.migrated`a çevrilmiş, trades ÇEVRİLMEMİŞ) → insan+araç yanlış okuyor (Rol-1'i "pozisyon
   izsiz kayboldu" yanılgısına düşürdü; gerçek: T00097 VLO target +728$ DB'de düzgün). Düzeltme: migrate
   edilen TÜM defter dosyalarına .migrated disiplini + store'a "bu ad DB'de, dosyayı okuma" koruması.
   *gerekçe: adli/ölçüm güvenilirliği · boyut: S · bağımlılık: yok · öncelik: yüksek.*

7. **4 pozisyon adet-sapması muhasebeli true-up (NUE 54/25 · EMR 64/37 · BKNG 43/22 · AMGN 33/22)** —
   **KÖK ÖLÇÜLDÜ (2026-08-12, Alpaca emir-geçmişi salt-okunur): kısmi-dolum DEĞİL — dört giriş emri de
   TAM dolmuş (25/25 · 37/37 · 22/22 · 22/22, 08-06). Sapma GÖNDERİM-ANI BOYUTLAMA AYRIŞMASI** (SB-1
   makbuz-öncesi dönem; oranlar 0.46–0.67 değişken = tek çarpan değil; AMGN coid'i momentum_burst —
   dormant bir kez aynalanmış, tarihsel). İleri akış SB-1 makbuzuyla korunuyor; geriye dönük yön kararı
   operatörde: (a) kitabı broker-gerçeğine indir (25/37/22/22; iç R-muhasebesi düzeltme-satırlı) ya da
   (b) iki-motor kabulü + drift_sinifi 'makbuzsuz_boyut' (olculemedi yerine açıklanmış sınıf, alarm
   anlamlı kalır). Uygulama her iki yönde de muhasebe-satırlı, SESSİZ DEĞİL. *gerekçe: kitap↔broker
   bütünlüğü · boyut: S-M (kök artık belli) · bağımlılık: operatör yön kararı (§3) · öncelik: yüksek.*

8. **MNST split sınıfı — TEŞHİS ✅ (docs/TESHIS-MNST-SPLIT-2026-08-12.md); düzeltme KART-önce açık** —
   MNST 1→2 (08-11, Massive splits dış-doğrulama). Kök: kaynak-kıyas kör-yüzde (oran-imza tanımaz); defter
   DOĞRU retro-değişmez. Yön: A1 oran-imza + A2 kümülatif-katsayı defteri (kart ön-kayıtlı ölçüm-değişikliği).
   YAN: corp-action FLAP (GE 34 reset/26g) aynı körlük ailesi; MNST turnover ~2× şişme izlemede. *(eski madde:)* — DATA_QUALITY: nasdaq 91.43 vs massive 45.72
   (%50) + ledger_matches_bars 2 sapma (T00020/T00095 MNST defter-entry bar'ın 2 katı). Bar zinciri split'e
   ayarlanmış, trades satırları ham kalmış görünüyor. Teşhis + tutarlılık kuralı (defter mi bar mı düzeltilir,
   retro-değişmezlik gözetilerek). *gerekçe: ölçüm tabanı tutarlılığı · boyut: S-M · bağımlılık: yok · öncelik: orta.*

9. **equity_curve KADANSLI YAZAR planı (öğrenme-durması turu ölçtü, 2026-08-12)** — canlıda eğriye nokta
   ekleyen HİÇBİR kadanslı yazar yok (yalnız replay_seed tohumu + reset işareti); 149sa bayatlık alarmı
   BİLİNÇLİ görünürlük yaması (Ç1). TUZAK: ledgerstamp.seed_boundary sınırı eğrinin SON NOKTASINDAN okur —
   bugün nokta ekleyen yazar sınırı kaydırıp köken defterini bozar. SIRA ZORUNLU: (1) seed_boundary önce
   SON reset-işaretinin egri_son_nokta'sından okusun (sınır donar); (2) ANCAK SONRA loop.daily_cycle seans
   sonunda (date, eq_now) noktasını file_lock altında eklesin. *gerekçe: pano eğrisi + Ç1 ölçümleri canlı
   akmıyor · boyut: S-M (sıralı 2 adım) · bağımlılık: ledgerstamp→loop sırası · öncelik: orta-yüksek.*

10. **OPT — parametre-evrim boru hattı (elle-değerlerin otomasyonu; operatör sorusu 2026-08-12)** —
    iskelet VAR (bounds arama-uzayı + hermes önerici + DSR/PBO/OOS/K kapıları + gölge varyantları; dün
    onarıldı), ÜÇ EKSİK: (1) KABLOLAMA — aranamaz sabitler parametrize (derisk bandı fonksiyon-gövdesinde
    sabitti, monkeypatch gerekti; max_open/size_r/scale_out/chandelier bounds'a — sınırlar operatör onaylı);
    (2) REPLAY-SWEEP otomasyonu — kart→koşum→CI→hüküm şablonu (bu hafta 5× elle) gece A1-nice penceresinde
    (operatör tercihi) makineleşir, K-deflate'e çarpılı sayılır; (3) UYGULAMA POLİTİKASI sınıf-başına — Rol-1 ÖNERİSİ (2026-08-12,
    operatör onayı bekler): HEP-PENCEREYE = risk-artıranlar (rampa/slot/boyut/ısı) + eşik-gevşetme
    (strateji kimliği); DONUK-EŞİK-OTOMATİĞE = çıkış-parametre iyileştirmeleri, skor-ağırlıkları
    (gölge-doğrulamalı), kurulum-silahlanma (025 emsali, operatör seçti), ölçüm/görünürlük. Tek cümle:
    'vanaları pencere açar, kenar-iyileştirmeleri kapılar içinde makine evriltir.' FREN: PBO 0.6286 — otomasyon kapıların İÇİNDEN akar. *gerekçe: elle-optimizasyon
    ölçeklenmez · boyut: M-L (3 aşama) · bağımlılık: 023-027 karar penceresi + örneklem birikimi ·
    öncelik: yüksek (karar penceresinden sonra ilk büyük iş).*

11. **KARAR PENCERESİ PAKETİ — 023/024/025/026/027 + Rol-1 önerileri (2026-08-12; ölçümler inince
    tek pencere kurulur)** — Rol-1'in pencereye getireceği öneriler ŞİMDİDEN kayıtlı (sayılar hükümden önce
    gelir; CI'lar öneriyi çürütürse öneri düşer):
    · RAMPA 15/36 (kâğıt): BENİMSE — kill#3 (dd ×2.29) otomatik-hükmü engelledi, karar operatörün; %17.8 dd
      kâğıtta öğrenme bedeli ↔ 3× işlem + eksiden artıya P&L + düzelen işlem-R (−0.078→+0.032). Gerçek-para 3/8 SABİT.
    · SLOT 20 + 0.5R: OPERATÖR ÖN-KARARI (2026-08-12: 'ISI 10R kalsın') — 0.25R geri-düşüş önerisi KALDIRILDI;
      ısı 10R sabit, 026 sayıları pencereye BİLGİ olarak gelir (karar değiştirmez, şasi-geçersizlik hariç).
    · EŞİKLER (024): sayı gelmeden söz YOK — CI>0 hücre varsa OOS-kapılı öneri; yoksa 'eşikler kanıtla doğrulandı' kapanışı.
    · momentum_burst (025): DONUK ÜÇLÜ EŞİK karar verir (operatör otomatik-akış seçimi): replay-CI>0 ∧
      portföy-etkisi≥0 ∧ çelişki-açıklandı → silahlanır; düşen ölçüt adıyla raporlanır.
    · ÇIKIŞ KOLLARI (027): CI>0 kazanan kol(lar) benimse; Rol-1 beklentisi scale-out (%38 erken-kesim panzehiri) — beklenti≠hüküm.
    · SIRA: pencere → TEK goal/bounds dağıtımı → hemen OPT Faz-1 kablolama (sonraki sweep monkeypatch'siz koşmalı).
    *gerekçe: pencere kararları kanonik belgede ön-kayıtlı olsun (sohbette kaybolmaz) · bağımlılık: 024/025/026/027 ölçümleri · öncelik: en yüksek (bekleyen tek büyük karar).*

12. **M8 kararları Rol-1 turu (docs/M8-K-SENKRON-RAPOR-2026-08-10.md'nin işlenmesi)** — rapor 7 başlık verdi,
   kararlar ölçüm-anlamı değiştirir, aceleye gelmez: U1 EXE-001 K-düzeltme notu (aritmetik dürüstlük;
   tarihçe-koru) · U2 8 kartın pending-* trial_ids temizliği · U3 README endeks tazeleme · U5 beyan-K/
   harcanan-K şeması · U6 kart-K↔DSR n_trials bağlanmalı mı (MİMARİ: yeni tüketici + DSR çıktısı değişir) ·
   U7 rotasyon-yerel vs ömür-boyu sayaç hükmü. *gerekçe: K-defteri deneysel bütçenin kalbi · boyut: M ·
   bağımlılık: rapor(✅) · öncelik: yüksek-ama-odaklı-tur.*


## §3 OPERATÖR BLOKLARI (karar/aksiyon/kimlik/para/bakım-penceresi operatörde)

Claude'un otonom kapatamayacağı kalemler: operatör kararı, ücretli kimlik/kota, gerçek-para kapısı,
ya da canlı-worker durdurup state'e yazan bakım penceresi. "Çağıranı yok" ile "çağıranı İNSAN" ayrı
şeydir (envanter tablosu §3-sonu bu ayrımı korur). **Bakım-penceresi onaylı sırası (2026-08-09):**
OB-2 systemd exit-143 → OB-1 N1 kanal → OB-4 restart→PBO (M2) damgalama çapraz-kaldıraç; N4 cf
çıkış-sadakati (EXE-2026-004 Aşama-2, saatler, state'e yazar) aynı pencerede.

**YENİ OPERATÖR BLOKLARI (WP turlarından toplandı — eski §6 numaralı listesi + envanter tablosu altta):**
- **OB-2 systemd `SuccessExitStatus=143` — ✅ YAPILDI (2026-08-09, operatör):** canlı `SuccessExitStatus=143`
  doğrulandı (`Result=success`, active/running, NRestarts=0). Artık restart exit-143'ü "FAILED" SAYMIYOR →
  N1 kanalı açılınca temiz-durdurma yanlış-alarm boğmayacak (gerçek çöküş SIGKILL=137/SIGSEGV=139 HÂLÂ
  OnFailure'a gider — satır temiz-durdurmayı susturur, arızayı değil). Bu N1 kanalının (OB-1) ön-şartıydı, kalktı.
- **DASH-TOKEN LoadCredential faz-1 etkinleştirme (bakım penceresi):** drop-in'ler HAZIR
  (`deploy/oracle-a1/meridian.service.d/`, faz-1 LoadCredential + faz-2 ortam-kanalı-sıfır) +
  `dash_token_credential.sh` (rotasyon/kurulum/doğrulama/geri-alma). Ana birime BİLEREK yazılmadı
  (kaynak-dosya-yokken ilk dağıtım panoyu düşürürdü); etkinleştirme operatör bakım-penceresinde.
- **ajan-git MEKANİK kapısı (süreç/araç kararı):** gece 2 ajan `git stash` koşup hasar verdi (hayalet
  dizin süpürüldü). Yasak yalnız CLAUDE.md sözleşmesi; `dagit.sh` yalnız DAĞITIMI kapıyor; `git stash`ın
  pre-stash kancası YOK → kapı ancak PATH-shim/wrapper'la mekanikleşir. Karar operatörde.
- **C2-4 LEAN CLI `lean login` (QC kimlik — fizibilite 2026-08-09):** toolchain ✅ (colima+docker+lean 1.0.227
  kurulu/çalışıyor, healthz-dışı yerel) AMA `lean init` QC `User id`+`API token` İSTİYOR (`~/.lean/credentials`)
  → LEAN CLI yolu KİMLİK-bloklu (ben giremem). Operatör `lean login` (QC Fat Apricot Koala) yaparsa CLI tam-impl
  açılır. ALTERNATİF (kimliksiz): CLI'sız dotnet-engine (LEAN Apache-2.0 local, QC'siz) — ama LEAN monorepo
  git-clone + dotnet-build = **L-boyut ayrı tur** (§1 C2-4). Karar: `lean login` (kolay) mı, dotnet-engine (bağımsız) mı.

**EKSİK OPERATÖR ENVANTERİ (eski §6 — kanonik liste 1-11 + §6.1 tablosu; numaralar korunur):**

1. **NOUS_MODEL / beyin çeşitliliği — CANLI KANIT EKLENDİ (2026-08-12): Gemini HTTP 404.** Review
   doğrulamasında yakalandı: birinci model "Gemini returned HTTP 404" (endpoint/model-adı ölü), yedek
   tencent/hy3:free boş dönüyor → beyin zinciri fiilen CEVAPSIZ. v233 artık bunu dürüst olaylıyor ve
   bütçe yangınını kesti (150 boş çağrı/gün bitti) ama GERÇEK review üretimi beyin gelene kadar olmaz
   (12 denemede tarih 'gecersiz' işaretlenir — kalibrasyon boşluğu dürüst). Claude API anahtarı EKLE
   veya NOUS_MODEL'i Google-dışı modele çevir (panodan GEMINI_API_KEY girmek çeşitliliği GERİ siler).
2. **Bildirim kanalı:** Telegram/webhook — teslim zinciri hazır, kanal boş.
3. **FMP kota kararı** (plan/limit).
4. **Oracle sunucu taşıma** (5.1) — Faz 6 ön şartı.
5. **Faz 6 kapısı:** BEŞ kilit (`health.faz6_kilitleri`) dolunca INTRADAY_ARM + emir bacağı onayı.
6. Ajan tavanı: 15 (2026-07-29; implementasyon yine turda tek ajan).
7. **FMP plan yükseltmesi (Y4):** ücretsiz planda Form-4 ucunun sayfalaması ve `search` ucu KAPALI
   (ölçüldü 2026-07-30 — aşağıdaki tabloda `insider` satırı). Yükseltme, 3 yıllık sınıflama
   penceresini beklemeden açar; yükseltilmezse pencere ancak zamanla dolar.
8. **FINVIZ_API_KEY (evren genişletme) — ÖNCE EDG-2026-022 (2026-08-09 keşfi):** Elite token evreni
   251'in üstüne çıkarır AMA satın almadan ÖNCE **EDG-2026-022** ("Evren bağlayıcı kısıt mı?" — otonom
   kart, `docs/KESIF-WP-U`) ölçmeli: işlem üretimini bağlayan aday-havuzu mu, yoksa de-risk tavanı
   (`eff_max_open`, günlerin %92'sinde 1 pozisyon) mu? Evren bağlamıyorsa FINVIZ parası boşa gider.
   Kanıt: `finviz_unavailable` 3.746 / `finviz_universe` 0. (§6.1 `FINVIZ_API_KEY` satırıyla aynı token.)
9. **Massive/QC delist-bar kaynağı kararı (2026-08-09 keşfi):** survivorship-serbest evrenin TEK meşru
   yolu — RAKİP DEĞİL TAMAMLAYICI: **(a) QC platform-içi ölçüm** (BEDAVA; ToS barı dışarı ÇIKARAMAZ →
   yerel arşiv boşluğu ÖLÇÜLÜR, DOLMAZ) VEYA **(b) Massive plan yükseltmesi** (yerel arşivin tek meşru
   derin-tarih yolu; grouped bugün 403 + plan ~2 ay derinlik → 2004+ arşiv yeniden-üretilemez KALINTI).
   %96,57 delist boşluğu + EDG-018 açılışı buna bağlı. `docs/KESIF-WP-U` §4-B2 / `docs/KESIF-WP-QC`.
10. **OCI Object Storage bucket + S3-uyumlu anahtar:** H10 Litestream **aşama-2** (off-box PITR).
    Always-Free 20GB yeter; gelene dek RPO = aynı-disk (medya/bölge arızası kapsanmaz). `docs/KESIF-WP-HD` §H10.
11. **QC FREE defter koşumu (EDG-021 boru hattı, 2026-08-09 keşfi):** FREE hesap AÇIK (2026-08-03);
    kalan tek blok operatörün notebook'u KOŞMASIDIR (ajan defteri yazar → operatör koşar → Rol-1 hüküm).
    Kuyruk başı = **⑤ RETIRED çapraz-doğrulama** (yerel yarısı 8/8 tutarlı; tek QC-adımı 1-hücrelik
    Security Master delist-olayı sondası). Ayrıca **EDG-021 2. koşum** tanım-eşitleme hakkı operatörde
    (@20 fazla CI-0-içi; WP-K K3). Katman yükseltmesi (Researcher Seat $10/ay) yalnız ölçüm-OTOMASYONU
    için — elle koşumda GEREKMEZ. `docs/KESIF-WP-QC` §4-5.

### 6.1 OPERATÖR KALEMİ ENVANTERİ (temizlik turu 2026-07-30 — ölü-mekanizma avının üçüncü kovası)

Bu tablonun VARLIK SEBEBİ: hedef sözleşmesi md.1 üç hâl tanır — kablolu, emekli, ya da **operatör
kalemi**. Üçüncüsü yazılı olmazsa bir sonraki ölü-mekanizma avı bunları "çağıranı yok" diye yeniden
öldürmeye çalışır (bu turda İKİSİ tam olarak öyle işaretlenmişti ve çürütüldü). "Çağıranı yok" ile
"çağıranı İNSAN" ayrı şeylerdir.

| Kalem | Ne | Neden operatörde | Nasıl kullanılır |
|---|---|---|---|
| `alpaca.live_client` / `live_guard` | Gerçek-para ticaret istemcisi ve onun sert kapısı (UYUYAN — hiçbir üretim yolu çağırmıyor) | Gerçek para. Kod bir insan iki bayrağı elle çevirmeden ve §8 terfi kapıları geçilmeden bu yola GİREMEZ | `MERIDIAN_MODE=live` **ve** `MERIDIAN_I_ACCEPT_RISK=true` + `goal.limits.autonomy_level >= 1`; üçü eksikse `live_guard` RuntimeError atar |
| `TELEGRAM_*` / `MERIDIAN_WEBHOOK_URL` | Bildirim kanalı kimliği (HALT, breaker, rollback, süreç ölümü) | Kimlik/kanal operatörün; girilene dek `notify.configured()` False ve `fail-notify` beyanlı no-op'tur | Ayarlar ekranından ya da ortam değişkeni; girildiği an teslim zinciri (obs.alarm → notify.send) uçtan uca çalışır |
| `FINVIZ_API_KEY` | Finviz **Elite** token'ı (evren keşfi) | Ücretli abonelik. Yokken public HTML scraping ToS-riskli olduğu için otonom döngüde KAPALIDIR — Finviz dürüstçe devre dışı kalır | Ayarlar → "Test et" (`finviz.ping`). Token yoksa evren `REPLAY_UNIVERSE`e iner ve `finviz_unavailable` olayı bunu söyler |
| `HERMES_API_KEY` / `ANTHROPIC_API_KEY` | Yansıma beynine erişim | Ücretli API kimliği; anahtar yoksa beyin zinciri kotasız yola düşer ve gece yansıması sessizce durmaz, `brain_availability` alanında görünür | Ayarlar/ortam; durum `/api/hermes` → `integrations` ve `brain_cooldown` satırlarında okunur |
| `NOUS_MODEL` | Haftalık öz-değerlendirme beyninin model kimliği | **Beyin ÇEŞİTLİLİĞİ kararı**: Google'dan Google'a çevirmek çeşitliliği GERİ siler (bkz. §6 md.1) | Ortam değişkeni; boşsa varsayılan zincir kullanılır |
| `MERIDIAN_FORCE_RESEED` / `MERIDIAN_FORCE_BASELINE` | Kurtarma kolları — durum yeniden tohumlama / taban zorlama | Yıkıcı: birikmiş defteri geçersiz kılabilir. Otomatik bir yolun bunlara dokunması, bir arızayı sessizce "temiz başlangıç" gibi göstermek olurdu | Yalnız elle, tek koşu için; kullanıldığı tur ROADMAP §7'ye yazılır |
| `MERIDIAN_CORS_ORIGINS` | API'yi BAŞKA bir origin'e açar | Güvenlik yüzeyi. Token'sız açılırsa API hem cross-origin hem kimliksiz olur — `api.py` bunu `cors_without_token` ile uyarır ama ENGELLEMEZ | Virgüllü origin listesi; **daima** `MERIDIAN_DASH_TOKEN` ile birlikte |
| `MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES` | L1+ bayrağı: WS koptuğunda açık girişleri iptal et | Otonomi seviyesine bağlı bir risk tercihi; kâğıtta gereksiz, gerçek parada operatörün kararı | RUNBOOK'ta yazılı; `deploy/oracle-a1/RUNBOOK.md` prosedürüyle açılır |
| `MERIDIAN_SUPERVISED` | "Süpervizör altında (yeniden) başladım" bildirimi | Süreç ölümünün operatöre ulaşan iki yolundan biri. `ops/com.meridian.agent.plist` kuruyor — yani **ölü değil**, av adayıyken çürütüldü | LaunchAgent yüklüyse otomatik; elle koşuda `MERIDIAN_SUPERVISED=1` |
| `watchdog.grant_amnesty` | Meşru defter küçülmesine (re-seed) af damgası | Monotonluk dedektörünü SUSTURUR. Bir mekanizmanın kendi alarmını kapatabilmesi, dedektörü dedektör olmaktan çıkarırdı | Elle çağrılır; af `monotonic_amnesty.json`a yazılır ve raporda `amnestied` alanıyla GÖRÜNÜR kalır |
| Sprint elle tetiği | Öğrenme antrenmanını sıradan önce başlatma (override) | Kadans zaten otomatik (`sprint.maybe_start`); elle tetik yalnız HIZLANDIRMADIR ve `should_run` kapılarını atlar | Pano düğmesi / `/api/sprint`; meşguliyet penceresinde kullanmak bar kovalamasını yavaşlatır |
| `reflect --auto` | Deterministik tek-hamle yansıması (LLM'siz) | Beyinsiz/kotasız gecede tek hamle üretmenin elle yolu. `skills.axis2_cycle` Eksen-2 kolunu devraldıktan sonra ÜRETİM çağıranı kalmadı — kalan tek yol bu komut | `uv run python -m meridian.reflect --auto` (README'de yazılı). Otomatik bir çağıran EKLENMEZ: iki yansıma aynı gecede yarışır |
| FMP plan yükseltmesi | Y4 içeriden-işlem derinliği | Para kararı. Ücretsiz planda ölçüldü (2026-07-30): `page>=1` → 402, `limit>100` → 402, `search?symbol` → 402, `date=` sessizce yok sayılıyor | Yükseltilince `insider.PLAN_SAYFA_TAVANI` ve `--gecmis` yolu yeniden açılabilir; kadans bugün günde 1× `page=0` çekiyor |

**🔒 BİLET SAHİPLERİ (eski WP-O — §3'teki biletlerin envanteri):**
bildirim kanalı · NOUS_MODEL · FMP planı · VIX kaynağı [öncelik düşük — aile hükmü zayıf] ·
analist/NLP verisi · FISV/PSKY; ~~shares-outstanding~~ ve ~~PIT-fundamentals~~ 2026-08-01'de
EDGAR'la operatörsüz çözüldü)

## §4 KANIT/KARTLAR (`research/cards/` indeksi + hükümler)

Kural (README + iş emri): **kartsız ölçüm kodu yok**; her parametre grid'i K'ya ÇARPILARAK sayılır;
eşik ölçümden SONRA değişmez; kill-list dokunulmaz; ölçüm ajanı karta DOKUNMAZ (hükmü Rol-1 işler).
Durumlar: registered → measuring → promoted | archived. Kuzey yıldızı canlı hüküm (§0): **EDGE 1/5 ·
SONUÇ 0/4** — edge/para kanıtlanmadı. Aşağısı ÖZET-indeks; tam hüküm ilgili §6 WP / §5 kararında.

**AKTİF / YENİ KARTLAR (hüküm işlenmiş ya da ölçümde):**
- **EDG-2026-022** evren-bağlayıcı-kısıt — **measured (2026-08-09):** de-risk+tavan BİRLİKTE %65,84
  (CI 58,73–72,14; tamamı >%50) BASKIN → FINVIZ token harcaması **GEREKÇESİZ**; evren bağlayıcı DEĞİL
  (%34,17). Bağlayan: `tavan_sifir` %57,54 + `derisk_bagladi` %8,28 (asıl kaldıraç de-risk rampası/
  `eff_max_open`). KILL#3 tetiklendi (rejim-koşullu): trend_up'ta de-risk baskın, chop'ta (nadir %6,7)
  evren baskın → FINVIZ genel gerekçesiz, chop-özel evren ayrı+küçük. OTONOM/bloksuz. → §3-8 FINVIZ.
- **EXE-2026-004** cf-çıkış-sadakati (N4) — **measured_partial (2026-08-09):** AŞAMA-1 ölçüldü, üç
  tüketici ölçütünün ÜÇÜ de ölçülebilir zarar göstermedi → cf çıkış-tipleri **EKLENMEDİ**; +0,039R
  iyimserlik bir sapma olarak KAYITLI (düzeltilmedi). AŞAMA-2 (dört/altı çıkış tipi + TÜM cf tarihi
  yeniden koşum) eşiğe ULAŞILMADI → **DONDU**; bakım penceresi şartlı (saatler, state'e yazar). Eşikler
  ölçümden ÖNCE donmuştu, DEĞİŞMEDİ. → bakım penceresi §3.
- **EDG-2026-021** qc-delist-doğrulama — **measured (2026-08-03, QC FREE, defter v3):** DUR=None, PK
  GEÇTİ (IC=0,0265 n=335k); @20 fazla CI-0-içi → kill#1 "ŞÜPHEDE-değerlendirme" (birincil şüpheli
  evren-kompozisyon farkı). 2. koşum tanım-eşitleme hakkı OPERATÖRDE (§3-11; WP-K K3).
- **EDG-2026-019** skill-görüş-defteri (N2b) — **registered (2026-08-09); kod indi (v218), CANLI KANIT
  KURU-KOŞU:** terfi/emeklilik R-figürleri (vcp +0,116R / momentum-burst −0,114R) canlı state'te
  yeniden-üretilemedi (`eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi, kadans koşmadı). Birkaç EOD
  penceresi + ölçüm kodu bekliyor. _(README numara-notu: 019 önce "emekli" damgalıydı; skill görüş defteri için yeniden kullanıldı.)_
- **EXE-2026-003** gölge-planlı-kol (N2) — **registered (2026-08-09); kod indi (v217):** silahlanmamış
  planlı kol AYRI defterde `kol: planli|silahli` (karışım kill#4'ü ateşlerdi). Faz-5 kilidini AÇMAZ
  (kilit gerçek-iç-dolum ister); ölçeği ikincil hat verir: gölge(dakika-sim) × cf(EOD-sim).
- **EDG-2026-017** rvol-form-revizyonu — registered (K+=2); rvol≥2,5 bölgesi form-şartsız + sürekli-rvol artığı (1.4'ün torun-kartı; ölçüm-sonrası-seçim yasağına uyuldu).
- **EDG-2026-018** pit-midcap-üst-sınır — registered (K+=1); **askıda:veri-kapısı** (delist-bar; feasibility-gate önce; §3-9).
- **EDG-2026-020** postevent-inplay — **archived (2026-08-03):** kill#1+#3 (havuz-fazlası CI-0-içi/negatif; ham +%1,1 taban-sürüklenmesi = ders#3 vakası); 011'e aleyhte-önsel not.
- **KYS-2026-001** kıyas-kirlenmesi — registered (K+=2); **ALTYAPI kartı, retro-hüküm yok**; WP-M şasi aracına bağımlı (M1 = en yüksek kaldıraç — TÜM evren-medyanı ölçümlerini etkiliyor).
- **EXE-2026-001** entry-execution — **E1-R2 (2026-08-07):** işletim noktası REF·limitsiz rejimi
  (`limit_atr_mult:100`/`limit_pct_cap:0,04`); limit-bacağı MONOTON ZARARLI; kaçanlar sistematik kazanan.
  E2 defteri gerçek dolumla accrues → canlı-geçiş kapısında E2 kanıtıyla yeniden hüküm (WP-E §1).
- **EXE-2026-002** faz5-çıkış-ölçümü (+R1) — **ölçüyor (v212):** `olculdu`; n_eşleşen 4/4 (kill#4 %0),
  ort −9,69 bps; CI **hesaplanmadı** (`n_kume=1`, dört dolum tek gün). İş ister, kod DEĞİL. kill#4
  uygulama borcu → WP-S2 §1.

**ARŞİV / KAPALI KARTLAR (hüküm — tam gerekçe §6 ilgili WP + §5):**
- **EDG-2026-016** turnover-ana-etkisi — **SUCCESS / YAŞAYAN SİNYAL** (@20 net +0,55% CI-0-dışı; q5 monoton; survivorship-şerhli). Kablolama açık → WP2 §1.
- **EDG-2026-009** trend-kolu-rafine — **measured→ALIVE/refine** (ham kol incumbent; PIT şerhi ~6-7p/yıl; gölge-kitap kod-hazır). **EDG-2026-003** rampa-p3 — measured→daraldı (P3 öldü; rampa koruması gerçek). **EDG-2026-011** inplay-önceliklendirme — **askı** (PIT-takvim; FMP-402'ye bağlı).
- **EDG-2026-013** mom-turnover — devir-arşiv (etkileşim-tezi düştü). **EDG-2026-012** net-issuance — ARŞİV (yön ters+anlamlı, U-eğrisi). **EDG-2026-014** gross-profitability — ARŞİV (bilgisiz; PIT filed-tabanlı as-of İLK KEZ meşru). **EDG-2026-010** pullback — ARŞİV (bağımsızlık gerçek, kenar yok; ders#3). **EDG-2026-015** vcp-decompose — ARŞİV (çatı bilgisiz; form=bileşen-toplamı ρ=0,95).
- **EDG-2026-001** 52wh · **EDG-2026-002** volume-shock (torun→EDG-017) · **EDG-2026-004** max-filter (yön TERS, kill×2) · **EDG-2026-005** sma-gate (KAPI AÇILMAZ, GÖSTERGE'ye emekli) · **EDG-2026-006** turn-of-month (yön ters) · **EDG-2026-007** residual-momentum (6/6 CI-0-içi; ρ=0,625) · **EDG-2026-008** vol-scaling-overlay (kill#3, iki pencere yönsüz) → hepsi **ARŞİV**.
- **BASE-2026-001** sistem-karnesi (+%2,5/4,5yıl, 2024-bağımlı; huni üç-darboğaz).
- **Retro kuyruk (README):** EAP large-cap **archived** (+9,0bps<30 eşik; PK geçti) · Insider CMP **archived** (pozitif-kontrollü 0) · Short-interest FINRA **archived** (12 hücre 0) · çıkış paketi P1/P2/P3 (K=3) **measured→shadow-accrual** · PEAD/rekonstitüsyon/sektör-takvim **archived** (kaynaklı; kill-list altta).

**⑤ RETIRED çapraz-doğrulama (`research/qc_dogrulama/`, 2026-08-09; üç kaynak):** 8 emekli sembol
(ANSS/DFS/FI/HES/IPG/K/PARA/WBA) — **yerel SP500-üyeliği 8/8 tutarlı** (her sembol delist gününden
önce üyelikten düşmüş, beklenen); **Massive delist-otoritesi 7/8'i gün-güne BİREBİR doğruladı** (vekil→
gerçek taşındı); hiçbir emeklilik kararı ÇELİŞMEDİ. Tek kalan QC-adımı: 1-hücrelik Security Master
delist-olayı fizibilite sondası (artık TEYİT, bilinmeyen değil) — §3-11.

### YAPMA LİSTESİ (kill-list — ölçülmüş/belgeli çürükler; tur harcanmaz; DOKUNULMAZ)

Araştırma-kaynaklı: PEAD (likit büyük-cap'te ölü) · overnight drift (2021 sonrası çöktü) ·
ay-dönümü (ABD'de kayboldu) · sektör-ETF trend (net edge marjinal) · VCP geometrisi (bağımsız
kanıt yok — ölçülebilir bileşenleri zaten skorda) · opsiyon verisi satın alma (öngörü kısa-bacak/
borç-ücreti kanalında) · equity-eğrisi otomatik risk kısma (momentum sistemini dipte kapatır;
yerine DD>1.5×beklenti insan-incelemeli alarm) · fractional Kelly (sabit-R zaten ~çeyrek Kelly;
üç aylık overbetting kontrolü yeter) · derin NN/geniş özellik uzayı (bu veri rejiminde overfit
tiyatrosu) · breadth birincil kapı (yalnız <%20 washout istisnası) · **yerel LLM kurulmaz**
(operatör kararı 2026-07-30: karar yolu deterministik → gecikme argümanı yok; gece yansıması
1-3 çağrı/gün → maliyet/fallback değeri ≈0; VM 2OCPU/12GB'da toplu iş zaten ölür; ileride yalnız
"Y6 toplu API maliyeti ısırırsa + anlaşma-ölçümü geçerse" koşuluyla yeniden açılabilir).
Kendi ölçümlerimizle çürüyenler: breakeven'ı erkene çekme (H1a) · min_score 80 (H2 — dilim
istatistiği tam replay'de tutmadı) · stm21 kısa-vade momentum (devir-koşullusu anlamlı NEGATİF —
Medhat-Schmeling bizde replike olmadı) · knob-bileşik çıkış paketleri mevcut R-yasası altında
(G3a: 3/3 ret — kuyruk kazanır ortalama kaybeder; dolar merceğiyle yeniden değerlendirilecek).

## §5 KARAR GÜNLÜĞÜ (kronolojik; yeni giriş EN ÜSTE — tek satır + tarih; ayrıntı oturum kayıtlarında)

- **2026-08-09 ROADMAP §0-6 MİMARİ YENİDEN-ÖRGÜTLEME (operatör onaylı; İÇERİK KORUNDU — silme/özet
  DEĞİL, yeniden-ORGANİZE).** Eski §1-7 düzeni §0-6'ya taşındı. **Eski başlık → yeni bölüm haritası:**
  eski §1 "ŞİMDİ" GÜNCEL-DURUM bloğu → §1 tepesi; eski §1 gece-vardiyası/denetim-kuyruğu tarihçesi →
  §6 oturum snapshot'ları · eski §2 DURUM PANOSU → §6 snapshot · eski §3 PLAN WP'leri → §1 (aktif: WP-E/
  WP2/WP-U/WP-S/WP-S2/WP-M/WP-D/WP-H/WP-QC/WP-UX/WP-P/WP-L) ve §6 (tamamlanan: WP0/WP1/WP3/WP-G/WP-R/
  WP-K/WP-N) · eski §3 SIRALAMA → §0 · eski §4 YASALAR → §0 · eski §5 YAPMA LİSTESİ → §4 (kill-list) ·
  eski §6 OPERATÖR + §6.1 envanter → §3 · eski §7 KARAR GÜNLÜĞÜ → §5 (aynen). Bitmiş dalgalar (KOVA-B,
  WP-N, dalga-3) §6'da; WP-U/QC keşfi §4 kanıt + §3 operatöre dağıtıldı; kartlar §4 indeksinde. Hiçbir
  bilgi kaybı yok: taşınan bloklar byte-özdeş; her açık kalem §1/§3/§4'te temsil edildi.
- **2026-08-09 EDG-2026-022 ÖLÇÜLDÜ — FINVIZ HARCAMASI GEREKÇESİZ:** de-risk+tavan birlikte %65,84
  (CI >%50) BASKIN; evren bağlayıcı DEĞİL (%34,17). Asıl kaldıraç de-risk rampası/`eff_max_open`.
  Rejim-koşullu KILL#3: chop'ta (nadir %6,7) evren baskın ama genel+trend_up de-risk baskın. Sonuç:
  `FINVIZ_API_KEY` operatör-bloğu (§3-8) DE-RISK edildi — evren bağlamadığı için token parası şimdilik
  gerekçesiz. Otonom kart, blok değil; `docs/KESIF-WP-U-2026-08-09.md`.
- **2026-08-09 EXE-2026-004 (N4) AŞAMA-1 ÖLÇÜLDÜ, AŞAMA-2 DONDURULDU:** üç tüketici ölçütü ölçülebilir
  zarar göstermedi → cf çıkış-tipleri EKLENMEDİ (+0,039R iyimserlik sapma olarak KAYITLI, düzeltilmedi).
  Aşama-2 (çıkış tipleri modeli + TÜM cf tarihi yeniden koşum) eşiğe ulaşılmadı; bakım penceresi şartlı
  (saatler, state'e yazar → canlı worker koşarken YAPILMAZ). Eşikler ölçümden ÖNCE donmuş, DEĞİŞMEDİ.

- **2026-08-09 DÖRT-CEPHE KEŞİF TURU + BAKIM PENCERESİ ONAYI (commit `068a580`):** operatör onayıyla
  dört büyük cephede SALT-ÖLÇÜM keşfi koşuldu (git yasaklı, canlı salt-okunur, `meridian/` dokunulmadı) —
  `docs/KESIF-WP-{U,QC,HD,MKP}-2026-08-09.md`. Her cephede küçük otonom çekirdek + büyük operatör-bloğu;
  en değerli bulgu: **FINVIZ'e para harcamadan ÖNCE "evren bağlayıcı mı" ölçülmeli (EDG-2026-022)**.
  ÖZET: WP-U evren=251=REPLAY_UNIVERSE, FINVIZ %100 ölü · WP-QC FREE hesap açık, ⑤ en düşük blok, LEAN
  dotnet/docker yok · WP-H H9 kapı-dışı yazım (auth._write) + systemd-143 CANLI DEĞİL (N1 ön-şartı) ·
  WP-MKP WP-M 11 açık / WP-K hipotez yok / WP-P P1-P10 kapalı (tek borç RUNBOOK 32 prosedür). **BAKIM
  PENCERESİ ONAYLANDI:** OB-2 systemd exit-143 daemon-reload → OB-1 N1 kanal → OB-4 restart→PBO (M2)
  damgalama çapraz-kaldıraç; N4 cf çıkış-sadakati (saatler, state'e yazar) aynı pencerede. Bloklar §6-8..11.
- **2026-08-09 WP-UX D0-D6 BAYAT-KAYIT DÜZELTİLDİ (git otoritesiyle):** ROADMAP D0🔄/D1-D6📋 gösteriyordu
  ama git D0-D6'nın HEPSİNİN indiğini kanıtladı — v196 `c59dfcc` (D0) · v197 `6025d82` (D1) · v198 `07deab7`
  + v199 `c0d8238` (D2) · v200 `ac86de9` + v197 `7b9158a` (D3-UI/arka) · v201 `9cd27de` (D4) · v208 `11bdc02`/
  `4560362` (D5) · `b71f65b`/`64009ca` (D6) · v229 `6bb2bb9` 16:45 (D3-b F1/F2/F14). Hash'ler doğrulandı.
  `KESIF-WP-MKP` §0 "D0-D6 inmedi" bayat-ROADMAP'e güvenmişti (git yasağı, ~16:30 ölçüm), git ÇÜRÜTTÜ.
  Kalan açık: D3-c altı modül + D3-b F3-F13/F15.
- **2026-08-09 ~09:00 GECE+SABAH DÖRT DAĞITIM İNDİ (v216→v196, son `964696b`):** WP-N kanıt-hızı
  dalgası (v216-v219) + koruma×süpürücü kök düzeltmesi (v220+v221) + dalga-2 sahte-yeşil avı
  (v222-v226) + null-sıfır kapısı (v196). Sistem paper/sağlıklı, otoriter suite yeşil, 4 pozisyon
  korumalı. Kapsam hasadı `docs/SABAH-TRIYAJI-2026-08-09.md` (13/13 gerçek kalem, 0 çürük).
- **2026-08-09 KORUMA ARKI KAPANDI — E1-v2 → N6 çarpışma → v220+v221 kök düzeltme:** E1-v2 (v209-v211,
  TIF gtc + `cancel_open_entries` kadansı) korumayı ölmez kılmıştı; N6 devir tatbikatı v211'in
  bağımsız OCO'sunun 08-07'de süpürüldüğünü ARTEFAKTTAN yakaladı → çarpışma yeniden açıldı; v220
  (P-KORUMA aile kemeri + yön kemeri) + v221 (OCO grup kemeri) süpürücüye korumayı YAPISAL tanıttı.
  CANLIDA md5+broker doğrulandı (4 OCO); davranışsal EOD kanıtı Pazartesi.
- **2026-08-09 N6 DEVİR TATBİKATI KOŞTU — "✅ KAPANDI" yalanı ARTEFAKTTAN yakalandı:** bağlamsız
  ajan (oturum hafızası yok, salt-okunur canlı) devralmayı denedi, koruma kapanış beyanının
  doğrulanmadığını buldu. Ders: bir kalem ancak artefaktı canlıda doğrulanınca ✅.
  `docs/DEVIR-TATBIKATI-2026-08-09.md`.
- **2026-08-09 DALGA-2 SAHTE-YEŞİL AVI (v222-v226) + v196:** "doğru çalışıyor ama kendini yanlış
  anlatıyor" sınıfının son kalıntıları — liveness ölçümü (sprint orphan + öğrenme durması),
  tohum/canlı karne ayrımı, E2 totoloji+kilit, SB-1 boyut makbuzu, universe-unknown alarmı;
  v196 null-sıfır kapısı dalga-2'nin 15 yeni guard'ını SINIFLADI (15/15 meşru, tavan 181→192).
- **2026-08-09 WP-N W1 (v216) SERMAYE BEKÇİLERİ + KARTLAR:** SB-4 damgasız-yazım + SB-3
  `taban_kaymasi` indi (WP-S N3); NAKED_POSITION jetonu ayrıldı (N1 kod); gölge planlı-kol
  (v217, EXE-2026-003) + skill görüş defteri (v218, EDG-2026-019 — figürler kuru-koşu) kartları
  indi. Ölü-mekanizma avının beşinci kovası: `docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md`.
- **2026-08-03 OPERATÖR MANDASI — STRATEJİDE TABU YOK:** "katı hiçbir kural yok; değişmesi
  gereken değişir, kalkması gereken kalkar." Hiçbir strateji bileşeni (çıkış/boyutlama/skor/
  evren/ufuk/yaşayan sinyaller dahil) dokunulmaz değildir; QC-ders hükümleri ve sonraki tüm
  turlar tam yapısal serbestlikle verilir. DEĞİŞMEYEN tek şey karar TERAZİSİ: ölçüm-önce +
  kart + kill-disiplini ("değişmesi gereken"i keyfîden ayıran mekanizmanın kendisi).
- **2026-08-02 ~21:20 EDG-016 KANIT ZİNCİRİ KAPANDI + A1'E DAĞITIM.** Kartın hükmü depodaki yolu
  gösteriyordu ama kod damgası + damgalı betikler scratchpad'deydi; sınıf avı 012–014 kodunu da
  yakaladı → 11 dosya damga-SHA doğrulamalı `wp2_olcum/` arşivine (039c5b8, merge 06e8f60);
  `dagit.sh --uygula` yeşil (bounds/goal canlı=repo BİREBİR · healthz 200 · A1'de 13 dosya
  bayt-özdeş). 70c61f4 token-bekçisi onarımları aynı dağıtımla canlıya indi. Ders günlükte:
  "measured" = kanıt+damga+kod depoda — damga kodsuz yaşayamaz.
- **2026-08-02 ~17:40 GECE KAPANIŞI: KOVA-B CANLIDA — dağıtım kapısı kırmızıyı yakaladı, kök çözüldü,
  A1 yeni kodla.** Kapı açılınca dağıtım-öncesi tam suite İLK KEZ otoriter koşuldu ve 16F/2E yakaladı
  → `--uygula` durdu (kapı çalıştı). Bisect kökü: 0a4453f iki-motor ATR bacağı DOĞRU sıkılaştırması
  v76 fikstür kanıt tabanını 17<30'a düşürdü → onarım FİKSTÜRDE (da6bec3; geometri+16 sembol,
  17→68 işlem, eşik/assert değişmedi). Girişim avı ÇÜRÜTMELİ kapandı: sızıntı ipucu yanlış alarm
  (bounds/goal = c783442 git-çıkışı), 9'lu aile = YÜRÜYEN-AĞAÇ artefaktı (a75a207 statik koşu 0/9);
  DERS: otoriter suite yalnız DONMUŞ ağaçta. Yapısal kilitler: close_engine_position/replace_order_stop/
  cancel_order üç ateş-duvarı listesine (b6273af). Freeze 571a094 → otoriter suite 3752/0 → pencere
  14:00 UTC → birim migrasyonu token-korumalı TEMİZ (journal 0/48) → adım-7 doğrulaması yeşil
  (healthz 200 · 3 birim aktif · scheduler 0,7 dk · evren 251 · fail-notify bayt-özdeş) — BLOKE
  ÇÖZÜLDÜ (25e8824). Kadans dersi kalıcı: log-edit + runbook_uret TEK commit (t3 aynası).
- **2026-08-02 ~04:30 GECE KAPANIŞI: S2R ÜÇLEMESİ TAMAM + KOVA A 9/9 — DAĞITIM OPERATÖR KAPISINDA.**
  S2R-1 kabuk (f7f66fa) → S2R-2 göç 20 bölüm + YASA-6 emekli listesi (9ca0998) → S2R-3 cila +
  bekçi ÖLÇÜLEMEDİ yüzeyi + palet-20 (006cc67). Denetim KOVA A: d50b03b/395920e/8a38248 +
  close_connections yeniden-adı (8ac8e1a, C5 yasa-çivisi isim çakışması). Final tam suite ~3.600
  test SIFIR kırmızı; dagit kapıları [0a-0c]+kuru-koşu YEŞİL. `--uygula` izin-sınıflandırıcısına
  takıldı (2 ret — otonom pencerede canlı-sunucu yazımı; karar operatöre bırakıldı, tek komut:
  `./dagit.sh --uygula`). A1'de C15 canlı hasarı ölçüldü: sprint HER 5-DK poll'de yeniden
  tetikleniyor (99 start, tamamlanma olayı YOK, w_turnover örneklemesi 0) — düzeltme dağıtımla
  iner, kadans kendini bir koşuda onarır; sprint erken-ölümü AYRI şüphe (dağıtım-sonrası izleme).
- **2026-08-02 ~03:30 TAM-SİSTEM DENETİMİ İNDİ (operatör talebi: "bütün bileşenler").** 8 salt-okuma
  denetçi + şiddet≥3'e adversarial doğrulayıcı (34 ajan): **25 doğrulanmış ciddi bulgu** (19 şiddet-3)
  + 22 hafif + 1 çürütülen. Rapor+triyaj: `docs/SISTEM-DENETIMI-2026-08-02.md`. KOVA A (9 sessiz-güvenli
  hata-yolu düzeltmesi) gece kapatılıyor; KOVA B (16 karar-değiştiren: en kritiği C9 çıkış-ayna kopukluğu)
  operatör sabah onayında. Yan kazanım: her-gece-sprint gizemi çözüldü (C15 damga-ezilmesi).
- **2026-08-01 ~17:50 UIUX S1 CANLIDA (otonom gece, pencere-5).** WP0 onaylandı → S1 iki ajanla:
  DTCG tokens.json (eş-doğrulamalı; ham-renk istisnası SIFIR çıktı) + 136-çift kontrast raporu
  (8 beyansız bulgu — B1 merdiven-çöküşü, B6 aynı-renk-iki-seri: refinement-turu adayı) + RUNBOOK
  yüzeyi (50 bölüm kaynak-türetimli, 34 dürüst-boşluk; /runbook auth'lu, alarm→çapa bağlı) +
  g-kısayolları + soru-cümleleri. YAN AV: CSP listesinde eksik virgül — palette.js hiç
  denetlenmemişti. Suite-10 yeşil. Gece nöbetçisi A1'de (trend_book/turnover/yedek).

- **2026-08-01 ~16:15 GÜN KAPANIŞI (tam-güç günü).** Mutasyon %49→%86,8 (28-ajan Workflow) ·
  EDG-016 turnover SUCCESS→KABLOLANDI (bounds'ta bakir düğme) · BASE-001 karne: '+%2,5/4,5yıl,
  2024-bağımlı' + huni üç-darboğaz · sermaye tohum-ayrıştırması CANLI (100k gerçek-canlı taban;
  rampanın hayalet-tepe kusuru dahil) · WP-P pano dönüşümü CANLI (sessiz-hat 16/17'yi dürüstçe
  gösterdi + alarm-KPI ilk gün tepe-aşımını yakaladı + ⌘K palet) · dagit sır-silme sınıfı kapandı ·
  8-K vekili + P9 dışında WP-P tamam. DÖRT pencere, DOKUZ tam-suite, ~50 commit. İzlemede: akşam
  trend_book doğumu + turnover ilk örneklemesi + restart-patlamasının alarm-tepesini şişirmesi
  (yarın: dağıtım-penceresi muafiyeti değerlendirilebilir — bilinçli, ölçülmüş karar ister).

- **2026-08-01 ~16:00 BÜYÜK HÜKÜM GÜNÜ KAPANIŞI.** EDG-016 turnover SUCCESS (yeni yaşayan sinyal;
  net +0,55% @20; survivorship-şerhli) · EDG-013 devir-arşiv · EDG-015 VCP-çatı arşiv (a-fortiori:
  canlı skor kesit-sıralaması @10 TERS — stratejik izleme) · EDG-012/014 arşiv · EDG-011 askı
  (PIT-takvim birikimi başladı) · EDG-010 arşiv+ders#3. WP2 KOMPLE ÇÖZÜLDÜ (EDGAR, operatörsüz);
  WP-K hipotez listesi SIFIR. Karne: 19 kart → 16 hükümlü (14 arşiv + trend-kolu + turnover),
  1 askı, 1 ölçüm-altyapı (EXE), mutasyon-karnesi koşumda. İki pencere daha (sabah H11+gölge-kitap,
  öğlen WP-M/WP-D/pano) — üçü de temiz. Sıradaki: turnover-kablolama turu + H5 ilk skor + akşam
  trend_book doğumu.

- **2026-08-01 ~09:45 PARALEL DALGA İNDİ.** H3 tur-2 seccomp 6.3→2.1 OK · WP-D teyit (kapı 3/4
  aktif dışlıyor; DLTR kaynak-onarımlı) · EDG-010 pullback ARŞİV (lafzen-success/kanıten-kenarsız;
  WP-M ders #3: ham-getiri ölçütü yasak) · PARA-v3 ①② indi (realized_usd + mtm_dd_veto, geriye-uyum
  çivili; ölçek borcu rakamla görünür: n_ölçülen=0) · EDG-005 kapı emekliliği + component_ic aracı
  (kuru: 61/63 hücre; rs cf/havuz ANLAMLI NEGATİF — w_rs=0.35 İZLEME) + mutmut fikstürü (--kisa
  kanıtlı) · .gitignore ölü-negasyon: goal/bounds ilk kez gerçekten versiyonda. Karne 15 ölçülen →
  14 arşiv + 1 yaşayan. AKŞAM PENCERESİ PAKETİ: kod dağıtımı + component_ic --uygula + bounds knob
  düşümü.

- **2026-07-31 ~21:45 GÖLGE-KİTAP TURU KAPANDI.** Trend kolu canlı paralel-defter olarak hazır
  (d3425e2); dağıtım paketi = H11 + SQLite −0.0 düzeltmesi + gölge-kitap (migrasyonsuz düz kod);
  tam suite koşuyor, yeşilse pencere operatöre tek komutla hazır. 23:32 yedek + ~02:00 ilk
  SQLite-gecesi döngüsü izlemede.

- **2026-07-31 ~15:30 EDG-009 TREND-RAFİNE HÜKMÜ.** Rafine üstünlük kanıtlanamadı → ham kol
  incumbent; KALICI PIT ŞERHİ: fazlanın ~yarısı evren-seçim yanlılığı (~6-7p/yıl, D t=2.08
  hayatta); 2021+ = oynaklık, decay değil; eşik-dilbilgisi dersi WP-M'ye. Pozitif kontrol
  0.000000. Kanıt research/olcumler/trend_rafine/. Sıradaki: aylık gölge-kitap Opus turu.

- **2026-07-31 ~sabah WP-G + WP1 HÜKÜM GÜNÜ.** EDG-005 SMA-kapısı ARŞİV (tanı turu: OOS etkisi
  sıfır — fark IS-yankısıymış; temiz pencerede kill#1; "oosonly standardı" WP-M'ye sınıf dersi
  olarak girdi; ci_para kökü: _slim'in pnl_dollars düşürmesi) · EDG-006 ToM ARŞİV (ön-adım, yön
  ters) · EDG-007 residual momentum ARŞİV (6/6 CI-0-içi; residmom≈rawmom ρ=0,63 yapısal; FF3
  verisi yan-kazanım olarak repo'da). Skor: 12 ölçülen aile/filtre → 11 arşiv + 1 yaşayan
  (uzun-ufuk trend). Aynı gün: git kuruldu (H8), SQLite defter-çekirdeği turu sahada (H9).

- **2026-07-31 ~07:00 MÜHENDİSLİK EL KİTABI TURU (operatör dokümanı).** 2024-26 araştırma anketi
  gerçekle çarpıştırıldı → WP-H açıldı. Üç düzeltme: Meridian SQLite-backed DEĞİL (Litestream
  ailesi reddedildi) · git YOK = en büyük boşluk (operatör kararına sunuldu) · systemd 9.2 UNSAFE
  ölçüldü + pano token'ı unit'te düz metin (H3). uv audit temiz + dağıtım kapısına kablolu;
  CLAUDE.md yazıldı. Aynı sabah: EDG-006 ToM ön-adımda arşiv (yön ters −11,8bps) · EDG-005
  "AÇILABİLİR" hükmü mekanizma-kanıtına kadar ASKIDA (pozitif kontrol aslında geçiyor —
  tum-digest artefaktı; tanı ajanı sahada) · EDG-007 residual momentum kartı açıldı, ölçüm ajanı
  sahada (FF3 ingestion dahil).

- **2026-07-31 ~03:00 GECE DALGASI DAĞITIMI (operatör uykuda, tam-yetki).** 6 kod kolu tek bakım
  penceresinde: WP-E + SIP-yasası + pano + BT-1 migrasyonu (95/95 seed damgası) + round-2
  (karantina-v2 8 onarım + bütünlük 61 sembol) + regime üretici düzeltmesi + tick-bekçisi.
  Suite ~2.900/0. İlk canlı kanıtlar: `alpaca_sip_skipped_current_session` + damga sayaçları.
  Gece ölçüm hükümleri: 52wh/volshock/MAX/EAP arşiv (kartlarda gerekçeli), ToM yeni kart,
  WP3.1 4/4 birinci-el, PIT üyelik verisi repo'da. Koşan: WP-R + SMA/ToM.

- **2026-07-31 ~04:00 PLAN WP-KONSOLİDASYONU (operatör talimatı).** Eski §3.0-3.5'in tamamı iş
  emrinin WP yapısına döküldü: örtüşenler emildi (Y2→WP-E · G2-adayları→1.4 kartı · Y3-SMA/VIX→WP-G
  · Y6-transkript→3.3 bileti · Y6-13F→WP-U · G7→1.5 · G3b→WP-R), örtüşmeyenler yeni WP oldu
  (WP-R rampa/çıkış [EN YÜKSEK] · WP-U evren/PIT · WP-K kurulum/aile · WP-M metodoloji borçları ·
  WP-D veri bütünlüğü · WP-L ölçek merdiveni). Kapalılar işaretli: WP0 ✅ · 2.4-EAP ✅ edge-yok ·
  3.2-insider ✅ kalıcı-arşiv. Ön-kayıt metinleri research/cards/'a taşındı; §1/§2 sabah
  konsolidasyonunda tazelenecek (bayat oldukları burada beyan).

- **2026-07-30 TEMİZLİK + KABLOLAMA TURU KODLANDI — DAĞITILMADI (Rol 2).** Ölü-mekanizma avının
  kapanışı; hedef sözleşmesi md.1: "kablola / emekli et / belgele — üçü dışında hiçbir şey kalmaz".
  Dokunulan: `meridian/{watchdog,notify,broker,regime,shadowlaw,api,scheduler,skills,reflect*}.py`
  (*yalnız yorum/belge), `meridian/adapters/{alpaca,fmp,macro,news,insider,finviz*}.py`
  + yeni `tests/test_temizlik_kablolama_v137.py` (57 test) + 5 mevcut test dosyası güncellendi + §6.1
  tablosu + bu not. `hermes.py`/`shadow_model.py`/`sprint.py`/`loop.py`/`analytics.py`/`health.py`/
  `codelaw.py`/`adapters/data.py`/`web/app.js` DOKUNULMADI (HALT delegasyonu `health.set_halt`i
  ÇAĞIRIR, dosyayı DEĞİŞTİRMEZ); **`state/`e YAZILMADI** (doğrulandı: tur boyunca `state/` altında
  hiçbir dosyanın mtime'ı değişmedi); **DAĞITILMADI**.

  **① EMEKLİ EDİLENLER (13 fonksiyon + 2 sabit = 15 ad; her biri çağıran taramasıyla, her biri
  geri-al notu bırakarak).**
  Tarama `meridian/ + tests/ + ops/ + deploy/ + skills/` üzerinde yapıldı ve HER birinde tek eşleşme
  tanımın kendisiydi: `alpaca.paper_client` (SDK sarmalayıcısı — kağıt yürütme REST/httpx yolundan
  gidiyor; `_client` KORUNDU, `live_client`ın tek dayanağı) · `fmp.income_statement` /
  `fmp.search_name` / `fmp.stock_list` (üçü de kota yakabilen, hiçbir karara bağlı olmayan ağ yolu) ·
  `macro.snapshot` / `macro.status` (modül MEZAR TAŞINA çevrildi — `regime.classify`ı sarmalıyordu,
  canlı yol onu zaten doğrudan çağırıyor) · `news.stock_news` / `news.status` / `news.available` /
  `MAX_SYMBOLS` (aynı — mezar taşı; N1/N3 dersleri metinde KORUNDU) · `broker.PaperBroker.
  open_risk_dollars` (ikinci bir "açık risk" gerçeği; canlı tavan R biriminde ve `guard.py`de) ·
  `regime._slice` (tek satırlık dilimleyici) · `shadowlaw.score_eski_yasa` (eski yasanın hükmü ZATEN
  `money_score_detail`in `score_eski_yasa` ALANINDA kayda geçiyor) · `notify.data_quality` (kendi
  docstring'i K1'de zaten "emekli, çağıran eklenmez" diyordu — beyan fiiliyata geçirildi; tek kapı
  `obs.alarm(ALARM_DATA_QUALITY)` ve o zaten susturma penceresi uyguluyor).
  **İKİ AV ADAYI ÇÜRÜTÜLDÜ ve operatör kalemi olarak belgelendi (§6.1):** `MERIDIAN_SUPERVISED`
  (`ops/com.meridian.agent.plist:31` onu KURUYOR → süreç ölümünün operatöre ulaşan iki yolundan
  biri) ve `reflect.propose_deterministic` (Eksen-2 kolu gerçekten koptu — `skills.axis2_cycle`
  devraldı — ama `reflect --auto` CLI'ı README:81'de operatör komutu olarak yazılı).

  **② KABLOLANANLAR (tetikleriyle).** ① Sağlayıcı sağlık kartı → `/api/diagnostics.saglayicilar`
  (finviz/massive/insider/shortinterest/alpaca-veri/alpaca-ticaret; beşinin de sağlık sayacı
  ölçülüyor ve dördünün okuyucusu YOKTU). Ortak biçim + üç dürüstlük kuralı: ölçülemeyen **None**
  (0,0 değil), `son_basari_ts` yalnız `ok is True` iken dolar, kapsam `surec-ici` diye BEYAN edilir.
  ② Y4 toplama → scheduler seans-sonrası kancası, seans başına 1× (`y4_session`, KALICI).
  ③ `validation_report.build/render_text` → haftalık kadans, `state/validation_report.json`,
  `/api/diagnostics.mlops.validation_report`. ④ `massive.verify` → aynı haftalık blok (yazım
  kapısının dayanağı bayatlamasın). ⑤ `massive.reset_cache` → EMEKLİ EDİLMEDİ, **bakım yoluna
  bağlandı**: docstring'in "gün dönümü" gerekçesi GEÇERSİZDİ (iki sözlük de tarihe anahtarlı, bayat
  veri servis edilemez) ama SIZINTI gerçekti (memo `{tarih: {~12.400 sembol}}`, 7/24 worker'da hiç
  boşalmıyordu) → yeni seans kovalaması başlarken temizlenir; memo diskten geri dolar, ağa çıkmaz.
  ⑥ `shadowlaw.variance_drift` (YENİ) → haftalık MEASURED_V3 kayma bekçisi. **Toleranslar
  uydurulmadı**, üçü de kodda yazılı gerekçeden türedi: marj çevriminin YUVARLAMASI
  (`0,02 × margin_scale` hâlâ `MONEY_GATE_MARGIN`e yuvarlanıyor mu), veto marjının kendi gürültüsünün
  DIŞINDA kalması, PARA payının TEK TERİM özdeşliği. Bekçi UYARIR, **sabiti değiştirmez** (operatör +
  Rol 1 kararı). ⑦ HALT tek kapı: `api_halt`/`api_resume` artık `health.set_halt`e delege ediyor
  (kardeş kapı `api_intraday_arm` zaten `set_intraday_arm`e delege ediyordu; `set_halt`in üretim
  çağıranı yoktu — yani kapının "resmî" hâli ölü, kopyası canlıydı). ⑧ `watchdog.EXPECTED` 9 → 17:
  öğrenme turunun dört kadansı (`shadow_fit`/`axis2_cycle`/`opinion_backfill`/`sprint_cadence`)
  nabız ATIYOR ama listede olmadıkları için `report()` onları ARAMIYORDU — nabzı atılıp beklenmeyen
  bir mekanizma, durduğunda MECHANISM_STALE üretmez. Yeni dördü de eklendi. Kısılabilen kadanslar
  (dolgu/sprint) 9 günlük pencerede: kısılmayı arıza sanan bir dedektör gürültüyle susturulur.
  ⑨ **Eksen-2 cf kolu (Rol 1 tasarım kararı, uygulandı):** örneklem kapısı iki kollu oldu —
  `n >= min_n` **VEYA** (`n >= min_n/2` **VE** `n_cf >= 5·min_n`). cf tek başına öneri TETİKLEMEZ
  (gerçek katman ölçülmemişse `avg_r is None` → kol açılmaz); yön hükmü **yalnız** gerçek katmandan;
  cf-destekli satır `kanit: "gercek+cf"` künyesi taşır ve rationale'inde cf payını AÇIKÇA yazar.
  `axis2_diagnosis` beyanı güncellendi ("cf OKUNMUYOR" artık yanlış olurdu) ve yetersiz-örneklem
  kovası ikiye ayrıldı.

  **③ Y4 KABLOLAMASI — Rol 1'in canlı sondası kadansı DEĞİŞTİRDİ (brief eki, aynı gün).** FMP
  ÜCRETSİZ planında ölçüldü: `search?symbol` → **402**, `limit>100` → **402**, `page>=1` → **402**
  (yalnız `page=0` çalışıyor), `date=` parametresi **sessizce yok sayılıyor** (200 + günün verisi).
  Yani `fetch_delta`ın sayfalama yolu bu planda ÖLÜ. Kadans `VARSAYILAN_SAYFA_TAVANI` (40) yerine
  yeni `insider.PLAN_SAYFA_TAVANI` (=1) kullanıyor — 40'lık tavan her gece 39 boşa 402 yakardı.
  402 `obs.log` ile TEK SATIR bilgi olarak geçiyor (alarm DEĞİL: her gece tekrarlayan ve ancak plan
  yükseltilerek çözülebilen bir uyarı, gerçek uyarıları okunmaz yapar). Sağlık kartında
  `plan_siniri: page0-only`. **DÜRÜSTLÜK DÜZELTMESİ:** dosyanın başlığındaki ve
  `codelaw.DECLARED_SINKS`teki "günlük biriktirmeyle 3 yıllık pencere dolar" cümlesinin ÖLÇÜLMEMİŞ
  BİR UMUT olduğu yazıldı — günde tek sayfa = ~100 dosyalama, evren isabeti ~6/100 ve `latest` akışı
  GERİYE derinleşmez, İLERİ akar; o pencere bu yoldan ancak 3 yıl BEKLEYEREK dolar. (`codelaw.py`
  bu turun dosyası değil — oradaki aynı cümle Rol 1'e bırakıldı.)

  **④ SINIF AVI — "kodda örtük zaman/yayın varsayımı" (T+1 kusurunun sınıfı).** Üç aday okundu:
  * **finviz keşif zamanlaması → BULUNDU, BELGELENDİ (davranış değişmedi).** Önbellek anahtarı
    `date.today()`, yani SUNUCUNUN YEREL takvim günü. Zincir günde İKİ çekim yapıyor: biri kapanış
    sonrası kovalamada (`use_cache=False`, doğru), biri yerel gece yarısından sonraki ilk poll'de
    (önbellek tarihi tutmayınca `use_cache=True` bile `discover()`a DÜŞÜYOR). Örtük varsayım:
    "yerel gün sınırı NY seansının (13:30-20:00 UTC) dışına düşer". UTC/Amerika/Avrupa'da doğru;
    UTC+10:30…+14'te yerel gece yarısı seansın İÇİNE düşer ve gün-içi filtre değerleri önbelleğe
    yazılırdı. Koşum yerleri o bantta değil (geliştirme makinesi UTC+3; A1'in TZ'si bu depodan
    doğrulanamadı — systemd birimi TZ ayarlamıyor). Varsayım artık `discover_universe` docstring'inde
    YAZILI. Ucuz çözüm (UYGULANMADI, Rol 1): anahtarı son kapanmış seansa bağlamak — varsayımı
    kaldırır ve günde iki olan çekimi bire indirir.
  * **earnings takvim tazeleme → NET AMA KAPSAM DIŞI (AÇIK).** Ölçüm: tazeleme penceresi
    `[bugün-7, bugün+14]`, kadans haftalık, `BLACKOUT_DAYS = 5`. Normal işleyişte bir sonraki
    tazelemeden hemen önceki asgari ileri kapsama `14-7 = 7` gün > 5 → **2 gün marj**. AMA
    `earnings_calendar_gave_up` (5 deneme) hafta damgasını YAKAR: bir hafta kaçarsa sonraki deneme
    7 gün daha ileridedir → ileri kapsama **0**'a iner ve `in_blackout` herkes için False döner
    (guard FAIL-OPEN, bilanço gününde işlem açılır). Yani örtük varsayım "haftalık kadans hiç
    kaçmaz" ve TEK kaçan hafta marjın %100'ünü yiyor. Sessiz DEĞİL (`earnings_calendar_gave_up` +
    `earnings_refresh_empty` + `coverage().future_dates`). Düzeltilmedi: `earnings.py` bu turun
    dosyası değil ve iki çözüm de (ileri pencereyi genişletmek / pes ederken hafta damgasını
    yakmamak) davranış kararıdır. Not: Nasdaq ucu ANAHTARSIZ ve ~15 istek — pencereyi genişletmenin
    kota maliyeti ≈ 0.
  * **bararchive Redis TTL → AÇIK (mimari karar Rol 1'de).** Ölçüm: `BARS_MAXLEN = 900` (~2 seans),
    `BARS_TTL_S = 172800` (2 gün). TTL'nin KENDİSİ belgeli. Belgeli OLMAYAN: **arıza hâlindeki kayıp
    penceresi**. `archive_frame` `hotstate.ingest_bars` içinden satır-içi çağrılıyor, her istisnayı
    yutup False dönüyor ve `_WARNED` global'i yüzünden SÜREÇ BAŞINA TEK uyarı basıyor; watchdog'a
    bilerek bağlanmamış (gerekçe yazılı: seans-dışı sahte bayat alarmı). Sonuç: sürekli bir arşiv
    arızası tek olay satırı üretir ve Redis çerçeveleri ≤2 günde döndürür → sessiz kayıp penceresi
    ~2 seans. Dokunulmadı: `barsarchive.py`nin kendi notu iki arşivin birleştirilmesini/emekliliğini
    zaten Rol 1'e devretmiş ve `bararchive.py`/`hotstate.py` bu turun yüzeyi değil.

  **⑤ TESTLER.** Yeni `tests/test_temizlik_kablolama_v137.py` — **57 test, hepsi yeşil**: emeklilik
  ("gerçekten yok" + geri-al notu + `_client` korundu), operatör kalemleri (plist ve README kanıtı
  KODLA doğrulanıyor — kaynak kaybolursa test kırılıp kararı yeniden aldırır), sağlayıcı kartı
  (None≠0, `son_basari_ts` yalnız ok iken), Y4 (tetik / kota kısılması / plan sınırı / bir ayak
  düşünce öteki yaşar / damga kalıcılığı), haftalık üçlü (tetik / nabız / hafta kısılması / anahtarsız
  atlama / bekçi sabiti DEĞİŞTİRMİYOR), memo temizliği (tetik + yalnız seans değişiminde + ağa
  çıkmıyor), HALT tek kapı (delege +
  davranış aynı + statik `touch/unlink` yok), watchdog (AST taramasıyla "nabzı atılan her ad
  EXPECTED'de mi"), Eksen-2 cf kolu (cf tek başına tetiklemiyor / birleşik koşul / rationale şeffaf /
  eski yol değişmedi / PROTECTED delinmiyor). Güncellenen 5 dosya: `test_macro_news_audit_v20.py`
  (denetim → emeklilik çivisi, 6 test — dersler mezar taşında korunuyor), `test_gaps_final_v52.py`
  (determinizm çivisi `regime.classify`a devredildi), `test_review_backlog_v98.py` (#7'nin dersi
  emeklilikte de korunuyor), `test_na_revision2_v54.py` (saflık çivisi `fmp.status`a devredildi),
  `test_ogrenme_otomasyonu_v136.py` (cf beyanı çivisi YÖN DEĞİŞTİRDİ: artık kolun SINIRINI kilitliyor).
  TAM SUITE KOŞULMADI (Rol 1'de).

  **⑤b ROL 1 TAM-SUITE TRİYAJI — BAYAT ÇİVİ TAŞINDI (aynı gün, ek görev).**
  `tests/test_agent_efficiency_v9.py::test_axis2_recommendations_ignore_cf_columns` FAILED verdi.
  Çivi KAYNAK-METNİ yasaklıyordu: `recommend_from_attribution` içinde `"cf_avg_r"`/`"n_cf"` dizeleri
  geçemez. **ÖNCE GERÇEK KUSUR MU DİYE SINANDI** (Rol 1'in şartı: cf tek başına tetikleyebiliyorsa
  düzeltme, RAPOR ET). Dört bağımsız sonda, dördü de `[]` döndü:
  ① gerçek katman ölçülmemiş (`avg_r=None`) + cf n=100.000, cf_avg_r=−5,0 → öneri YOK
  ② gerçek n=3 (eşiğin yarısı 4'ün altında) + cf n=100.000 → YOK
  ③ gerçek n=4 ama cf n=39 (eşiğin 5×'i 40'ın altında) → YOK (birleşik koşul gerçekten VE)
  ④ **en sert hâl:** gerçek katman NÖTR ölçülmüş (0,0R), cf katmanı −5,0R → YOK. Yani yön
  karşılaştırması `cf_avg_r`yi OKUMUYOR; cf yalnız örneklem kolunda. → **Tasarım kusuru YOK, çivi
  BAYAT.** Kaynak-metin çivisi bu ayrımı yapısal olarak yapamaz (iki kullanım da aynı dizeyi içerir),
  bu yüzden çivi DAVRANIŞA taşındı ve ÜÇE bölündü: (a) cf TEK BAŞINA öneri üretemez — yukarıdaki
  dört vaka parametrize (eski korumanın YAŞAYAN yarısı), (b) birleşik koşulda öneri üretilir,
  `kanit="gercek+cf"` künyesi taşır ve rationale cf payını + "HÜKÜM gerçek katmandan"ı BEYAN eder,
  (c) cf'siz yol AYNEN durur (`n >= min_n` iken cf'ye bakılmaz, künye `gercek`, rationale'e cf
  cümlesi sızmaz, PROTECTED yeni koldan da delinmez). Eşikler testte SABİTLERDEN okunuyor
  (`sk.CF_REAL_FRACTION`/`sk.CF_SAMPLE_MULT`) — sayı ikinci kez yazılmadı. Dosya: **13 test yeşil**
  (1 kaynak-çivisi → 6 davranış vakası). Modül docstring'inin #3 satırı da güncellendi.

  **⑥ ROL 1'E UYARI — TAM SUITE'TE ÇIKACAK, BU TURUN ÜRÜNÜ DEĞİL.**
  `tests/test_api_contract.py::test_benchmark_relative_beat_flag_is_a_plain_bool` sırayla bazen
  ERROR veriyor: `conftest._no_live_state_writes` "CANLI state'e YAZILDI" diyor. KÖK NEDEN ÖLÇÜLDÜ
  ve bu turun diff'iyle ilgisi YOK: o test `sandbox_state` fikstürü ALMIYOR, yani `analytics.
  benchmark_relative()`i CANLI state üzerinde koşuyor; çağrı canlı SPY bar önbelleğini yüklüyor ve
  `adapters/data.py`nin hayalet-seans onarımı devreye giriyor (`bar_ghost_session_dropped` →
  `bar_cache_repaired`), yani test bir CANLI YAZIM deniyor ve bekçi haklı olarak düşürüyor.
  Doğrulandı: `state/bars/SPY.csv` satır 3752 = **2018-11-22** (Şükran Günü) ve satır 5386 =
  **2025-05-26** (Anma Günü) — ikisi de XNYS'te KAPALI gün, yani gerçek hayalet satır. Kesintili
  görünmesinin sebebi `pytest-randomly`: sıra rastgele ve SPY'ı ilk okuyan testin sandbox'lı olup
  olmaması değişiyor. Bu turda DOKUNULMADI çünkü `analytics.py` ve `adapters/data.py` bu turun
  DOKUNMA listesinde ve iki çözüm de (teste `sandbox_state` vermek / canlı önbellekteki iki hayalet
  satırı temizlemek) ya başka bir iş kolunun dosyası ya da `state/`e yazmak — bu tur `state/`e
  yazmadı. Rol 1'e bırakıldı.

- **2026-07-30 ÖĞRENME OTOMASYONU TURU KODLANDI — DAĞITILMADI (Rol 1).** Operatör mandası: "elle
  tetik beklemeden tam fonksiyonlu". Dokunulan dosyalar: `meridian/{scheduler,shadow_model,hermes,
  skills,analytics,api,sprint}.py` + yeni `tests/test_ogrenme_otomasyonu_v136.py` (27 test) + bu not.
  `loop.py`/`reflect.py`/`watchdog.py`/`web/app.js` DOKUNULMADI; `state/`e YAZILMADI.
  ① TEŞHİS — kusurun adı "eksik çağrı" DEĞİL, **REHİNELİK**. `shadow_model.refit_and_save` (loop.py:796)
  ve `skills.auto_shadow_from_evidence` (loop.py:848) ZATEN çağrılıyordu — ama ikisi de P5_LEARN ⊂
  `daily_cycle` ⊂ "yeni seansın barı geldi" zincirindeydi. Canlı ölçüm: scheduler `last_summary=noop`,
  kapsama 0,172, `portfolio.last_date=2026-07-28` → veri hattı takıldığı gece öğrenme de duruyor ve
  durduğu hiçbir yerde yazmıyor. (Kanıt ki model eğitimSİZ değildi: `shadow_model.json` n_fit=2201,
  brier_train=0,2431, 2026-07-29T21:10Z.)
  ② ANTRENMAN: `shadow_model.maybe_refit()` + `dataset_fingerprint()` + `training_status()`. Tetik =
  model yok VEYA kaynak defterlerin (trades/trade_plans/counterfactuals) boyut+mtime parmak izi değişti
  VEYA `force`. Bütçe = parmak izinin kendisi (fit saf-numpy, LLM kotası harcamaz). Yetki DEĞİŞMEDİ:
  terfi hükmü `evaluate_promotion`ın yazılı kuralı, tek sonucu `shadow_veto`. `n_live=0` DÜRÜST —
  `p_win_shadow` damgası 2026-07-21'de başladı, damgalı 23 planın hiçbiri henüz kapanmadı (95 kapanmış
  işlemin 0'ı damgalı); terfi kod değil VERİ bekliyor.
  ③ DOLGU: `backfill_opinions(max_days=None)` → tavan `hermes.backfill_budget()`ten türer, seans-sonrası
  kadansa bağlandı, `backfill_progress` olayı kuyruğu (kalan gün/satır) yayınlıyor, `watchdog.beat`
  atıyor. Pano düğmesi ELLE HIZLANDIRMA olarak kaldı (artık kendi `max_days`ini vermiyor — tek formül).
  KUYRUK ÖLÇÜLDÜ ve brief'teki 390 sayısı YANLIŞ: dolgu yalnız SONUCU BİLİNEN plana dokunabilir
  (kalibrasyon çifti sonuç ister) → **93 gün / 95 satır** dolgulanabilir; 386 plan görüşsüz ama 291'inin
  sonucu yok. Türetilmiş tavan (kalan 140) = 46/gece → kuyruk ~3 gecede erir.
  ④ EKSEN-2 ÜRETECİ — KİM ÇIKTI, NEDEN SESSİZDİ. İki üreteç var: (a) `skills.recommend_from_attribution`,
  TEK çağıranı `reflect._proposal` (reflect.py:643) ve deftere ancak o öneri `_submit_locked`e
  (reflect.py:706) ulaşırsa yazılıyor — yani üreteç bir HİPOTEZ ÖNERİSİNİN YAN ÜRÜNÜ; hermes'in canlı
  yollarının ikisi de o alanı boş bırakıyor (beyin zinciri hiç doldurmuyor, `propose_virgin_knob`
  BİLEREK `None` yazıyor). (b) `auto_shadow_from_evidence` (H5, bugün eklendi), loop.py:848 → aynı
  rehinelik. ÇÖZÜM `skills.axis2_cycle()`: ikisini de kadansa bağlar, `record_recommendation`ı doğrudan
  çağırır. `reflect.py`ye DOKUNULMADI (Rol 1'in kararına bırakıldı). EŞİK DEĞİŞTİRİLMEDİ — ölçüldü:
  `recommend_from_attribution()` = [] DÜRÜST bir sıfır (korumasız skillerden yalnız vcp n=91 avg_r=0,000
  eşik aralığında; pullback n=4 < min_n=8 ve zaten gölgede). Ama eşiğin YAPISAL körlüğü var ve
  `axis2_diagnosis()` onu sayıyla yazıyor: eşik YALNIZ gerçek katmana bakıyor, `catalog()`ün bugün
  taşımaya başladığı cf katmanını (`n_cf`,`cf_avg_r`) hiç okumuyor → en büyük örneklemli iki skill
  (momentum-burst n_cf=1080, vcp n_cf=1004) gerçek katmanda n=0/n=91 olduğu için üretecin gözünde YOK.
  ÖNERİ (uygulanmadı): eşiğe cf kolu eklenmeli, H5'in üçlü koşulu (cf eşiği + gerçek katman aynı yönde)
  desenini izleyerek.
  ⑤ BÜTÇE ÖZ-AYARI — `hermes.quota_state()` tek türetim yeri. `kalan = AGENT_RPD − agent_budget.json[day]`
  (gün damgası bugüne ait değilse 0); soğuma = `brain_cooldown("agent")`. `backfill_budget = 0` eğer
  soğumada, aksi `max(1, floor(kalan × 1/3))`. Pay 1/3 çünkü canlı yollar (öneri/inceleme/sıralama/
  nous_eval) aynı kovadan içiyor ve ölçülmüş tüketimleri kotanın ~%7'si (day=10/RPD=150) — 1/3 pay o
  tüketimin ~5 katını rezerve bırakır. Env override (`MERIDIAN_BACKFILL_MAX_DAYS`) türetimi DEVRE DIŞI
  bırakır; bozuk değer uyarıyla türetime döner. **BEYAN EDİLMİŞ SAPMA — `search_budget()`:** yönerge
  "soğumada sıfıra" diyordu, uygulanmadı ve nedeni ölçülebilir: `SEARCH_BUDGET` bir LLM değil CPU
  bütçesidir (walk-forward sayısı) ve beyin zinciri sustuğu gece hipotez üreten TEK mekanizma o aramadır
  — sıfırlamak son kolu tam da diğerleri düştüğünde kesmek olurdu. İlişki TERS ve SINIRLI kuruldu:
  taban `SEARCH_BUDGET` (=10), beyin kapalıyken `min(SEARCH_BUDGET_MAX=20, 2×taban)`; asla 0 olmaz.
  ⑥ ÖĞRENME ANTRENMANI (sprint) — Rol 1 ek mandası. `sprint.maybe_start()` + `should_run()` +
  `auto_config()`; docstring'in "Operator-triggered" ibaresi güncellendi. Ölçüm: son sprint 2026-07-22
  (8 gün önce), `learning_scorecard.outcomes_measured=1` ve o TEK satır H00026 (`source: sprint_search`,
  realized_delta −0,0364) — yani karnedeki tek ölçülmüş sonuç gerçekten sprint kökenli. Kadans
  zamanlayıcının **"current" (boşta) dalına** bağlandı, `fresh` bloğuna DEĞİL: `fresh` bloğu aynı
  `advance_once` çağrısında birkaç satır sonra EOD döngüsünü başlatıyor ve ikisi 8 çekirdeği paylaşırdı.
  Kapılar: aktif sprint / çağıranın meşguliyet sinyali (`refetch_chase`) / canlı arama
  (`hermes.SEARCH_PROGRESS`) / gece dilimi [22:00,06:00) / tetik (haftalık 7 gün VEYA 5 taze hipotez);
  her ret ADIYLA raporlanır. Bütçe türetimi ÇEKİRDEKTEN (kotadan değil — sprint LLM ÇAĞIRMAZ):
  `isci = max(2, min(4, çekirdek−2))` (reflect'in kendi formülü), `budget = clamp(3×isci, 6, 24)`,
  `k_max = clamp(1+isci//2, 2, 4)`. Bu makinede (8 çekirdek) formül **bugünkü elle yazılmış varsayılanları
  birebir yeniden üretiyor** (12/3) — ölçülmüş değeri yeniden üretmeyen bir formül türetim değil yeni
  bir sabit olurdu. Override: `MERIDIAN_SPRINT_BUDGET` / `MERIDIAN_SPRINT_KMAX` + pano/CLI düğmesi.
  ⑦ `sprint_runs.jsonl` TERS ORPHANININ KÖK NEDENİ BULUNDU. Kayıtlı teşhis "defter ya hiç doğmadı ya
  07-23 taşımasında kayboldu" diyordu — İKİSİ DE DEĞİL: `sprint_run` çocuk süreçtir ve `MERIDIAN_ROOT=
  <sbroot>` ile koşar, yani defteri KUM HAVUZUNA yazıyor. Üç sandbox'ın üçünde de dosya yerinde
  (921/921/443 B). `sprint.status()` okuyucusu yanlış rafa bakıyordu; kum havuzlarını gezecek şekilde
  düzeltildi (yazarı canlıya yazdırmak izolasyonu delerdi).
  ⑧ KARNE KABLOLAMASI (YASA 6): `hermes_scorecard()` → `kesif_payi` (bugünkü `exploration_share`, tek
  tüketicisi hermes'in KENDİ istemiydi — operatör göremiyordu), `butce` (arama+dolgu türetimleri),
  `ogrenme_otomasyonu`. `learning_scorecard()` → `besleme` bloğu (antrenman durumu / dolgu kuyruğu /
  antrenman sprinti); eski anahtarların HEPSİ yerinde (testle çivili). `/api/diagnostics` → `ogrenme`
  bloğu + `scheduler.learn_session`. **app.js'e DOKUNULMADI** — alanlar API'de hazır, pano turu Rol 1'de.
  Uydurma YOK: 0 ship / 0 terfi / outcomes_measured=1 rakamları AYNEN duruyor; eklenen tek şey "0'ın
  NEDENİ"nin ölçülebilir hâli.
  ⑨ AÇIK BIRAKILANLAR (Rol 1). (a) `watchdog.EXPECTED`e üç satır: `shadow_fit`/`axis2_cycle`/
  `opinion_backfill` (+`sprint_cadence`) — `beat()` atılıyor, veri var, ama MECHANISM_STALE onları
  izlemiyor; watchdog.py bu turun dosya sınırının dışındaydı. Tazelik geçici olarak
  `analytics.learning_automation().nabiz`ta kadansların KENDİ damgalarından ölçülüyor
  (`mechanism_beats.json` beyanlı bir lağım — dışarıdan okumak `codelaw` `stale_sinks` ihlali olurdu).
  (b) **KIRMIZI TEST, BENİM DEĞİL:** `tests/test_sprint.py::test_reflect_once_searches_when_no_claude`
  düşüyor — sebebi BUGÜNKÜ keşif-dengesi turunun `VIRGIN_FALLBACK` yolu: test `dataset.load`u
  ("BARS","IDX") ile ve `search_and_submit`i mock'luyor ama `reflect.submit`i mock'lamıyor; yeni yol
  gerçek `submit`e giriyor ve `backtest.py:147`de `'str' object has no attribute 'set_index'` atıyor.
  `HERMES_VIRGIN_FALLBACK=0` ile test GEÇİYOR → üretim değil FİKSTÜR boşluğu. Testi düzeltmek mevcut bir
  test dosyasına dokunmak demekti (sınır dışı), o yüzden raporlandı. (c) Eksen-2 eşiğine cf kolu (④).
  ⑩ TAM SUITE TRİYAJI — İKİ EK BULGU (Rol 1 sevkiyle, 2026-07-30 gece).
  (a) `test_na_revision_v53.py::test_scheduler_owns_only_its_own_state` BAYAT ÇİVİYDİ, sahiplik ihlali
  DEĞİL. Çivi elle yazılmış bir literal kümesi sayıyordu ve o gün İKİ meşru artefakt eklenmişti:
  `learning_cadence.json` (bu tur) ve `validation_report.json` (eşzamanlı Y4/doğrulama turu). AST
  taraması ikisinin de TEK yazarının `scheduler.py` olduğunu doğruladı (depo geneli sahiplik taraması
  `test_no_module_writes_another_modules_file` yeşil). Çivi, kardeşlerinin desenine (`probgate.META_FILE`,
  `shadow_model.STATE_FILE`) çekilerek adları artık MODÜLDEN okuyor — elle kopyalanmış bir ad, dosya adı
  değiştiği gün çiviyi sessizce yanlış yapardı. 30/30 yeşil.
  (b) **KENDİ SOKTUĞUM GERÇEK KUSUR — SAAT BAĞIMLI SUITE.** Sprint kadansını zamanlayıcının boşta dalına
  bağlarken `advance_once`ın İKİ çağıranı olduğunu gözetmemiştim: daemon `_run` döngüsü VE panonun ELLE
  TİK düğmesi (`api.py:1823`). Saat 22:00'yi geçip gece kapısı açılınca testlerin doğrudan çağırdığı
  `advance_once()` GERÇEKTEN bir `meridian.sprint_run` alt süreci başlattı. Paket 18:00-21:00 arası
  yeşil, 23:52'de kırmızıydı — sıra bağımlılığının daha sinsi kuzeni: gece yarısına kadar görünmez.
  DÖRDÜNCÜ KAPI eklendi (`_thread.is_alive()` → `mesgul:elle_tik`), ve gerekçesi test değil DOĞRULUKTUR:
  operatör "bir tur ilerlet" düğmesine bastığında 4 çekirdek yiyen dakikalarca sürecek bir antrenman
  başlatmayı istememiştir; sprint'in elle tetiği ayrı bir düğmedir (`/api/sprint/start`) ve o hiçbir
  kapıya uğramaz. VM worker (`run.py`) `loop.daily_cycle`ı doğrudan çağırır, etkilenmez. Regresyon çivisi
  `test_elle_tik_ASLA_sprint_alt_sureci_baslatmaz` SAATTEN BAĞIMSIZ (gece kapısı zorla açılır, hüküm
  yalnız daemon ayrımına bakar) ve mutasyon testiyle doğrulandı: kapı kaldırılınca DÜŞÜYOR.
  KAZA CANLIYA DOKUNMADI — kopyalanan state pytest'in tmp `sandbox_state`iydi: `state/sprint/` hâlâ eski
  üç kum havuzu, `sprint_status.json` 2026-07-22'de, koşan `sprint_run` süreci yok, canlı defterde 0
  test artefaktı. Test sayısı 27 → **28**.

- **2026-07-30 ÜRETEÇ KEŞİF DENGESİ TURU KODLANDI — DAĞITILMADI (yarın sabah Rol 1).** Nous N00002'nin
  implementasyonu; dokunulan dosyalar YALNIZ `meridian/hermes.py` + yeni `tests/test_uretec_kesif_dengesi_v135.py`
  + bu not. SORUN (ölçüldü): 41 hipotezin %51,2'si `stop_loss_atr_mult`ta (21 deneme, 0 ship),
  32 düğmenin 18'i hiç hipotez taşımamış; H2 (`analytics.dead_families`) bunu ZATEN ölçüyordu ama
  isteme yalnız kanıt paketinin İÇİNDE, tavana çarpınca düşebilir ham veri olarak giriyordu.
  ① İSTEM: `_user_prompt`ın her iki dalına (şemalı/şemasız) `_exploration_sections()` eklendi —
  (A) ÖLÜ AİLELER (deneme/ship/ölüm sebebi kırılımı/denenmiş değerler + "bu aileden yeni deneme
  için FARKLI bir ret sebebi gerekçelendir" + K/p_required maliyeti), (B) BAKİR DÜĞMELER (H2'nin
  listesi + bounds aralıkları + canlı değer/"unset"). YÖNLENDİRME, kota DEĞİL: kapı tek hakem, beyin
  serbest. Bölümler kanıt paketinin İÇİNDE değil ARDINDA — `_render_pack` tavan taşmasında alanları
  tümden düşürüyor ve bu turun tek çözdüğü şey bu iki bölümün beyne ULAŞMASI. Ölçü: bölüm 2,6k
  karakter; SYSTEM'e HİÇBİR ŞEY eklenmedi (statik sabit + cache_control sözleşmesi duruyor).
  ② DETERMİNİSTİK YOL — ESKİ DAVRANIŞ (okunduğu hâliyle): beyin zinciri boş dönünce `reflect_once`
  TEK akıllı hamle üretmeden DOĞRUDAN koordinat-inişi aramasına düşüyordu; `reflect.propose_deterministic`
  hermes'in yolunda HİÇ çağrılmıyor (yalnız `reflect --auto` CLI'sinde) — yani yuva BOŞTU. Arama sırası
  denenmemiş düğmeleri zaten öne alıyor (`_ucb_rank` → +inf) ama arama sondaları DEFTERE YAZILMIYOR,
  dolayısıyla bakir düğme aramada denense de "hiç önerilmemiş" kalıyor ve kör nokta kapanmıyordu.
  YENİ: `propose_virgin_knob()` yuvayı H2'nin bakir listesinden dolduruyor (değer = bounds ORTA NOKTASI,
  adıma oturtulmuş; no-op ise denenmemiş yarıya bir adım; o da no-op ise sonraki düğme). Guard ÖN-DENETİMİ
  zorunlu (gerçek aylık kota ile): guard'a takılan bir öneri deftere `rejected_by_guard` yazar ve düğme
  HİÇ ÖLÇÜLMEDEN bakir listesinden düşerdi. Bakir kalmayınca/hiçbiri geçmeyince ZARİF düşüş → davranış
  birebir eski hâl. Kaynak etiketi `deterministic:virgin`. Dağıtım anahtarı `HERMES_VIRGIN_FALLBACK=0`.
  ③ ÖLÇÜM (YASA 6): `exploration_share()` — son 12 önerinin aile dağılımı, bakir isabet (öneri kendi
  ailesine defterdeki İLK dokunuş mu), ölü-aile tekrar oranı (H2'nin BUGÜNKÜ hükmüne göre; sapma beyanlı).
  Ölçülemeyen None. TÜKETİCİ: istem bölümünün son satırı + yeni `python -m meridian.hermes --kesif`
  (karneyi basan `analytics.system_telemetry`/`/api/diagnostics` yolları BAŞKA dosyaların malı — bu tur
  onlara DOKUNMADI; panoya bağlama Rol 1'e kalan iş). Canlı ölçüm bugün: son 12 öneride bakir isabet
  10/12, ölü-aile tekrarı 2/12 — yoğunlaşma TARİHSEL (21 stop denemesi eski), kör nokta ise güncel (18/32).
  ④ UYDURMA YASAĞI/TEK KAYNAK: bakir liste, ölü aile hükmü, aile tanımı (`_knob_family`) ve eşik
  (`DEAD_FAMILY_MIN_N`) H2'den ALINIR — ikinci sayım YAZILMADI. ⑤ DEĞİŞMEZLER korundu: HYP_SCHEMA
  geriye-uyumlu (yeni zorunlu alan yok), K/`k_probes` muhasebesi aynı (bakir öneri `probes_tested`
  YAZMAZ → K=1), H4 bütçesi ve guard'lar el değmedi, ship yetkisi yalnız `reflect.submit`
  (h1b yasa-çivisi yüzünden `reflect._proposal` ÇAĞRILMADI, öneri sözlüğü hermes'te kuruldu).
  TESTLER: yeni dosyada 27 test (hepsi geçti); mevcut hermes'e dokunan 20+ dosya koşuldu;
  `codelaw.report()` ok=True / silent_handlers=0 / artifact_violations=0. TAM suite Rol 1'de.
  İKİ FİKSTÜR BOŞLUĞU — ÜRETİM HATASI DEĞİL (Rol 1 tam-suite triyajında buldu, ikisi de düzeltildi):
  `test_sprint.py::test_reflect_once_searches_when_no_claude` ve
  `test_regime_patch.py::test_reflect_once_targets_live_nondefault_regime`. İkisi de `reflect.submit`i
  mock'lamıyordu; yeni bakir hamle GERÇEK backtest'e girip stub/None bar'larda patlıyordu. AYNI onarım
  (a): fikstüre eksik `submit` basamağı eklendi ve İDDİAYA dahil edildi — sprint'te "bakir yol tek
  öneri verir → ship etmez → arama PRODUCTION pencereleriyle devralır", regime_patch'te ayrıca "bakir
  hamle her zaman KÜRESELdir (`@rejim` yok), rejim hedefleme kararı bütünüyle aramaya ait kalır".
  `HERMES_VIRGIN_FALLBACK=0` yamalama seçeneği İKİSİNDE DE REDDEDİLDİ: testi varsayılan-olmayan bir
  yapılandırmada koşturmak, bakir yol bir gün yansımayı yutarsa testleri yeşil bırakırdı.
  SINIF AVI (üçüncü kardeş yok): `reflect_once`a değen 5 test dosyası tarandı — kalan ikisi YAPISAL
  olarak bağışık, şansla değil. `test_hermes_audit_v28` iki testinde de `propose_with_llm` GERÇEK bir
  öneri döndürüyor, yani bakir dal hiç girilmiyor (h1d'de öneri sertifikasız-rejim kapısında düşüyor —
  o düşüş bakir daldan SONRA olduğu için yuvayı yeniden doldurmuyor; kasıtlı: guardrail'in düşürdüğü
  bir yuvayı doldurmak guardrail'i delerdi). `test_hermes_runtime` doğrudan `hermes.reflect_once`ın
  kendisini mock'luyor. Koşum: test_regime_patch 28 + v135 27 = 55 geçti; test_sprint 17 + v135 27 +
  hermes audit/prompt = 79 geçti.
  BENİM OLMAYAN 3 HATA (aynı triyaj çıktısında, dokunulmadı): `test_api_contract` +
  `test_hafta3b_v125` benchmark/bootstrap testleri teardown'da canlı-yazım bekçisine takılıyor —
  yazılan satırlar `bar_ghost_session_dropped`/`bar_cache_repaired` (SPY), yani benchmark yolu
  SANDBOX İÇİNDE koşarken CANLI SPY bar önbelleğini okuyup ONARIYOR. Kanıt bana ait olmadığına dair:
  her iki dosya TEK BAŞINA koşturulduğunda da, `HERMES_VIRGIN_FALLBACK=0` ile de birebir aynı üç hata
  çıkıyor. Ayrı bir tur ister (canlı defteri kirletiyor ve canlı bar önbelleğini değiştiriyor).
  BEYAN (YASA 4): geliştirme sırasında `propose_virgin_knob` bir kez SANDBOX DIŞINDA denendi ve
  canlı `state/events.jsonl`e TEK bir info satırı düştü (`hermes_virgin_proposal`, 17:49Z, satır
  26831) — defter geri düzeltilmedi (ikinci bir yazım daha kötüydü); başka hiçbir canlı state yazımı
  YOK, kalan tüm koşular sandbox'ta.
- **2026-07-30 ~20:35 İST: İKİ TUR A1'E DAĞITILDI (kapanıştan önce).** Kod rsync + uv sync +
  restart; healthz 200, heartbeat taze; `OnFailure=meridian-fail-notify` kurulu dosyaya cerrahi
  eklendi (üretilmiş token korundu, CHANGEME=0); codelaw ihlalleri dağıtım sonrası 0 (panodaki
  kalabalık eski kod/state uyumsuzluğuydu). 07-29 deliği (44/259) bilinçli olarak bu akşamki yoğun
  fazda kapanacak (onarım tetiği fresh-penceresine bağlı; 07-29'un penceresi dağıtım öncesi yanmış).
  Bu gece İLK aynı-akşam denemesi: kapanış+16 dk'da SIP bacağı → beklenti `alpaca_sip` damgalı
  07-30 barları + repair(07-29) + hacim kalibrasyonu bootstrap. VM-dışı yedek çekici Mac'te kurulu
  (LaunchAgent 21:40; TCC: anahtar ~/.ssh/oci-a1.key'e kopyalandı — ~/Documents'ı launchd okuyamıyor,
  duman testiyle kanıtlandı). Operatör kalemi: bildirim kanalı kimliği (fail-notify şimdilik beyanlı no-op).
- **2026-07-30 VERİ KAPSAMA / AYNI-AKŞAM BACAĞI TURU İNDİ (Rol 1 kabulü; tam not:
  oturum scratchpad `veri_turu_notu.md`).** KÖK NEDEN (Rol 1, kanıtlı): bar zincirinin birincisi
  Massive ücretsiz katmanı seansı T+1 yayınlıyor (kanıt `massive_grouped_last.json`: date 07-28,
  fetched_at 07-29 21:15); zamanlayıcının 8×300 sn (~40 dk) bütçesi bu yüzden HEP boş dönüyor,
  seans "atlandı" ilan edilip bir daha onarılmıyordu — 07-29 barı hâlâ 44/259 sembolde, 164
  tarihsel atlama aynı imza. FMP bilgi katmanına tahsis edilince akşam-yayın varsayımı sessizce
  çökmüştü: sistem fiilen T+1 ritmindeydi ve her seans için sahte SEANS ATLANDI alarmı üretiyordu.
  ÇÖZÜM (4 parça): ① `alpaca.same_evening_bars` — birincil `feed=sip` (Rol 1 CANLI KANITI:
  ücretsiz paper anahtarla dünün barı HTTP 200 + konsolide hacim; `delayed_sip` bu uçta "invalid
  feed" → merdivenden çıkarıldı), yedek IEX snapshot + sembol-başına hacim kalibrasyonu (canlı
  ölçüm: IEX hacmi konsolidenin medyan %2,2-2,5'i — ölçeksiz yazım rvol'ü ~40× küçültürdü);
  damgalar `alpaca_sip`/`alpaca_iex`, abonelik reddi 6 sa soğur, ham hata olaya yazılır.
  ② T+1 Massive düzeltmesi otoriter üstüne-yazım — watchdog'a DOKUNMADAN mevcut
  `_changed_rows → _bump_wf_rev` sanctioned yolundan (`bar_source_upgrade` olayı: seans, n, maks
  |Δclose|/c, hacim oranı); dikiş istisnası adlı ve üreticisi kilitli (yalnız bacağın kendi geçici
  barları). ③ Onarım geçidi `data.repair_coverage`: son 5 seansın deliği grouped'la kapanır
  (07-29 deliği ilk turda kapanmalı). ④ Merdiven: sık faz aynen (8×poll), sonra 30→45→60 dk
  seyrek kovalama; TERMİNAL atlama+alarm yalnız SONRAKİ seans kapanışında (imza korundu); geç bar
  `session_bar_arrived_late`. Ölçüm defteri `state/bar_same_evening.json` (beyan edilmiş sapma:
  `data_quality.json`'ı loop her seansta sıfırdan yazıyor — birikim orada yapısal imkânsız);
  tüketici `scheduler.status()["bar_upgrade"]` → /api. Replay yolu bacağı GÖRMEZ. 3 bayat
  yasa-çivisi + v64 dikiş çivisi yeni yasaya taşındı ("pes sınırı" denemeden ZAMANA); v133
  sıra-bağımlılığı fixture ile kapatıldı (kirleten: alpaca `_TRANSPORT` mutlak sayacı). Yeni test
  dosyası `test_ayni_aksam_bacagi_v133.py` (32); NİHAİ OTORİTER SUITE: %100 tamam, 0 fail/0 error
  (~2.500 test). YAN BULGU (ayrı çip oturumunda): ANSS/DFS/FI/HES/IPG bayat sembol şüphesi.
- **2026-07-30 GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU İNDİ + DAYANIKLILIK ÇİFTİ.** Yeni
  `meridian/shadow_lifecycle.py`: varyant başına KALICI kâğıt defteri (`state/shadow_books.json` +
  `state/shadow_trades.jsonl`) — fill → yönetim → çıkış → mark, her gün, canlı akışın taze
  barlarıyla. Kanca v1 ile AYNI (`loop.daily_cycle` → `shadow_variants.record_cycle`; loop'a eklenen
  tek şey `bars=per, index_bars=idx, regime_ok=regime_ok` — ikinci bir bar yükleyici YOK).
  **YASA KOPYALANMADI:** kitap bir `broker.PaperBroker` ÖRNEĞİDİR (fill/gap koruması/likidite
  tavanı/notional tavanı/kısmi satış/bar-içi muhafazakârlık/komisyon-kayma muhasebesi hep
  üretimden), yönetim `strategy.manage_position`, ADV `backtest._adv`, kısma `broker.derisk_mult`/
  `max_positions_at`, tarama+kapı `shadow_variants._signals`/`._judge` (→ `strategy.scan_all` /
  `guard.classify_gate`). **Kopyalanan TEK şey sürücüdür** (`step()`in OPEN→INTRADAY→CLOSE faz
  sırası, kaynağı `backtest.replay` 182-351 olarak yazılı) — replay kendi takvimini ve kendi
  brokerını kurduğu için çağrılamıyordu.
  **TASARIM SAPMASI (bilinçli, Rol 1 briefinden):** V3/V6 `shadow_variants.VARIANTS`e EKLENMEDİ;
  ayrı bir `LIFECYCLE_ONLY` setinde duruyorlar ve payda İKİYE ayrıldı — `k_variants`=4 (KARAR
  sorusu, v1 defteri) ve `k_lifecycle`=6 (PARA sorusu, kitap defteri). Gerekçe: çıkış düğmeleri
  `scan_all`/`classify_gate` yolunda hâlâ HİÇ okunmuyor (v123 çivisi bunu ölçüyor), yani karar
  defterinde V3/V6 hâlâ kontrol koluyla ÖZDEŞ; onları oraya geri koymak 07-30'da tam bu gerekçeyle
  yapılan temizliği geri almak ve V1/V2/V4'ün çoklu-karşılaştırma cezasını SIFIR ölçüm kazancı
  karşılığında artırmak olurdu. Kitapta ise gerçekten ayrışıyorlar. Yan fayda: mevcut v1 çivilerinin
  HİÇBİRİ gevşetilmedi (test dosyasına dokunulmadı).
  **YENİ KOLLAR:** V3 `exit.early_kill_pivot=1` (`early_kill_bars` VARSAYILANDA 1 — iki düğmeyi
  birden oynatmak "hangisi etkiledi"yi ölçülemez yapardı; pivot artık `_judge` yan haritası →
  `fill_entry(pivot=)` → `Position.pivot` yolundan taşınıyor, yani kitapta GERÇEKTEN ateşliyor) ·
  V6 `exit.scale_out_frac=0.5` (YALNIZ frac: `scale_out_r` zaten 2.0 — E4 no-op tuzağı).
  **NO-OP GUARD ÖLÇÜMDÜR, KONVANSİYON DEĞİL:** `noop_arms()` her kolun ETKİN parametre sözlüğünü
  kontrol kolununkiyle OKUNAN anahtar düzeyinde karşılaştırır; ayrışmayan kol turdan düşer
  (obs.warn + `dropped_arms`). Varsayılan tablosu (`LIFECYCLE_READ_DEFAULTS`) bir KOPYA olduğu için
  AST testiyle kaynaktaki literallere çakılı — strategy/broker varsayılanı değişirse test patlar.
  **TOHUMLAMA (Nous N00005):** ilk koşuda son 5 seans aynı `step()` sürücüsüyle geriye doldurulur,
  yalnız defter BOŞKEN; satırlar `seeded: true` taşır ve `ts` GERÇEK yazım anıdır (retro-damga
  yasağı), seans tarihi ayrı alandır. **KARNE:** `--karne` CLI — varyant × {n_islem, ort_R, PF,
  para, maxDD, açık_poz} + V5 kontrolüne göre fark; para sütunu `shadowlaw.ret_c_v3` (probgate'in
  PARA-v3 tek-terim yasasıyla AYNI ölçek), ölçülemeyen değerler None. Kitapların DIŞ okuyucusu
  `shadow_variants` (codelaw YASA 6 zinciri: sl YAZAR → sv OKUR).
  **KİMLİK:** kapanan gölge işlemi `SV-<kol>-<tarih>-<ticker>`; `ledgers.PLAN_ID_RE`/`CF_ID_RE` ile
  eşleşmediği testle çakılı. **ARIZA:** bir kolun patlaması turu düşürmez, kitabı da SİLİNMEZ
  (açık pozisyonları düşürmek gerçekleşmemiş K/Z'yi yok etmek olurdu) — kitap ilerlemez ve arıza
  `last_error`/`failed_days` ile damgalanır.
  **DAYANIKLILIK ÇİFTİ:** yeni `ops/pull-a1-backups.sh` (A1'deki `state-*.tar.gz` arşivlerini bu
  Mac'e rsync'ler — yalnız eksikler, `--delete` ASLA, yerelde 30 gün budama; kurulum komutları
  betiğin başında) + `ops/com.meridian.backup-pull.plist` (LaunchAgent, StartCalendarInterval 21:40
  → Mac uykudaysa uyanınca telafi; hedef ~/AI-Trading, yani ESKİ ~/Documents TCC engelinin DIŞINDA
  — tek kalan temas SSH anahtarının yolu ve okunamazsa betik çıkış kodu 2 ile bağırır). Yeni
  `deploy/oracle-a1/meridian-fail-notify.service` (oneshot; `meridian.service`'e `OnFailure=` ile
  bağlı, `deploy.sh` kuruyor) — süreç ÖLÜYKEN haber verebilen tek katman; kanal yoksa
  `notify.configured()` False → beyan edilmiş NO-OP, birim 0 ile çıkar ve nedenini journal'a yazar.
  **KOŞULMADI/ELLE:** yedek çekici ve LaunchAgent bu turda KURULMADI ve KOŞTURULMADI (ağ+A1 erişimi
  bu ajanın yetkisi dışında) — kurulum operatörde. **OPERATÖR KALEMLERİ:** ① bildirim kanal kimliği
  (`TELEGRAM_BOT_TOKEN`+`TELEGRAM_CHAT_ID` ya da `MERIDIAN_WEBHOOK_URL`) kurulmadıkça fail-notify
  no-op'tur; ② `launchctl bootstrap` ile yedek çekicinin kurulması; ③ A1'e dağıtım (Rol 1);
  ④ gölge-v2 kartının panoya bağlanması SONRAKİ tur (bugünkü tüketici CLI + testler).
  **TESTLER:** yeni `tests/test_golge_v2_yasam_dongusu_v132.py` (27 test: fill+gap koruması, erken
  itlaf, kısmi satış, breakeven, dokunuş çıkışı, uçtan-uca arm→fill, no-op reddi, varsayılan-tablo
  AST çivisi, kimlik ayrıklığı, tohumlama tek-seferliği, karne/PARA-v3, iki payda, sıfır yetki,
  artefakt grafiği, dayanıklılık çifti). Mevcut v123/v125/v57/v59/v60/v122 çivileri KIRILMADI.

- **2026-07-30 5.1 ORACLE TAŞIMA KİTİ HAZIR (yazıldı, KOŞULMADI — kesme kararı operatörde).**
  `deploy/oracle-a1/` altında: yeni `cutover.sh` (yerelden tek komut; sıra **durdur → rsync →
  deploy → token → doğrula**, çünkü koşan worker'dan alınan state kopyası yarım defter taşır),
  yeni `meridian-barsarchive.service` (worker'dan AYRI birim — yereldeki serve.sh/`stop_worker`
  ayrıklığının systemd karşılığı: pano restart'ı bar akışını kesmesin) ve yeni
  `meridian-backup.{service,timer}` (23:30 UTC, 7 gün, yalnız yerel disk). **ÜÇ GERÇEK HATA
  BULUNDU VE DÜZELTİLDİ:** ① `deploy.sh`'ın tohum adımı `serve.sh:16`'daki
  `[ ! -s state/trades.jsonl ]` korumasını TAŞIMIYORDU → rsync'lenmiş CANLI state üstüne
  2022→bugün replay koşabilirdi; kapı birebir eklendi ve iki dalın hangisine girildiği basılıyor.
  ② RUNBOOK B.3'ün `sed` deseni (`DEĞİŞTİR-uzun-rastgele-token`) `meridian.service`'teki gerçek
  placeholder'la (`CHANGEME-long-random-ascii-token`) EŞLEŞMİYORDU → `sed` sessizce 0 dönüyor,
  servis **bilinen bir placeholder token'la** canlıya çıkıyordu; desen dosyadan doğrulandı ve
  değişimin gerçekten olduğu artık denetleniyor. ③ `deploy.sh` **redis kurmuyordu**, oysa
  `hotstate.py`/`barsarchive.py` ona bağlı — `redis-server` apt'ye eklendi (localhost-only
  default'a DOKUNULMADI). **ÖLÇÜLMÜŞ İKİ DÜZELTME:** sunucu 2 değil **4 OCPU** (`nproc=4`, ssh ile
  teyit) → havuz KAPATILMIYOR, `MERIDIAN_PARALLEL_PROBES=1` birime eklendi; ve Redis yokken
  arşivci **ölmüyor, sessizce boşa dönüyor** (`barsarchive.py:343/413` okundu) → `is-active`
  yeşilliği bar yazdığını KANITLAMAZ, birim yorumuna ve doğrulama listesine böyle yazıldı.
  Taşıma-sonrası ölçü listesi eklendi (tabanlar bugün ölçüldü): `pencere_id:"R1"` damgası
  **0/204** satır, PBO `olculemedi`, `hotstate_down` yerel taban **15.860/hafta**.

- **2026-07-30 NOUS SİSTEM-DEĞERLENDİRME KATMANI İNDİ (§3.2'nin ilk kalemi; 33 yeni çivi, canlı
  state'e SIFIR yazım, RESTART YOK).** Operatör yönü uygulandı: "bütün mekanizmaları değerlendirip
  güncellenmesi gerekenleri nous bulmalı." Dört katman: **A** `analytics.system_telemetry` — 12
  bölümlük haftalık paket, HEPSİ mevcut üreticilerden (yeni ölçüm icat edilmedi); **B**
  `nous_eval.haftalik_degerlendirme` — paket + statik görev şablonu, `hermes.chain_text` ile
  YERLEŞİK beyin zincirinden (SYSTEM'e dokunulmadı, AST çivili); **C** `sekil="parametre"` öneriler
  `composite_queue`ya `nous_eval` damgasıyla — **AYRI BÜTÇE AÇILMADI**, H4'ün 3/hafta tavanına tabi
  ve taşan öneri GÖRÜNÜR biçimde devrediyor; **D** çekirdek hakkındaki öneri YALNIZ rapor —
  kuyruğa giden TEK fonksiyon `_kuyruga_yaz`, ilk işi şekil denetimi, ihlal denemesi
  `CekirdekIhlali` + `AUTHORITY_CHANGE` alarmı (AST testi ikinci bir `enqueue` çağrısı türerse
  düşer). **ÜÇ ÖLÇÜLMÜŞ TASARIM KARARI:** ① **şekil beynin etiketine GÜVENMEZ** — kodda yeniden
  türetilir ve etiket EZİLİR; ilk canlı koşuda bu FİİLEN oldu (model bir veto-geri-besleme önerisini
  "tasarim" diye etiketledi, kod `cekirdek_hakkinda`ya çevirdi). İlk test koşusu ayrıca `koprule`nin
  DIŞ süzgecinin aynı alana güvendiğini yakaladı: iç çivi ihlali durdurup alarm basmıştı ama
  `n_parametre` sayacı yalan söylüyordu — süzgeç de yeniden türetiyor artık. ② **kalite kapısı**
  kanıt-atıfsız öneriyi düşürür ve atıf DENETLENEBİLİR (eşleşen telemetri jetonu satıra yazılır);
  ilk test koşusunda kapının kendini geçersiz kıldığı bulundu — `genel` (gerçek bir alan adı)
  "sistem GENEL olarak iyi" cümlesini kanıtlı sayıyordu, tek-kelimelik ad eşiği 9 karaktere çıkarıldı.
  ③ **iki ayrı boşluk sayacı**: "üretici hiç çıktı vermedi" (0) ile "üretici kendi içinde ölçemedim
  DEDİ" (3) — yalnız birincisi raporlansa paket "12/12 doldu, her şey ölçülüyor" yanılgısını verirdi,
  oysa ilk koşuda 6 önerinin 5'i o üç boşluktan çıktı. **İLK KOŞU KUM HAVUZUNDA YAPILDI** (telemetri
  CANLI verilerden salt-okuma derlendi, değerlendirme sandbox'a yazdı): beyin `nous`/gemini-3.5-flash,
  6 öneri üretildi, 6'sı da kanıt atıflıydı (0 düştü), 4 tasarım + 2 çekirdek-hakkında, **0 parametre
  → kuyruğa hiçbir satır girmedi** (bütçe 3/3 kullanılmadı). Sıfır parametre bir arıza DEĞİL,
  muhafazakâr sınıflandırmanın beklenen sonucu: mekanizma dilinde "veto"/"guard" geçen bir öneri
  anayasal sayılır ve rapora gider. Tüketiciler (YASA 6): pano "Sistem önerileri" kartı +
  `/api/diagnostics.improvement_proposals` + `python -m meridian.nous_eval --ozet` + önceki
  önerilerin akıbetinin SONRAKİ prompt'a geri beslenmesi (H1'in mekanizma-düzeyi ikizi; akıbet
  kuyruktan CANLI okunur, deftere retro damga YAZILMAZ). Kadans `scheduler.advance_once`ın haftalık
  bloğunda (`sweep_orphan` deseni) — **CANLIYA RESTART'la iner, bu turda restart YAPILMADI.**

- **2026-07-30 DSR/PBO SERT KAPI İNDİ — "MOD-FARKINDALIKLI" TASARIM (karar #3, operatör onaylı;
  38 yeni çivi, canlı state'e SIFIR yazım, RESTART YOK).** Y1'in advisory hâli kapandı. Tasarım
  MÜHÜRLÜ hâliyle uygulandı ve buraya AYNEN kaydedilir — çünkü asıl karar eşikler değil, **eşiğin
  hangi bağlamda kestiği**:
  ⟨**KURAL MATRİSİ — mod × ölçüm × hüküm**⟩
  | | DSR ölçülü, ≤0,95 | DSR ölçülü, >0,95 | DSR ÖLÇÜLEMEDİ | PBO ölçülü ≥%20 | PBO ölçülü <%20 | PBO ÖLÇÜLEMEDİ |
  |---|---|---|---|---|---|---|
  | **kâğıt** (bugün) | ship GEÇER + `dsr_dusuk:true` damgası | GEÇER | GEÇER + `dsr_durum:olculemedi` | **RET** | GEÇER | GEÇER (veto YOK) |
  | **gerçek-para** (MODE=live + I_ACCEPT_RISK) | **RET** | GEÇER | **RET** (fail-closed) | **RET** | GEÇER | **RET** (fail-closed) |
  **GEREKÇELER KODDA YAZILI, ikisi ayrı:** (a) DSR kâğıtta bloklamaz çünkü **kâğıt evrimi ölçüm
  aracıdır** — ana defterin öğrenme hızını istatistiksel bir uyarıyla kısmak, kanıt üretimini kanıt
  olmadan yavaşlatmaktı; bloklamamak SUSMAK değildir, uyarı damga olarak KAYDEDİLİR. (b) PBO kâğıtta
  DA keser çünkü **aday testi değil SÜREÇ testidir**: aşırı-uydurulmuş bir SEÇİM SÜRECİNDEN çıkan
  aday kâğıda bile inmemeli — kâğıt defter o adayın kanıtı olarak birikir ve süreç bozuksa biriken
  şey kanıt değil gürültüdür. (c) Gerçek-parada ikisi de FAIL-CLOSED: **"kanıt yoksa gerçek para
  kapısı kapalı"** — ölçülemeyen bir kontrolü "geçti" saymak, yapılmamış bir testin sonucunu
  uydurmaktır (UYDURMA YASAĞI'nın kapı hâli).
  ⟨**BUGÜNKÜ DEĞERLER — kural CANLI SAYILARLA okundu**⟩ Canlı defter DSR (95 işlem, N=32 deneme):
  **0,000024** → kâğıtta `dsr_dusuk: true` damgası, **gerçek-para bağlamında RET**. Doğrulama
  defterindeki **122 ölçülü DSR'nin 122'si de ≤0,95** (medyan 0,047, maks 0,193) — yani DSR kâğıtta
  SERT olsaydı bu tur **hiçbir aday** ship edemezdi; (a) gerekçesi bir tercih değil, ölçülmüş bir
  zorunluluk. PBO yürürlükteki pencerede **ÖLÇÜLEMEDİ (0/8 aday)** → kâğıtta veto YOK, gerçek-parada
  RET olurdu. **YAN BULGU (ölçüldü, düzeltilmedi):** defterdeki 124 satırın **124'ü de `pencere_id`
  damgasız** — yani canlı yazar süreç R1 rotasyonundan ÖNCEKİ kodu koşuyor. Sonuç: **PBO tabanı
  restart'a kadar boş kalır ve sert PBO kapısı canlıda NO-OP'tur** (bu turun canlı davranışı
  değiştirmediğinin ikinci kanıtı; restart operatörde).
  ⟨**FAZ-6 KİLİT ZİNCİRİ: DÖRT → BEŞ, ve İLK KEZ MAKİNE OKUNUR**⟩ `health.faz6_kilitleri` —
  ① EDGE kanıtı (5/5) ② SONUÇ hükmü (4/4) ③ Faz-5 çıkışı ④ operatör onayı (INTRADAY_ARM; 5.1
  runtime ön şartı burada, operatörde) ⑤ **DSR>0,95 yürürlükteki pencerede ölçülü ve geçer**.
  ROADMAP'in "dört kilit" cümlesi bugüne kadar hiçbir yüzeyde yazılı DEĞİLDİ — yani bir kilidin
  sessizce düşmesi kimseye görünmüyordu. Bugün **3/5 açık** ve kapalı olan ikisi ③ (Faz-5 çıkış
  ölçümünü üreten kod YOK → fail-closed) ile ⑤ (DSR 0,000024). Zincir SAF OKUMA: hiçbir şey
  silahlamaz, diske yazmaz; Faz 4b/6 emir bacağı yazıldığında ön-koşul kontrolü oraya bağlanır.
  ⟨**KAPI SEMANTİĞİ KORUNDU**⟩ `_gate_eval.passes` DEĞİŞMEDİ ve DSR orada hâlâ `passes` satırının
  ALTINDA üretiliyor (çivi: `dsr_kapi` adı `_gate_eval` kaynağında GEÇMEZ) — sertlik yalnız SHIP
  yolunda. Arama döngüsünü sertleştirmek, ölçüm aracını ölçüm yapmadan kısmak olurdu. İki yeni statü:
  `rejected_by_dsr` / `rejected_by_pbo`; `rejected_by_backtest` kovasına KARIŞMAZ ve `_ledger_stats`
  onları bandit DENEMESİ saymaz (süreç hükmü, o değişken hakkında kanıt değildir — guard reddiyle
  aynı yapısal sebep).
  ⟨**SAPMALAR — üçü de yazılı**⟩ ① `dsr_dusuk` mühürde "true/false" yazıyordu, **ÜÇ DEĞERLİ**
  uygulandı: `None` ⟺ `dsr_durum: olculemedi`. Ölçülmemiş bir DSR'ye `False` yazmak "düşük değil"
  demek, yani yapılmamış bir ölçümün sonucunu uydurmak olurdu (UYDURMA YASAĞI). ② Kilit zinciri
  `health.py`ye kondu (mühür "arming/health yolu" diyordu, mevcut adlandırılmış bir kilit kontrolü
  YOKTU): Faz-6'nın fiziksel anahtarı `state/INTRADAY_ARM` o dosyada yaşıyor ve anahtarla kilit
  listesini iki dosyaya dağıtmak, birinin diğerinden habersiz gevşemesine izin verirdi. ③ Panoda
  hazır bir "Faz-6 hazırlık satırı" YOKTU; 5 kilit doğrulama kartına eklendi (mühür "varsa" dediği
  için yeni bir kart açılmadı).
  ⟨**SUİT**⟩ 2354 → **2392 / 0 / 0** (+38: kural matrisi 16 parametrik hücre + ship yolu 11 + Faz-6
  zinciri 6 + damga/sözleşme/tüketici 5). Canlı worker koşarken tek bayt canlı state'e yazılmadı;
  restart YAPILMADI (yasa canlıya operatörün restart'ıyla iner — PARA-v3'ün ③ borcuyla aynı sıra).

- **2026-07-30 HOLDOUT ROTASYONU "R1" İNDİ (operatör onayı: "holdout rotasyonunu da yap"; 35 yeni
  çivi, canlı state'e SIFIR yazım).** Sınav kâğıdı döndü: **OOS 2023-07-01→2025-12-31 ⇒
  2024-01-01→2026-04-30**, IS başlangıcı AYNEN 2022-01-01, yeni **dondurulmuş holdout
  2026-04-30→2026-07-30** (sıfır sorgu). GEREKÇE ÖLÇÜLDÜ VE TASARIM SIRASINDA BÜYÜDÜ: aynı
  parmak izine §7 yazıldığında 290, Rol 1 tasarımında 367, **rotasyon uygulandığında 434 sorgu**
  (limit 20 → **21,7×**) — yani "biraz daha bekleyelim" maliyetsiz değildi. Çifte kazanç: en çok
  kazılmış [2023-07→2023-12] dilimi Search'ten çıktı (**silinmedi — IS'e geçti**, öğrenmeye açık,
  yargılamaya kapalı: `is_score` 0,0083→**0,0616**) + eski holdout'un ~4 ayı [2026-01→04] taze OOS
  oldu. **DÜRÜSTLÜK NOTU KODA GİRDİ:** eski holdout kabule HİÇ girmedi ama insana RAPORLANDI →
  **YARI-TEMİZ** sayılır, "hiç görülmemiş veri" diye SUNULMAZ (`dataset.ARSIV_GEOMETRILER`).
  ⟨**R1 TABANI, SANDBOX, KARNEYE YAZILMADI**⟩ v3 incumbent iki geometride yeniden ölçüldü (250
  sembol, `load_cached` — canlı barlara tek bayt yazılmadı): **R0 0,0853 / n111 / PARA 0,1311**
  ⇒ **R1 0,0749 / n90 / PARA 0,1005**. R0 sayısı PARA-v3 kabul sınavının 0,0853'ünü **BİREBİR**
  yeniden üretti → motor sürekliliği kanıtlı; düşüş bir kırılma değil, **%12 skor / %23 PARA**
  farkı (maks düşüş İKİSİNDE DE 0,0689 — aynı motor, aynı barlar). **AMA BEDEL ÖRNEKLEMDE VE §7'nin
  TEŞHİSİNE TERS: Search n 90→71, dilim 630→585 gün.** §7 "çıta artık ölçek sorunu değil ÖRNEKLEM
  sorunu (n≈81-96'da P tavanı ~0,66)" diyordu; R1 örneklemi **küçültüyor**, yani P tavanı DÜŞER —
  rotasyon temizliği kanıt hızıyla ÖDÜYOR ve bu takas ölçülmüş bir maliyet olarak yazılıdır
  (kanıt-hızı akışları + gölge-varyant birikimi bu boşluğun karşılığı). Fold'lar n-dengeli kesimle
  kendiliğinden yeniden oluştu: 27/27/28 ⇒ **20/19/22**, avg_r deseni de döndü
  (+0,04/−0,15/+0,29 ⇒ +0,36/+0,21/−0,07). Holdout skoru İKİ pencerede de `None` (min_sample altı —
  dürüstçe tanımsız, uydurulmadı). **SÜREKLİLİK DAMGALARI:** yeni parmak izi
  `da8bdc35…`⇒`a5f205ec…`, aşınma sayacı R1'de **sıfırdan** başlar ("aşınma yok" DEĞİL "henüz
  ölçülmedi" — ek marj 0,01⇒**0,0**, yani PARA-v3 sınavında S2'yi vetolayan kol şimdilik boşta);
  R0 kayıtları **SİLİNMEDİ**, `arsiv_R0` işareti aldı (içerik değişmez — retro damga yasağı),
  arşiv 435 sorguyla ayrı satırda durur ve yürürlükteki sayaca **EKLENMEZ**. Tüm yeni kapı/ön-eleme/
  doğrulama kayıtlarına `pencere_id: "R1"` damgası; habersiz kıyas yasağı ledgers sözleşmesine +
  pano doğrulama satırına yazıldı. **BULUNAN VE KAPATILAN İKİ SESSİZ HATA (rotasyonun kendisi
  doğurdu):** ① `oos_erosion.report()` defterin TAMAMINDA maksimum arıyordu → arşivlenmiş 434'ü "en
  çok sorulan pencere" gösterip ek marjı YÜRÜRLÜKTE sanardı, yani pano kapının uyguladığı marjın
  TERSİNİ söylerdi ② `analytics.validation_trio` PBO'yu defterin TAMAMINDAN hesaplıyordu → iki
  ayrı takvim ızgarasını havuzlayıp gürültüyü "aşırı-uydurma yok" diye okurdu; PBO artık YALNIZ
  yürürlükteki pencereden (canlıda 84 satırın 84'ü R0 → PBO dürüstçe "taban dolmadı" diyor,
  eskiden 84 satırdan sayı ÜRETİYORDU). **BEYAN EDİLMİŞ SAPMA:** holdout sonu "yuvarlanır"
  tasarlandı, **DONDURULDU** — `fingerprint` girdilerinde `holdout_end` VAR, yuvarlanan bir son
  parmak izini her gün değiştirir ve aşınma sayacı hiç birikemezdi (④ ile çelişki); yuvarlanma
  isteği `dataset.holdout_report_end()`te yaşar, YALNIZ insana-rapor yolunda, pencerelemeye ve
  parmak izine ASLA girmez. 2D değerlendiricisi artık "R1 UYGULANDI (2026-07-30)" durumunu bilir ve
  arşivlenmiş 434 yeni bir öneri TETİKLEMEZ (yoksa ölü sayaç her tur "döndür" derdi). **RESTART
  YAPILMADI:** canlı uvicorn (2s+ ayakta) R0 sabitlerini bellekte tutuyor → R1 sonraki süreç
  başlangıcında yürürlüğe girer; karne güncellemesi de gece döngüsünün resmî yolundan/operatör
  onayından geçer (rapordaki hazır blok ÖNERİ).

- **2026-07-30 ROL 1 PLAN DÜZELTMESİ (V6/V7 ajanının bulgusuyla):** gölge-v1 yalnız GİRİŞ kararını
  ölçer → çıkış-düğmeli kollar (V3 scale_out, V6 early_kill, V7 e.k.+s.o.) kontrolle karar-özdeş —
  k paydasını kazançsız şişiriyorlardı; ÜÇÜ DE SETTEN ÇIKARILDI (set: V1/V2/V4/V5, k=4; V2
  kalıyor — stop mesafesi RR-filtresi/boyut yoluyla girişe DOKUNUYOR, sandbox'ta ayrışması
  ölçülmüştü). E1/E4 kanıt birikiminin gerçek kanalı: ① haftalık prescreen yeniden-ölçümü
  (Rol 1 rutini; her hafta ~5-10 yeni işlem defterde) ② gölge-v2 YAŞAM-DÖNGÜSÜ motoru — önceliği
  YÜKSELDİ (çıkış hipotezlerinin tek gölge-ölçüm yolu; §3.2'ye kalem eklendi). Ders: kanıt
  akışının ŞEKLİ hipotezin şekliyle eşleşmeli — giriş defteri çıkış sorusunu cevaplayamaz.

- **2026-07-30 PARA-v3 KABUL SINAVI (k_probes=4, sandbox, 123 dk):** hiçbiri geçmedi (gereken
  P=0.95) AMA yasa görevini yaptı — üç anlatı düzeltmesi: ① E1 erken-itlaf yeni yasada GÜÇLENDİ
  (P 0.561→**0.659**, para_delta **+0.0688** = incumbent paranın yarısı; dd vetosu geçti) ②
  **S2'nin maskesi düştü**: eski-yasa cazibesi (fold 3/3, kuyruk) PARA getirmiyormuş — para_delta
  **−0.0692**, P 0.327; rvol bandı işlem kalitesini değil pencere getirisini yönetiyormuş ③
  G3a-P2'nin eski yüksek P'si (0.742) çift-sayım avantajıymış — yeni yasada dürüst 0.632 (para
  +0.053 + kuyruk −2.28R gerçek ama orta). E4 fold 3/3 sürüyor (P 0.612). SONUÇ: çıta artık
  ölçek sorunu değil ÖRNEKLEM sorunu (n≈81-96'da P tavanı ~0.66) — kanıt-hızı akışları tam bu
  boşluk için; E1+E4 gölge-varyant setine ekleniyor (V6/V7) → canlı kâğıt-kanıt birikimi.
  S2 neden-vetosu notu: aşınma marjı artık PARA ölçeğinde işliyor (sahada ilk görüldü).

- **2026-07-30 BÜYÜKLÜK YASASI YENİDEN TASARLANDI — "PARA-v3" İNDİ (operatör onayı: "1 numaradan
  başla"; 20 yeni çivi + 9 bilinçli güncelleme, yasa GEÇİŞİ YAPILDI).** Kapının karar değişkeni
  değişti: `ΔS` artık YALNIZ paradan türer. `ret_c_v3 = kıs(pencere_bileşik_getirisi /
  ((1+%25)^(span/365) − 1))` — **30-güne indirgeme çarpıtması YOK** (pay ham getiri, ölçek yalnız
  paydada; terim getiride DOĞRUSAL). `dd_c` ve `sharpe_c` SKORDAN ÇIKTI. ÖLÇÜLDÜ: PARA'nın varyans
  payı **%0,3 → %100** (yapısal özdeşlik, çivili), σ(ret_c) 0,0151 → **0,0356 (2,36×)**.
  **KÖK NEDEN ÇİFT-SAYIMDI, ölçek değil** (3b'nin bulgusu): düşüş ve Sharpe HEM skorun varyansında
  HEM ayrı sert vetolarda sayılıyordu; v2 rötuşu (ölçek düzeltmesi) PARA payını yalnız %3,2'ye
  taşımıştı ve 3 ağırlık denemesi de tutmamıştı — o ölçüm kaydı SİLİNMEDİ, v3'ün gerekçesi olarak
  `MEASURED_V2`de duruyor. **KORUMA BİTMEDİ, GÜÇLENDİ:** skordan çıkan düşüş bacağı **DÜŞÜŞ
  VETOSU**na taşındı (`DD_VETO_MARGIN = 0,04`, TEK YÖNLÜ — kötüleşme RET eder, iyileşme HİÇBİR puan
  kazandırmaz, yoksa çift-sayım arka kapıdan dönerdi). Marj iki bağımsız türetimle aynı sayıya çıktı:
  ölçülen σ(düşüş) = 0,0343'ün DIŞINDA **ve** %8 düşüş bütçesinin tam yarısı. Sharpe hiçbir yerde
  AYRICA sayılmaz (fold çoğunluğu + kuyruk vetosu + DSR üç ayrı açıdan kapsıyor) — davranışla
  çivili: toplamı koruyup dağılımı daralttığımızda (Sharpe 2× artıyor) karar skoru DEĞİŞMİYOR.
  **MARJ ÇEVRİMİ σ-EŞDEĞERLİĞİYLE:** `GATE_MARGIN` 0,02 bileşik-ölçekliydi ve karar değişkeninin
  kendi gürültüsünde yalnız **0,107 σ**'ydı; para ölçeğinde aynı σ konumu → 0,02 × (σ_v3/σ_eski =
  **0,1908**) = 0,00382 → adlandırılmış sabit **`MONEY_GATE_MARGIN = 0,004`**. İKİNCİ ÇEVRİM BİLİNÇLİ
  REDDEDİLDİ ve gerekçesi kodda yazılı: "0,02'yi salt parayla kazan" okuması 0,0945 verirdi (25×
  daha sert) çünkü eski yasada o para HİÇ TAHSİL EDİLMİYORDU — aday 0,02'yi tek başına düşüşle de
  aşabiliyordu. Aşınma marjı da AYNI çarpanla para ölçeğine çevrildi (yoksa aşınmış bir pencerede
  aday kârı DEĞİL düşüşünü iyileştirerek cezayı geçebilirdi — çıkardığımız bacağın arka kapıdan
  dönüşü). **TERS GÖLGELEME:** `shadowlaw.py` "v2 gölgesi"nden "ESKİ YASA gölgesi"ne dönüştürüldü —
  eski bileşik hüküm her değerlendirmede AYNI replikasyonlarda ölçülüp `*_eski_yasa` alanına yazılır
  (tek `score_detail` çağrısı; gölge artık BEDAVA), kapı kaydına `yasa_surumu: para_v3` + geçiş
  tarihi damgası basılır, pano satırı "GEÇİŞ YAPILDI · eski hüküm: X" gösterir. Geçiş ÖNCESİ 15 kayıt
  `gecis_oncesi` olarak SAYILIR ama v3 hükmü **ters çevrilmez**: v2 doğrusal bir pertürbasyondu
  (tersinir), v3 üç terimden İKİSİNİ atıyor — tek bileşik sayıdan çıkarılamaz, denemek uydurma olurdu
  (`divergence_row`un ters-çevrim makinesi bu yüzden kaldırıldı). **YAKALANAN SESSİZ MİKTAR HATASI:**
  `predicted_delta` artık PARA, `realized_delta` ise hâlâ BİLEŞİK (rollback yolu) — meta-kalibrasyon
  bu ikisini bölüyordu ve σ oranı 0,19 olduğundan oran sistematik ~5× ŞİŞECEK, sahte bir "öngörüler
  fazlasıyla gerçekleşiyor" sinyaliyle kapıyı YANLIŞ yerde gevşetecekti (hiçbir test kırılmadan).
  Ölçek karışımı artık YASAK ve atlanan çift sayısı beyan ediliyor; realized tarafının para
  ölçeğinde ölçülmesi AÇIK ÖLÇÜM BORCU olarak kayıtta (`olcek_borcu`). SÜREKLİLİK: `score_detail`
  bileşiği RAPOR metriği olarak AYNEN yerinde (karne/tarih/`oos_score` serisi kırılmadı) ve kapı
  kaydında para skorlarıyla AYRI satır olarak durur. LEGACY yol (dilimsiz fikstür) para ölçeği
  hesaplayamadığı için eski 0,02 marjıyla kalır ve damgası bunu `eski_bilesik_marj` diye söyler.
  **YASA CANLIYA RESTART'LA İNER** — bu turda restart YAPILMADI (canlı worker koşuyor); kod
  yürürlükte, canlı süreç bir sonraki yeniden başlatmada yeni yasayı alır.

- **2026-07-30 G3b ÇIKIŞ REFORMU İNDİ (29 test; 4 mekanizma default-off, sıfır-etki çivili +
  anti-tautoloji):** ölçüm (k_probes=5, sandbox): **E1 erken-itlaf ham ΔS +0.0406 ve E4
  (E1+bankalama) +0.0275 fold 3/3 — PROGRAMIN İLK POZİTİF ÇIKIŞ ADAYLARI**; ret sebebi büyüklük
  değil olasılıksal çıta (P 0.56 vs gereken 0.96 — yasa-revizyon dosyasına girdi). E2 yapı-stopu
  ÇÜRÜDÜ (−0.178, CVaR +5.3R) AMA iki ölçülmüş karıştırıcıyla: notional tavanı stopu de-riske
  çeviriyor (1R→0.25R) + R:R filtresi gevşeyip n %60 artıyor — "pivot stopu mevcut tavanlarla
  kötü" (saf hüküm değil). **TIME-STOP EĞRİSİ (en net bulgu): kesiş KISALTILMAZ — gün-15 kovası
  popülasyonun %34'ü ve en kârlı kova (+13.2R; uzatma adayı); sızıntı gün 2-5'te (−18.3R, stop/gap).**
  Rejim-çıkış boşluğu kapatıldı (flat-params'ta olmayan knob'un rejim override'ı sessizce
  düşüyordu → REGIME_EXIT_KEYS izin listesi; sevk yetkisi bilinçli kapalı). Pivot defter alanı
  değil icra girdisi olarak taşındı (differential yasası korundu).

- **2026-07-30 HAFTA 3b + HERMES ETKİNLEŞTİRME İNDİ (43 yeni test; yasa geçişi YOK):**
  **① GÖLGE-YASA v2 ÖLÇÜM MODUNDA** (`shadowlaw.py`): mevcut yasa `passes`i AYNEN üretiyor, v2 her
  kapı değerlendirmesinde ÇİFT hesapla kayda geçiyor (`*_shadow_v2`, tek `score_detail` çağrısıyla).
  Harness E raporunu BİREBİR replike etti (v1 PARA %0,3 / düşüş %82,0 / Sharpe %17,7) → taban
  doğrulandı. v2 (yıllıklandırılmış getiri / **%25 yıllık hedef**, adlandırılmış sabit) PARA payını
  %0,3→**%3,2**'ye çıkardı; **hedef ≥%40 TUTMADI, 3 deneme beyanlı** (0.5/0.3/0.2 → %3,2 ·
  0.5/0.2/0.3 → %4,1 · 0.5/0.25/0.25 → %3,8; en az değişiklik seçildi). **KÖK NEDEN ÖLÇÜLDÜ ve ölçek
  DEĞİL:** getiri/hedef ailesinden hangi ölçek seçilse σ(ret_c)≈0,045-0,050'de kalıyor (yıllıklandırma
  kaldırılsa 0,0481; dolar-beklentisi bacağı konsa 0,0455) ama σ(dd_c)=0,4182 ve σ(sharpe_c)=0,2917 —
  fark PAYDALARDAN (maks düşüş %8 ve 2·min_sharpe=2,4 DAR, target_return GENİŞ). %40 için dd/sharpe
  paydaları 4,5× genişlemeliydi (maks düşüş %8→%36, anlamsız). **YAPISAL BULGU:** düşüş ve Sharpe
  bacakları HEM skorun varyansında HEM ayrı sert vetolarda sayılıyor (3A kuyruk + max_drawdown +
  TAIL_MARGIN_R) — ÇİFT uygulanıyorlar; PARA tek uygulanan bacak. **IRAKSAMA TABLOSU** (14 gerçek
  kapı kaydı + S1/S2 σ-beyanlı, ters çevrimle): PARA-nötr senaryoda v2 kapıyı **SERTLEŞTİRİYOR**
  (σ %9,3 şişer) — tek hüküm değişimi H00032 GEÇER→RET. Her satırda **δ\*** = hükmü döndürecek aylık
  getiri iyileşmesi: H00033 (P=0,799, kıl payı) **%0,038/ay**, S2 %1,22/ay, S1 %2,60/ay.
  **② HERMES PAKETİ H1-H5:** H1 tahmin-isabet bandı (canlı: n=1, bant ÖLÇÜLEMEDİ — tek çift v4
  rollback'i ve **YÖNÜ TERS**, oran −0,614) · H2 ölü aile hafızası (`stop_loss_atr_mult` 21 deneme /
  0 ship = hipotezlerin **%51,2**'si; **defterde HİÇ önerilmemiş 14/28 düğme** satırı; §5 YAPMA
  listesi makine-okunur) · H3 bileşik yol (`composite_queue.jsonl`, guard REDDETMİYOR→kuyruğa yazıyor,
  tek-değişken yasası KALKMADI) · H4 gece kancası (haftalık bütçe **3**, ayrı süreçte nohup deseni,
  döngüyü bloklamaz) · H5 skill öz-yönetimi (PROTECTED beşlisi ASLA; **motor-içi skiller yalnız
  RAPORLANIR** çünkü onlara `shadow` yazmak davranışı DEĞİŞTİRMEZ — kozmetik kayıt reddedildi).
  Kanıt paketi ORTADAN kesilmeyi bıraktı: **alan-düzeyi öncelik** (H1/H2 en üstte) + tavan 1400→6200.
  **③ Y3 DÖRTLÜSÜ** default-off indi (bounds 28→32): SPY 200-SMA yeni-giriş kapısı (zorla tasfiye YOK)
  · sektör notional tavanı · ısı tavanı (3a'nın "YALNIZ GÖSTERGE" ısısının kapıya bağlanma YOLU, kapalı)
  · **VIX/VIX3M: KAYNAK DOĞRULANDI ve YOK** — Massive endeks uçları HTTP 403 NOT_AUTHORIZED, FMP quote
  ^VIX/VIX/^VIX3M/VIX3M dördü de BOŞ → knob indi ama `veri_yok` ile DEVRE DIŞI, oran UYDURULMADI.
  **④ K1 DEVİRLERİ:** MAE karnesi (kazananlar p90 **0,713R** vs eşik 0,70 — kıl payı; kaybedenler
  medyan 1,058R = stop çalışıyor, ama maks 2,437R kuyruk gap'i var) · otonomi sayımı ts-tabanlı
  (400 satır → 30 gün = **26.357 olay**, 66×) · hotstate DOWN_REASSERT throttle (**500 kopma → 1 olay**,
  bastırılan sayılıyor + çırpınma alarmı; K1'in 6.834/24s seli kesildi) · notify.new_plan loop'a
  BAĞLANDI (ham metin kaldırıldı) · shadow_variants CONTRACT'a girdi ve **süreli codelaw beyanı
  KALDIRILDI** (pano/api devri tamamlandı). **⑤ 2B/2C/2D:** benchmark_relative blok-bootstrap'a geçti —
  aralık [−0,1694,−0,0517]→[−0,1868,−0,0378] GENİŞLEDİ ama **2. ölçütün hükmü DEĞİŞMEDİ** (ikisi de
  sıfırı dışlıyor; kayma alanı ve IID kıyası kayıtta) · 2C empirik Bayes: **rejim hücrelerinde τ²=0**
  — yayılımın TAMAMI hücre-içi gürültü, üç rejim de genel ortalamaya (−0,0421R) TAM küçültüldü
  ("chop zararlı / trend_up iyi" GERÇEK katmanda desteklenmiyor); bileşen IC'de 21 hücre, **rvol20@5
  0,2336→0,0667** (w≈0,15) yani G2'nin manşet IC'si aile-çapı küçültmede %71 tıraşlanıyor · 2D holdout
  rotasyonu: en çok sorulan pencere **290/20 sorgu = 14,5× limit → ROTASYON ÖNERİLİR** (uygulanmadı,
  operatör kararı; maliyet: fingerprint değişir, geçmiş p/ΔS karşılaştırılamaz).
  **İKİ ÖZ-ARIZA YAKALANDI:** (a) `catalog()` cf katmanını düşürüyordu → H5 sessizce HİÇ çalışmazdı;
  (b) `st = st or {}` boş sözlükte YENİ nesne yaratıyordu → H4 bütçesi diske hiç yazılmıyor, yoklama
  SINIRSIZ oluyordu (10/10 izin aldı). İkisi de v125'te çivilendi.

- **2026-07-30 K1 KOPUKLUK TURU İNDİ (25 BAĞLA + 10 EMEKLİ; suite 2224/0/0):** panoya: kelly
  (full −0.041 → yarım-kelly 0: overbetting yok ama kenar da yok — SONUÇ hükmüyle tutarlı),
  VaR/CVaR, tazelik rozetleri, rejim-tetik doluluğu (trend_up 57/30 READY, chop 35/30 READY —
  kalibrasyon yetki eşikleri DOLU), sprint son-5, işlem detay çekmecesi. Bağlanan: goal.failure_below
  İLK KEZ ölçüldü (16 gün sonra: −0.13% vs −4% eşik, failed=False) · crosscheck diagnostics'te
  (251/1775/0 uyumsuz) · selfreview haftası 7→66 vaka · verify_hermes SUNUCUYU ölçüyor (autostart
  gerçekten AÇIK) · monitoring filtresi 3/12→türetilmiş · sweep_orphan haftalık takvimde. İki
  öz-bulgu: yorum-satırı okuyucu değildir (AST'li korpus) + test üretim tüketicisi değildir.
  **YENİ GÖRÜNÜR 3 GERÇEK ARIZA:** universe_coverage 164 atlanmış seans (son: 07-28 %18 kapsam —
  FMP kota günü) · event_ledger %91 hotstate_down seli · hotstate 6.834 kopma/24s (reboot sonrası
  çırpınma şüphesi — restart sonrası yeniden ölçülecek). Devirler 3b'ye: mae_r→exit_efficiency,
  otonomi ts-sayımı, notify.new_plan loop kancası, hotstate throttle.

- **2026-07-30 SADELEŞTİRME+KANIT-HIZI TURU İNDİ (38 test; kendi kırmızısı 0):** ① 4a gözlemi
  TÜM planlara — izlenen ticker 0→10 (aç yığın beslenmeye başladı; eod_armed anlamı aynen, 4b
  gölgesi bilinçli yalnız-silahlı). ② `shadow_variants.py` — 5 varyantlı kâğıt-karar defteri
  (kanun çağrılır kopyalanmaz; near_miss üst-kümesiyle nüfus tamlığı; k_variants beyanı; ship yolu
  YOK); sandbox gerçek-döngü doğrulaması İLK AYRIŞMAYI gösterdi (V2 geniş-stop PM adayını
  geometrik kaybediyor). v1 sınırı beyanlı: karar ölçülür, portföy ömrü değil. ③ `prescreen
  --composite` resmî bileşik yolu. ④ barsarchive NOGROUP onarımı + `ops/barsarchive-run.sh`;
  RUNNER BAŞLATILDI (Rol 1, 2026-07-30 ~02:45) — ring 3 günü tutuyormuş: İLK TURDA 15.622 satır /
  33 sembol / 27-29 Tem KURTARILDI, Faz-5 birikimi resmen başladı. ⑤ mrd:price/pos yalnız-yazılır
  EOD kopyaları kapatıldı (geri açma tek satır), mrd:ord ölü beyanı temizlendi. Suite'teki 2 kırmızı
  K1'in /api/hermes emekliliğinden (K1 kapatacak — denetimde doğrulanacak).

- **2026-07-30 ROL 1 DÜZELTMESİ (Hafta 3a E-raporu sonrası — önceki günlük anlatımına):**
  (1) "Bileşik skor kuyruk-kazananları reddediyor" anlatımı YANLIŞ popülasyondaki gösterge
  sayıya (Δoos_score) dayanıyordu — kapının gerçek karar değişkeni P(ΔS>0)/SEARCH-blok
  yeniden-örneklemesi ve S2 o değişkende ortalama **+0,062 DAHA İYİYDİ**; ret sebebi terim değil
  ULAŞILAMAZ ÇITA (K=2'de gereken ΔS≈0,24 = incumbent skorunun 1,85 katı; σ'nın %82'si düşüş
  gürültüsü). S1 istisna: liyakatle reddedildi (ΔS −0,169 + kuyruk kötü). (2) Önceki G3a/S2
  "CVaR −2,2…−3,5R" rakamları DELTA'dır (iyileşme), absolut değil. (3) DSR canlı defterde
  **1e−06** (N=321 deneme, Sharpe negatif) — "beceri kanıtı yok" artık deflasyonlu sayıyla
  resmî. BÜYÜKLÜK YASASI REVİZYONU 3b'de GÖLGE-YASA olarak ölçülecek (çift hesap + ıraksama
  tablosu; canlı geçiş sabah operatör görünürlüğüyle).

- **2026-07-30 SKILL TEMİZLİĞİ İNDİ (suite 2122/0/0):** 37/68 klasör `skills/_emekli/`ye
  (22 emekli + 15 birleştirilen; silme yok, README'li geri-getirme yolu); registry 36 kayıtta
  retired damgası + 17 bayat last_run temizliği + 8 aktivasyon koşulu; skills.py zincirlerinde
  declared-only 26→14 (P1 12→7, P3 3→1, P5 9→4); PROTECTED beşlisi + hermes preload'ları dokunulmadı.
  Canlı-worker yarışı yakalandı ve kalıcı çözüldü (anahtar-kapısı arşivli kaydı yeniden
  enable ediyordu — 8 kayıtta kapı adaylığı kaldırıldı, özgün değer retired_requires'ta).
  breakout-planner sezgileri docs/G3B-CIKIS-REFORMU-NOTLARI.md'ye (G3b turunun girdisi).
  Yüzey-dışı bayat metinler (landing "66 skill" vb.) için görev fişi açık.

- **2026-07-30 G1 PİLOTU v2 SONUÇLANDI (Massive zinciri, FMP'ye sıfır dokunuş; 394 mid-cap vs
  250 büyük-cap, AYNI 2-yıl pencere, haftalık örnekleme; n=38.8k vs 24.7k):** McLean-Pontiff
  beklentisi ("mid-cap'te IC daha yüksek") BU PENCEREDE DOĞRULANMADI — rvol20 büyük-cap'te ~2×
  GÜÇLÜ (0.053✓ vs 0.024✓ @5bar); mom12_1 iki evrende benzer (0.045-0.049✓ @20); rvol bant deseni
  mid-cap'te de replike (1.5-2.0 tatlı nokta +2.03%). HÜKÜM: evren genişlemesi sinyal-kalitesi
  vaat etmiyor — kalan değeri yalnız FREKANS/çeşitlendirme; önceliği near-miss bulgusundaki
  hacim-eşiği takasına (mevcut evren İÇİNDE ~3.4× havuz) devretti. G1 genişleme kararı: giriş
  kapıları yeniden ayarlanana dek BEKLET (kaydedilmiş efor). Kısıtlar: 2-yıllık tek rejim
  penceresi + koşulsuz örnekleme — kırılım-koşullu popülasyonda tablo farklı olabilir.

- **2026-07-30 HAFTA 3a İNDİ — dolar merceği + kuyruk + ısı + doğrulama üçlüsü; suite 2122/0/0 (bu turun 61 testi dahil).**
  **1B SONUÇ HÜKMÜ** (`analytics.result_verdict`, EDGE'in ikizi, panoda yanındaki kart): canlı
  hüküm **"SONUÇ: 0/4 sağlandı (4 sağlanmadı) — para kanıtlanmadı"** — işlem başına $−58,34
  (blok-bootstrap %95 CI **[−137,75, +14,53]**, sıfırı İÇERİYOR), PF 0,567, maks düşüş %8,04,
  net −$5.542 vs ödenen friksiyon $581. Friksiyon İKİ KEZ kesilmez (`pnl_dollars` zaten net;
  `costs` yalnız 4. ölçütün kıyas tabanı). **3A KUYRUK** kuzey yıldızının 5. ölçütü oldu → hüküm
  artık **"1/5 sağlandı (1 zayıf, 2 sağlanmadı, 1 ölçülemedi)"**; kuyruk SAGLANMADI çünkü CVaR%5
  −1,16R (taban −1,5R) GEÇİYOR ama düşüş %8,04 > %8. **İKİ GERÇEKLİK DÜZELTMESİ:** (a) maks düşüş
  kapanmış-işlem eğrisinde %5,70, GÜNLÜK M2M eğrisinde %8,04 — kapanmış eğri tek başına okunsaydı
  iki hüküm de eşiği "geçmiş" görünürdü (denetim #6); (b) IID bootstrap CI'ı [−116,86, −0,00] ile
  sıfırı kıl payı dışlıyor, blok bootstrap içeriyor — IID okuma "kaybettiğimiz kanıtlandı" derdi.
  **3B ISI** `portfolio_heat` (anlık 0,0% — açık pozisyon yok) YALNIZ GÖSTERGE, hiçbir kapıya bağlı
  değil (test bunu guard/broker/reflect/loop/arming taramasıyla çiviliyor). **Y1** DSR/PSR +
  PBO/CSCV + `validation_ledger.jsonl` (D1) — hepsi ADVISORY, passes semantiği DEĞİŞMEDİ; canlı
  defterde **DSR 1e−06** (N=321 = 289 aşınma sorgusu + 32 k_probes; PSR(0)=0,027), PBO 0/8 adayla
  OLCULEMEDI. **E RAPORU — ÖLÇÜNÜN ÖLÇÜMÜ, KAPININ GERÇEK KARAR DEĞİŞKENİ BULUNDU:** olasılıksal
  yasada `oos_score` karşılaştırması karar VERMEZ (o tam-OOS bir GÖSTERGE sayısıdır); karar
  `P(ΔS>0) ≥ 1 − 0,20/K`dır ve ΔS, bileşik skorun SEARCH dilimi blok-yeniden-örneklemesidir.
  Canlı defterde ölçüldü: ΔS varyansının **%82'si düşüş terimi, %17,7'si Sharpe, %0,3'ü PARA
  terimi** — yani büyüklük kapısı fiilen bir düşüş+düzgünlük kapısıdır. σ(ΔS)≈0,19 ⇒ P=0,90 için
  gereken ortalama ΔS ≈ **0,24**, incumbent'ın TÜM skoru 0,1309 iken. S2 (fold 3/3, kuyruk −2,26R
  daha iyi, n 98→106) P=0,629 ile reddedildi — K=1'de bile (0,80) geçmezdi. Ayrıştırma
  `segment_score` docstring'ine düz yazıyla girdi; her resmî kapı değerlendirmesi artık
  `oos_components`i deftere yazıyor (bu borç kapandı).

- **2026-07-30 NEAR-MISS ÖLÇÜMÜ (ilk kez; n=4.988 vs girilen 2.102):** kılpayı elenenlerin ileri
  getirisi girilenlere ÇOK yakın — @10bar fark YOK (+0.453% vs +0.430%), @20bar mütevazı fark
  (+0.90% vs +1.31%, CI'lar sınırda örtüşür) → giriş eşiklerinin marj değeri zayıf; filtreler
  masada büyük havuz bırakıyor. KIRILIM: engelleyicilerin %85'i **hacim eşiği** (4.243 aday;
  rs 1.217, skor 690, uzamış 675). Bileşik skor IC'si HER İKİ nüfusta da ≈0/negatif (near-miss
  @10 anlamlı -0.034) — skorun sıralama körlüğü üçüncü bağımsız popülasyonda teyit. ADAY DOĞDU
  (prescreen kuyruğuna, dolar merceği indikten sonra): "hacim-eşiği gevşet + rvol-bant filtresi
  koy" bileşiği — replike olmayan volume_ratio kapısını, doğrulanmış rvol bandıyla TAKAS eder;
  frekansı ~2-3× büyütme potansiyeli, kalite bekçisi bantta.

- **2026-07-30 MASSIVE ENTEGRASYONU İNDİ — YAZIM modunda, suite 1980/0/0 (TEMİZ SAYIM).**
  Zincir: massive(grouped) → massive_hist(≤2y) → FMP → cboe → nasdaq; derin tarih Massive'e hiç
  sorulmaz. Günlük bar yenilemesi **250 çağrı → 1** (eski maliyetin kanıtı: 07-27'de calls_today=251
  "Limit Reach"). Canlı doğrulama GERÇEK anahtarla: 320 örtüşen bar / maks sapma 1.3e-05; canlı
  çapraz-kontrol defteri 251 sembol / 450 kıyas / 0 uyumsuzluk. İKİ GERÇEKLİK DÜZELTMESİ: MCP
  ölçümümdeki "0.000%" küçük-örneklem yuvarlamasıydı (gerçek ölçek ~1e-5) ve kıyas tabanı FMP
  değilmiş — bars_source: cboe 192 / nasdaq 59 / **FMP 0** (önbelleği son dönemde yedek zincir
  besliyormuş). Tur 6 GERÇEK HATA da düzeltti: tarih-yok-eden corporate-action reset yolu (tek
  artımlı bar 250 barlık önbelleği 1 satıra indirebiliyordu), tasarrufu sıfırlayan aynı-gün tarih
  hatası, kesinti çoğaltıcısı (memoizasyonsuz 250×4 retry), 30-günlük sessiz bayatlık kapanı,
  gürültü tabanına oturan alarm eşiği (0.1%→0.5%), seam-defteri kirletme riski. Kalan tek iş:
  api.py Test-düğmesi kablolaması (3 satır — ajana verildi).

- **2026-07-30 Y4 veri katmanı indi** (63 test yeşil, kendi kırmızısı 0): `adapters/insider.py` —
  Form 4 akışı sembol-BAĞIMSIZ `latest` sayfalarından (~3-8 çağrı/gün; sembol-başına yol 250
  olurdu), yalnız P/S kodları nete girer (KO'daki icra-et-ve-sat vakası naif okumada "75k ALIM"
  görünürdü — engellendi), sınıflama 3-yıl penceresi dolana dek DÜRÜST `siniflanamadi` ("bu dosya
  sinyal değil kapsam ölçümü" notu dosyada); BULGU: `insider-trading/search` ücretsiz planda 402
  (plan sınırı) → geçmiş derinleştirme yalnız günlük birikimle. `adapters/shortinterest.py` —
  FINRA anahtarsız (FMP kotasına sıfır etki), 250/250 eşleşme, kendi DTC'si ile FINRA DTC'si AYRI
  raporlanır, float kaynağı yokken si_yuzde_float=None. Suite'te kalan 21 kırmızının tamamı
  kanıtla Massive turunun yarım dosyalarına ayrıştırıldı.

- **2026-07-30 SKILL DENETİMİ (68/68, 10-ajanlı workflow; tam tablo tasks/w4fkdamk2.output):**
  Dağılım: **22 olduğu-gibi** (koruma katmanı PROTECTED beşlisi + hermes preload çekirdeği fiilen
  çalışıyor: backtest-expert 114 proposal çağrısında bağlamda, data-quality-checker 14/14 koşuda
  gerçek-invoked) · **22 EMEKLİ** (programa hizmet etmeyen aileler: temettü/kanchi üçlüsü, COT,
  opsiyon, pair-trade, teknik-görsel, skill-oto-üretim — hiçbirinin §3 kalemi ve kullanım izi yok)
  · **16 BİRLEŞTİR** (işlevi motor soğurmuş ya da ikizi var: breakout-planner→strategy.py yolu,
  breadth ikilisi→Y3, edge-* zinciri→orchestrator) · **8 ÖLÇÜMLE-AKTİVE** (programa eşlendi:
  theme-detector→G5 · uptrend-analyzer+ibd-distribution-day→Y3 · parabolic-short→G6 ·
  edge-orchestrator→G4/Y1-sonrası · canslim→FMP anahtarı+helper şartlı · economic-calendar→Y3 ·
  strategy-pivot-designer→Aşama 6). Yapısal bulgular: registry'nin eski "invoked" kayıtları
  2026-07-15 dürüstlük düzeltmesi ÖNCESİ yalanın kalıntısı; kayıt-zincir çelişkileri (P5_LEARN
  beyanlı ama zincirde adı olmayan skill'ler) belgelendi. AKSİYON: "skill temizlik mini-turu"
  §3.2'ye eklendi (emekli 22 → disabled+arşiv klasörü, birleştirmeler, registry dürüstlüğü).

- **2026-07-29 gece — S1/S2 bileşik skor kapı sınavı: İKİSİ DE GEÇMEZ.** S1 "yeni çekirdek"
  (rvol-bant ağırlıklı): Δ**-0.081**, fold 2/3, kuyruk KÖTÜ, P=0.19 → bileşen-IC kanıtı sistem
  düzeyine TAŞINMADI (çıkış darboğazı + w_mom popülasyon kayması; rvol sinyal olarak gerçek ama
  skor ağırlığı olarak değil). S2 "eski + min_rvol 1.5": Δ-0.046 AMA **fold 3/3 kazanıyor + CVaR
  -2.26R + n 98→106** ve bileşik skor yine düşük → G3a'dan sonra ÜÇÜNCÜ vaka: fold/kuyruk kazanan
  adayı büyüklük yasası reddediyor. HÜKÜM: hiçbir şey ship edilmez (kapı hakem); Hafta 3'ün dolar
  merceği (SONUÇ HÜKMÜ) artık kritik yol — S2 + G3a paketleri o mercekle YENİDEN değerlendirilecek;
  ayrıca "bileşik oos_score neyi ödüllendiriyor" ayrıştırması (ölçünün ölçümü) Hafta 3'e eklendi.

- **2026-07-29 KOTA TAHSİS POLİTİKASI (operatör):** bar verisi → Massive (grouped-daily günde 1
  çağrı; sembol-başına yakın-dönem yedek: massive→fmp→cboe/nasdaq; derin tarih 2021+ FMP'de kalır);
  **FMP kotası BİLGİ KATMANINA ayrılır** (temel/float, insider, kazanç takvimi, haber, transkript,
  13F — skill'lerin motoru). Gerekçe: aynı gün FMP birincil anahtar kotası G1 çekimiyle doldu
  (yedek anahtara rotasyon çalıştı — ilk saha testi). Ayarlama-tutarlılığı MCP ile ÖLÇÜLDÜ:
  37 kıyas / 2 tarih (temettü ex-pencereli) → 0.000% fark → Massive YAZIM modunda bağlanır.

- **2026-07-29 C2 bar arşivi indi** (barsarchive.py, 33/33): kendi "archive" consumer-group'u,
  fsync-sonra-XACK crash-safety, (ticker,t) idempotens; barfeed'e dokunması AST testleriyle yapısal
  olarak imkânsız. **Rol 1 kararı — örtüşme:** mevcut `bararchive.py` (hotstate içinden tek-deneme
  yazan, hatayı yutan eski yol) EMEKLİYE ayrılacak; `barsarchive` kanonik Faz-5 arşivi (dayanıklı).
  Emeklilik + `intraday_bars/`→`bars_intraday/` tekilleştirme sonraki mini-tura. Tur sırasında bir
  test kazası canlıya 16MB sızdırdı — geri taşındı (scratchpad'de), teste bekçi eklendi; canlı
  Redis'te atıl `archive` grupları kaldı (zararsız; runner başlarken karar: kabul ya da destroy).
  Yan bulgu: conftest bekçisinde yapısal delik (ham open() + alt dizin körlüğü) — görev çipi açıldı.

- **2026-07-29 G2 implementasyon turu (Rol 2, SIFIR ETKİLİ):** rvol20/mom_12_1/residual_momentum +
  bant-üçgen (1.75±0.75) ve yüzdelik-rütbe skor şekilleri üretime indi; üç bileşen plan/aday
  satırında ALAN oldu (`notes` metnine gömülmedi); `entry.w_rvolband`/`entry.w_mom`/`entry.min_rvol`
  bounds'a **varsayılan 0** ile eklendi (strategy.yaml'a dokunulmadı — canlı skor 20-sembollük çivi
  testiyle G2 öncesiyle BİREBİR); component_ic 4→7 bileşen ve kum havuzu koşusunda **rvol20 gerçek
  katmanda @5 +0.234✓ @10 +0.219✓** — gerçek defterin İLK anlamlı bileşeni. S1/S2 ölçümü sırada.
- **2026-07-29 G3b ön-kanıt (kapanış-konumu/pivot/gap, cf n≈2100):** kapanış-KONUMU sürekli sinyal
  olarak SIFIR (IC ≈ 0 her iki katman — Zarattini kuralının aralık-konumu biçimi bize taşınmadı);
  **pivot-ALTI kapanış kısa ufukta gerçek negatif işaret** (@5bar -0.74% vs pivot-üstü +0.32%,
  n=302; @20'de kısmen toparlar) → erken-itlaf yalnız "pivot-altı kapanış" biçiminde savunulabilir,
  PnL etkisi G3b replay'inde ölçülecek; **BONUS: gap'li kırılım kalite işareti** (@20bar +2.30%
  vs gapsiz +0.73%, n=841) → G5 önceliklendirme + meta-labeling ortogonal özellik adayı.

- **2026-07-29 G3a bileşik çıkış ölçümü:** P1(stop3.0+bank1.5R+BE0) Δ-0.036 · P2(stop3.0+BE0)
  Δ-0.030 · P3(stop2.5+bank2R) Δ-0.043 — üçü de fold 1/3, P≈0.63-0.68 GEÇMEZ; kuyruk hepsinde
  büyük iyileşme (CVaR -2.2…-3.5R). Ders: R-birim önyargısı + dolar merceği ihtiyacı (§4).
- **2026-07-29 G2 ölçümü (1.4 sonrası ilk adım):** rvol20 projenin İLK çift-katman-anlamlı bileşeni
  (gerçek @5 IC .234✓ @10 .219✓; cf @10 .047✓ @20 .062✓); bant doğrulandı (cf @20: 0.8-1.5→-0.5%,
  1.5-2.0→+1.84% n=955, 2.0+→+1.44%); mom12_1@20 cf +0.055✓; rmom zayıf ns; stm21 çürüdü.
- **2026-07-29 1.4 KARAR KAPISI (operatör):** ağırlık ayarı değil G2 YENİDEN İNŞASI. Gerekçe:
  gerçek 0/12 anlamlı; cf'te rs@10 −0.047 ve prox 3 ufukta anlamlı NEGATİF (ağırlıklarıyla ters),
  eski vol replike olmadı; tek anlamlı pozitif tight@20 +0.049.
- **2026-07-29 kimlik mini turu:** suite 35 kırmızı + 1 error → **1805/0/0**. Kök: auth.AUTH_FILE
  import-anı config.STATE bağlaması (geç bağlamayla 21/26 kapandı) + _FAILS sıra sızıntısı.
  Kimlik uçları api.KIMLIK_UCLARI tek kaynağında; ?token= kaldırımı çivili; auth.py hijyen
  istisnası gerekçeli; hermes iplik önle+yakala muhafızı. İkiz checkout YOKMUŞ — symlink + 124
  bayat bytecode (temizlendi, çivili).
- **2026-07-29 Hafta 2 turu:** EDGE hükmüne ANLAMLILIK katı (ZAYIF durumu; canlı 2/4→**1/4**) ·
  bileşen IC cf katmanı + Fisher CI · eşik eğrisi (80'de +0.066R ama CI canlı eşikle örtüşür —
  fark gösterilemedi) · KÂR ŞELALESİ (MFE +0.96R → çıkış −0.99R → friksiyon −0.02R → net −0.04R;
  sızıntı ÇIKIŞTA; çıkış verimi: stop −%76, stop_gap −%209, time_stop +%50, target +%82) ·
  maruziyet-düzeltilmiş SPY (ham −0.908 → **−0.110** CI[−.164,−.054], maruziyet 0.064) ·
  **rollback like-for-like: v4→v3 kararı ÇÜRÜDÜ** (simetrik Δ−0.075 > eşik −0.10; eski elma-armut
  −0.133 abartmıştı; Rol 1 hükmü: v3 yerinde kalır — v3 would-have +0.066 > v4 canlı −0.009;
  motor sapması +0.018 kayıtlı) · prescreen.py kalıcılaştı.
- **2026-07-29 H1b yeniden ölçümü (n-dengeli fold):** Δ+0.006 aynı, fold 3/3→2/3, P=0.446 GEÇMEZ —
  Aşama 0 kesin kapandı (4/4 elendi).
- **2026-07-28/29 derin araştırma sentezleri:** Aşama 7 (frekans+edge; 4 kol) ve Aşama 8 (yeni
  bileşenler; 4 kol) plana işlendi; kaynak listeleri oturum kayıtları + tasks/wpiusyxrm,wrj7g2q0t.
- **2026-07-28 Kuzey Yıldızı turu (Hafta 1):** IC katmanlaması (gerçek/cf/havuz) · bileşen IC ilk
  tablo · n-dengeli fold (fold_uncontested koruması + "taban tutan en çok fold" seçimi) · OOS
  aşınma defteri (sayaç o günden; >20 sorguda +0.01 marj) · EDGE VERDICT bileşimi (A3 ✅; ölçüt-1
  yalnız GERÇEK katmandan — 07-27 havuz kararı geri alındı) · cf sadakat kusuru makine-okunur
  beyanla kayıt altına alındı. Canlı-state sızıntısı yakalandı ve temizlendi (test-doğumlu
  oos_erosion.json — kök neden record_erosion bayrağı).
- **2026-07-28 Aşama 0 ön-eleme (takvim fold):** taban v3 OOS 0.1309 n=98; H1a Δ−0.046 ÇÜRÜDÜ ·
  H1b Δ+0.006 3/3 marj-altı · H2 Δ−0.095 ÇÜRÜDÜ · H3 Δ−0.030 ama CVaR −2.9R (kuyruk bulgusu
  G3'ün gerekçesi oldu). Zarar otopsisi: kâr time_stop'tan (+$3.9k, %70), stoplar −$11.8k,
  MFE ort +0.71R — "çıkış mimarisi kanatıyor" teşhisi.
- **2026-07-28 auth/login katmanı** (ayrı oturum): scrypt parola + imzalı HttpOnly çerez oturumu +
  x-meridian-token CLI yolu (MERIDIAN_DASH_TOKEN, .env 0600, serve.sh source eder) + kaba kuvvet
  sınırı. CLI tam yetki token yoluyla doğrulandı.
- **2026-07-28 rollback v4→v3 gerçekleşti** (o günkü asimetrik yasayla; 07-29'da yasa simetrikleşti
  ve karar çürütüldü — üstteki Hafta 2 satırı) · learning_loop_open temizlendi.
- **2026-07-27:** Faz 4b gölge modu kodda · hermes prompt yeniden inşası (statik SYSTEM + kanıt-bağ
  zorunluluğu; −%63 boyut) · broker-ret ack mekanizması · Piyasa sekmesi + SEANS İÇİ kolonu ·
  ilk yansıma yeni prompt'la: hipotez guard'dan geçti, backtest'te elendi (n=1 olumlu sinyal).
- **2026-07-26:** ilmek-1 (EDGE kartı, IC serisi, öğrenme çarkı, canlı akış kartı) · v3 ebeveyn
  taban ölçümü (OOS 0.1245) · keepalive/grup-kill sağlamlaştırması · 31 maddelik review revizyonu ·
  numpy sanitizer (54/54 rota) · review-backlog 5 madde · beyin unparseable kök nedeni düzeltildi.
- **Numaralandırma notu (2026-07-26):** intraday "Faz" sayımı kanoniktir (§3.5); Faz 5/6 tanımları
  yeniden kurulmuştur (kayıp tarihin kurtarılması değil).

## §6 ARŞİV — tamamlanan WP'ler + oturum snapshot'ları (tarihçe-koru; silme yok)

Buradaki WP'ler tam metin korunur (tarihçe). Bir WP'nin içinde geçen açık operatör/kart/ölçüm kalemi
KANONİK olarak §3/§4'te yaşar; buradaki metin o kalemin tarihçesi + gerekçesidir (çürütülen av
adayları, kill-eşikleri, PIT şerhleri kaybolmasın diye). Bitmiş dalgalar: KOVA-B (16/16, 2026-08-02),
WP-N kanıt-hızı programı (N1-N6; N1 kanal §3 · N4→EXE-2026-004 §4 · N2b→EDG-2026-019 §4), dalga-3.

### Tamamlanan WP'ler (tam metin)

### WP0 — Keşif ve Uyum Matrisi ✅ (2026-07-31; 14 mekanizma kanıtlı; en riskli 3 boşluk: iki-motor
icra ayrışması · hacim-onayı çelişkisi · BMO/AMC boşluğu)


### WP1 — Yalnız-OHLCV Adayları
- 1.2 52w-high ✅ ARŞİV (9/9 hücre anlamsız; VCP'den bağımsız ama bilgisiz ρ=-0.036; panel tanısı
  aralık-kısıtını dışladı) · 1.4 hacim-şoku ✅ ARŞİV (bant hayalet-artefaktı değil AMA 0/18 hücre
  ham rvol20'yi geçemedi — ham rvol20 @20 IC 0.065 ANLAMLI; canlı eşik kalır). TORUN-KART ADAYI:
  rvol≥2.5 bölgesi +1.61% anlamlı-pozitif, üçgen form onu sıfırlıyor — form-revizyonu YENİ ön-kayıtla
  (ölçüm-sonrası-seçim yasağına uyuldu). BT-2 hasar tespiti: 5/63 hücre anlamlılık DEĞİŞTİRDİ
  (sınırda hasar); 2018 hayaleti bu pencereye değmiyor — uzun-geçmiş artefaktları aklanmadı.
- 1.3 MAX-filtresi ✅ ARŞİV (2026-07-31: yön TERS — yüksek-MAX bizde @20 +1,46pp iyi; eleme
  hedef-çıkışların %28'ini keserdi; kill×2). **1.1 residual momentum ✅ ARŞİV (2026-07-31, kart
  EDG-007, K=2): 6/6 hücre CI-0-içi + artımlı katkı yok — yapısal örtüşme (residmom≈rawmom ρ=0,625,
  üst-terzil örtüşmesi %83); aile kapalı, torun yok. Yan kazanım: FF3 günlük faktörler repo'da
  (research/ff_factors/, damgalı+doğrulanmış) — 1.5 için altyapı hazır.** **1.5 vol-scaling overlay ✅ ARŞİV (2026-07-31, EDG-008, K=2, kill#3): iki pencere de yönsüz;
  tasarım dersi — IS-çapalı sigma_hedef düşük-vol OOS'ta kaldıraç-artırıcıya döner, ısı-rampasıyla
  çifte-kısma; torun (yalnız-kıs m<=1) tetik-şartlı: yüksek-vol penceresi birikince.**
- EMİLDİ: eski G2 skor-inşası S1/S2 adayları (rvolband/min_rvol çekirdeği) → 1.4'ün kart hükmüne
  bağlandı (iki ayrı ölçüm değil) · eski G7 vol-hedefleme → 1.5'in portföy-bacağı olarak, ısı
  tavanıyla birlikte POZİTİF-EV ÖNKOŞULLU (denetim RS-1).


### WP3 — Doğrulama ve Ek-Veri Aileleri
- 3.2 insider yeniden-kaydı ✅ KAPALI: gerçek CMP ayrımıyla ölçüldü, pozitif-kontrollü sıfır →
  kalıcı arşiv (iş emrinin kendi kill-eşiği).
- 3.1 kaynak-doğrulama ✅ TAMAM (2026-07-31 gece — 4/4 birinci-el): CMP tanımı BİZİMKİYLE
  BİREBİR (insider arşivi GÜÇLENDİ; 2025 replikasyonu etki yarıya inmiş diyor — sıfırımız decay'le
  tutarlı) · Moskowitz-Grinblatt: en-büyük-quintile'da da var AMA Grundy-Martin itirazı (VW +
  1-ay gecikme sağlamlık protokolü ŞART — ileride kart açılırsa protokole gömülü) · Meursault
  PEAD.txt: etki büyük-cap'te sönmüyor ama transkript+NLP ister → veri bileti (FMP transkriptleri
  VAR, NLP altyapısı YOK) · McConnell-Xu ToM: DOĞRULANDI+replike → KART AÇILDI (EDG-2026-006,
  ölçümde).
- 3.3 text/analist PEAD 🔒 veri bileti (analist-tahmin/NLP; proxy yasak). EMİLDİ: eski Y6
  transkript-LLM skoru (aynı text-veri ailesi; look-ahead disiplini şartıyla aynı bilete bağlı).


### WP-G — Rejim Kapıları ✅ İKİ KART DA KAPANDI (2026-07-31; tanı turlu)
- **SMA-200 kapısı ✅ ARŞİV (kart EDG-005): KAPI AÇILMAZ.** İlk "açılabilir" hükmü tanı turunda
  DÜŞTÜ: karşı-olgu kolları kapının OOS doğrudan etkisinin SIFIR olduğunu (55 bloke gün, 0
  engellenen giriş), OOS "iyileşmesinin" tamamen IS-yankısı (portföy-durumu taşıması) olduğunu
  kanıtladı; tek atfedilebilir pencerede kill#1: Sharpe −0,25→−0,90, PARA −0,03→−0,09. Tez kısmen
  doğru (vol anlamlı ↓, oran 0,79) ama bedeli getiri — "pano göstergesi yeter". · **ToM tilt ✅
  ARŞİV (EDG-006):** ön-adımda yön ters (−11,8bps), ikizler hiç açılmadı.
- **KABLO BİLETİ ✅ KAPANDI (2026-08-01 temizlik turu):** spy_sma_gate GÖSTERGE'ye emekli edildi
  (blocks sabit False + knob_emekli beyanı + sessiz-diriliş çivisi; hükümsüz kapıya çekilmiş kablo
  söküldü). KALAN KÜÇÜK İŞ 📋: bounds.yaml'dan knob satırı düşülecek (makine etkisiz knob'u hâlâ
  örnekliyor — 6 değerlendirme boşa K harcadı; akşam penceresi).
- VIX koşullaması 🔒 veri-kilidi (operatörde) — SMA hükmünden sonra AİLE ÖNCELİĞİ DÜŞTÜ: rejim
  kapısı ailesi bu evrende "vol'ü düşürür ama parayı da düşürür" profili verdi; JM rejim modeli +
  koşullu vol kısma adayları açılmadan önce bu hüküm karşı-kanıt olarak okunmalı.
- EMİLDİ: eski Y3 dörtlüsünün SMA/VIX bacakları · turn-of-month index-tilt (EDG-006 ile öldü) ·
  breadth/distribution-day = PANO GÖSTERGESİ, kapı DEĞİL (kill-list).


### WP-R — Rampa/Çıkış Serbestleştirme ✅ ÖLÇÜLDÜ→DARALDI (2026-07-31 03:19; kart EDG-003 measured)
- **HÜKÜM:** P3 paketi ÖLDÜ (rampa serbest bile olsa P≤0,48 — suçlu rampa değil paketmiş);
  early_kill-tek sağ (P=0,606) → gölge-v2 V3 birikimi sürer; **rampanın koruması GERÇEK ölçüldü**
  (serbestlikte DD %4,6→%9,7) — gevşetme lehine kanıt yok. Kalan iş küçüldü: eşikleri bounds'a
  taşımak yalnız hipotez-görünürlüğü için (düşük öncelik); çıkış-mimarisi umudu artık gölge-v2
  canlı birikimi + E1/E4 zamanlama içgörülerinde (gece bacağı kaybı, 8-15g gündüz kazancı).
- Kanıt: de-risk rampası (%3-kıs/%8-sıfırla, KODDA SABİT) günlerin %92'sinde aktif, izin çoğu gün
  1 pozisyon — işlem üretiminin gizli boğucusu; P3 çıkış paketi imzası 4/4 (ödeme 2,84, beklenti
  0,287R) ama örneklem çöküşüyle "reddedildi-çürütülmedi".
- İş: rampa eşikleri bounds'a + `exit.profit_target_r`/`exit.time_stop_days` "kapalı" değerleri +
  sabit-rampa koşulunda P3 ve early_kill tek-başına yeniden-ölçüm + chandelier sıkıştırma
  tuhaflığının (max(close,hh) formu) düzeltilme kararı. Tek ön-kayıt kartı, K-muhasebeli.
- EMİLDİ: eski G3b çıkış reformu ölçümü (bu turun ta kendisi, genişlemiş haliyle).


### WP-K — Kurulum/Aile Genişletme
- **Trend-kolu RAFİNE ✅ ÖLÇÜLDÜ (2026-07-31, kart EDG-009, K=4; pozitif kontrol 0.000000 farkla):**
  rafine üstünlük KANITLANAMADI (B aylık-rebalans CI-0-içi, vol/DD kötü; muhafazakâr okuma) →
  HAM KOL incumbent. ASIL BULGU — KALICI PIT ŞERHİ: +13,1p/yıl fazlanın büyük kısmı evren-seçim
  yanlılığı; PIT-sağkalan evrende ~6-7p/yıl (D t=2.08 — hayatta, kill#2 tetiklenmedi). 2021+
  tanısı: decay değil oynaklık (eşlemeli çıtada erime yok, t=1.82). **GÖLGE-KİTAP ✅ KOD-HAZIR
  (2026-07-31 gece turu; canlıya sonraki pencerede):** trend_shadow.py sıfır-yetkili paralel defter
  — şasi-birebir sabitler, PIT şerhi kitap içinde, YASA-6 okuyucuları çivili, 645-seans smoke temiz
  (medyan tur 23ms), kapatma anahtarı var; ilk giriş 2026-09-01 ay-sonu kararıyla (tasarım). · **G4 pullback ✅ ARŞİV (2026-08-01, kart EDG-010, K=2): bağımsızlık GERÇEK (Jaccard ~0.02)
  ama kenar YOK — ham pozitiflik evren-tabanında kayboluyor (dip10 trend-evreninde anlamlı negatif);
  kart-ölçütü kusuru itiraflı, ders WP-M #3'e (ham-getiri ölçütü yasak)** · G5 in-play: EDG-011 ASKI SÜRER (tanım tarafı — 2026-08-02 keşfi: veri İKİ bağımsız eksenle
  olgunlaştı [Nasdaq-geçmişi %99,7 tamlık + EDGAR 8-K %98,4 çapraz-doğrulama, dakika-damgalı]
  ama kartın "t'de BİLİNEN takvim" lafzı ex-post kaynakla karşılanamaz; PIT defteri 0 satır —
  A1'de snapshot dosyası hiç doğmamış, AYRICA canlı earnings.csv 2-sütunlu/Jul-31 bayat =
  tazeleme turu dağıtımdan beri koşmamış, İZLENECEK). Tek-yönlü post-event tez ölçüldü ve
  **EDG-2026-020 ✅ ARŞİV (2026-08-03: kill#1+#3 — havuz-fazlası CI-0-içi/negatif-nokta; ham
  +%1,1 taban-sürüklenmesiydi [ders#3 vakası]; PEAD-kopyası değil ama bilgi de yok; 011'e
  aleyhte-önsel not düşüldü)** · **G6 koşullu-kısa → RAF (2026-08-02 fizibilite keşfi: 5 yüzeyin 4'ü YOK
  [broker/strategy/gölge/ayna], 12-kalem motor inşası; EDG-005 karşı-gözlemi: SPY<200MA
  günlerinde long hâlâ pozitif-beklentili görünüyor — kısa tezine doğrudan karşı; 55 OOS
  bloke-gününde 0 silahlanma. Yeniden açılış: operatör kararı + delist-bar sonrası kısa-tez
  kanıtı. Kanıt: research/olcumler/kesif_2026-08-02/)** · **VCP-DECOMPOSE ✅ ARŞİV (2026-08-01, EDG-015,
  K=2): çatı da bilgisiz — üst-%20 kompozit @10 aday-havuzunun ANLAMLI ALTINDA; form=bileşen-toplamı
  (ρ=0,95). WP-K'da ölçülmemiş hipotez KALMADI.** ⚠ İZLEME→ÖĞRENME: canlı skorun kesit-içi
  sıralaması kısa ufukta kanıtsız/ters (rs-negatif bulgusuyla tutarlı) — knob kararı öğrenme
  döngüsünün/operatörün; kanıt vcp_olcum'da.
- **KEŞİF 2026-08-09 (`docs/KESIF-WP-MKP-2026-08-09.md` §WP-K):** kendi kuyruğunda **ölçülmemiş hipotez
  YOK** (VCP-DECOMPOSE ile tükendi). 3 artık kalem açık: **G5 in-play** (EDG-011 ASKI SÜRER — "t'de
  BİLİNEN takvim" lafzı ex-post kaynakla karşılanamaz + PIT defteri 0 satır + canlı `earnings.csv` bayat,
  FMP-402'ye bağlı) · **G6 koşullu-kısa** (RAF; EDG-005 karşı-gözlemi) · **EDG-021 2. koşum** (tanım-
  eşitleme, operatör — §6). Genişleme hattı (transkript-LLM/13F + WP-QC (b)-kovası [354 idio-skew /
  16 overnight / 269+125 mevsimsellik] + bileşen-ders Ek-B ①-⑤) kart-önce, WP-QC/HEDEF-5'te park.


### WP-N — Kanıt-Hızı Programı 🔴 AKTİF (2026-08-09; operatör onaylı sıra: N1→N2→N3→N4, N5 serpiştirilir)

**TEŞHİS (ölçülü):** darboğaz kod değil KANIT ÜRETİM HIZI. Faz-6'nın kapalı üç kilidi kârlı
işlem geçmişi istiyor (kodla açılabilecek kilit kalmadı — WP-L); Eksen-2 67 skill'in 2'sini
ölçebilmiş; Faz-5 4/20 çiftte; E3 ampirik bandı örneklem bekliyor; gölge modeli n_live=0
yüzünden hiç terfi edememiş. Sistem haftada ~4 pozisyon açıyor — kanıt musluğu bu.

- **N1 — Bildirim jetonu ayrımı ✅ KOD TARAFI (v216 — NAKED_POSITION jetonu obs.py NOTIFY_TOKENS'a ayrıldı; jeton pini `7f91178`'de beyanla büyüdü) / 🔒 KANAL OPERATÖRDE:** `NAKED_POSITION`
  jetonu (obs.py NOTIFY_TOKENS) + koruma alarmının `MIRROR_DRIFT`ten ayrılması — bugün ikisi
  aynı 6 saatlik susturma penceresini paylaşıyor; korumasız-pozisyon gecesi sev-1 alarmlar
  bastı ve operatöre HİÇBİRİ ulaşmadı (33 teslim edilmemiş alarm birikmiş). Jeton ayrımı kanal
  gelmeden de değerli (susturma ayrışır). KANAL (Telegram bot token / webhook URL) operatörün
  tek parçası — teslim zinciri hazır, kanal boş (WP-O §6.1).
- **N2 — Gölge kapsam genişletme ✅ KOD İNDİ (v217, kart EXE-2026-003 + R1 — gölge planlı-kol):** silahlı kol bayt-özdeş kaldı, planlı (silahlanmamış) kol AYRI defterde `kol: planli|silahli` etiketiyle (karışım kill#4'ü ateşlerdi, ölçülüp kanıtlandı). Tasarım metni: 4b bugün yalnız SİLAHLANMIŞ planların
  gölge dolumunu yazıyor (6 seansta 4). Genişletme: tetiği kesilen PLANLI (silahlanmamış)
  GO/REVIEW planları da gölge dolumu yazar, `kol: planli|silahli` etiketiyle AYRIK.
  **ROL-1 DÜZELTMESİ (ilk öneri metnindeki hesap yanlıştı):** bu genişletme Faz-5 kilidinin
  n_min'ini DOĞRUDAN doldurmaz — kilidin çifti gerçek-iç-dolum ister ve silahlanmamış planın
  iç dolumu YOKTUR (R1'in kapsam_disi kovasına düşerler). Ölçeği veren İKİNCİL eşleştirmedir:
  gölge(dakika-sim) × cf(EOD-sim) — İKİ SİMÜLASYON, aynı maliyet modeli, fark yalnız zamanlama
  (EXE-2026-002'nin kendi onayladığı metodoloji). cf tüm adayları kapsadığı için örneklem
  ~7 bin satırlık havuzdan beslenir. Bu ikincil hat KİLİDİ AÇMAZ (kilit gerçek-çift ister);
  birikip gerçek-çift hattıyla UYUŞURSA kilidin kanıt kaynağını genişletme önerisi ayrı bir
  kart revizyonu olarak OPERATÖRE gider. cf'nin çıkış-sadakati kusuru bu ölçümü KİRLETMEZ —
  bu bir GİRİŞ ölçümü, çıkış modeli işe karışmıyor.
  Skill gölge rotasyonu (57 ölçülmemiş skill, haftada N) AYRI kart — N2'den sonra açılır.
- **N2b — Skill görüş defteri + yaşam-döngüsü ⚠️ KOD İNDİ / CANLI KANIT BEKLİYOR (v218, kart EDG-2026-019):**
  skill yaşam-döngüsü dürüstlüğü + görüş defteri v1 katmanı indi (İLK koşusunda iki yönlü kesti).
  AMA terfi/emeklilik R-figürleri (vcp +0,116R / momentum-burst −0,114R) canlı state'te
  YENİDEN-ÜRETİLEMEDİ: `eksen2.uretilen=0`, `gorusleri.jsonl` beslenmedi, kadans bu adımı KOŞMADI —
  KURU-KOŞU. Doğrulama birkaç EOD penceresi + EDG-2026-019 ölçüm kodu bekliyor (uydurulmaz:
  ölçülemedi — bkz. `docs/SABAH-TRIYAJI-2026-08-09.md` §iii.7/§iv). 57 ölçülmemiş skill rotasyonu
  bu hatta bağlı.
- **N3 — Sermaye bekçileri ✅ İNDİ (WP-S SB-4 + SB-3, v216):** damgasız-yazım bekçisi (kitap
  `store` dışından değişebiliyor ve kimse görmüyor — denetim tabanı) + `taban_kaymasi` satırı;
  ikisi de v216'da indi (bkz. WP-S SB-4/SB-3 ✅).
- **N4 — cf çıkış-yasası sadakati 🔒 BAKIM PENCERESİ ŞARTLI (en pahalı, en değerli):** 6 çıkış
  tipi modellenecek + TÜM cf tarihi yeniden koşulacak (saatler, state'e yazar → canlı worker
  koşarken YAPILMAZ). %96'lık skor havuzundaki +0,039R iyimserlik kapanır; Eksen-2/terfi/edge
  hükümlerinin ortak zemini temizlenir. Kendi ön-kayıt kartıyla gider; pencereyi operatör açar.
- **N5 — Görünürlük turu ✅ İNDİ (v219 + v225 + v226):** 409-yutması (boş catch 6→0, v219) +
  `EV_TR` koruma_*/süpürücü çevirileri (v219 dokuz olay + v225 `siniflar` dökümü) +
  `k.olcum`un çizilmesi (beş kilit, v219) + hermes telemetri kartı (v219, İLK pano okuyucusu) +
  liveness kartı (v226). WP-S2 görünürlük borçlarının icra turu; hepsi app.js/api.py gösterim ailesinde.
- **N6 — DEVİR TATBİKATI ✅ KOŞTU (6. kova, 2026-08-09 01:20-02:10 UTC — `docs/DEVIR-TATBIKATI-2026-08-09.md`):**
  bağlamsız devralan ajan sistem haritası + ilk 10 risk çıkardı. **KRİTİK BULGU:** önceki koruma
  "✅ KAPANDI" beyanı artefakttan doğrulanmamıştı — koruma×süpürücü çarpışmasını yeniden açtı
  (`68ea173`), kök düzeltme v220+v221'le indi (bkz. WP-S ✅). Bağlam-sahibi SABAH TRİYAJI
  (`docs/SABAH-TRIYAJI-2026-08-09.md`) 13 kalemi dağıtımlardan SONRA yeniden ölçtü: **13/13 gerçek,
  0 çürük**; kapsamdaki P1=0 (tek gerçek sermaye-P1 çıplak pozisyon v220 ile kapandı). Fark hükmü:
  tatbikatın bulduğu bilinen-dışı kalemler (systemd exit-143, sprint orphan, dual-source) dalgaya/
  WP-S2'ye girdi. _(Aşağıdaki tasarım metni tarihçe olarak korunmuştur:)_
- **~~N6 — DEVİR TATBİKATI (tasarım; 6. kova; DAĞITIMLAR BİTİNCE koşar — operatör onayı 2026-08-09)~~:**
  BAĞLAMSIZ bir ajan (oturum hafızası YOK, yalnız depo + salt-okunur canlı) "sistem haritası +
  ilk 10 risk" çıkarır; girişi deponun kendi devir sözleşmesi (CLAUDE.md → MERIDIAN_ENGINEERING_LOG).
  Rol-1 çıktıyı BİLİNEN bulgu defteriyle (2026-08-07/09 turları = bilinen-pozitif seti) kıyaslar:
  (a) bilinenleri BULAMADIĞI yerler = depo onboarding'inin/tek-kaynak haritasının boşluğu —
  belge borcu olarak açılır; (b) bizim listemizde OLMAYIP bulduğu şeyler = bizim körlüğümüz —
  şiddetine göre dalgaya girer. Çıktı: docs/DEVIR-TATBIKATI belgesi + Rol-1 fark hükmü.
  SIRA GEREKÇESİ: dağıtım #2'den SONRA — tatbikat iyileştirilmiş durumu denetlesin ki bulduğu
  her boşluk GERÇEK kalan boşluk olsun, bu gece zaten kapatılmış bir şeyin gölgesi değil.


### Oturum snapshot'ları (tarihçe — açık kalemler ilgili §1/§3/§4'e taşındı; burada tam metin korunur)

**2026-07-31 gece-vardiyası + 2026-08-02 denetim-kuyruğu kaydı (eski §1 "ŞİMDİ" gövdesi):**

- **GECE DALGASI CANLIDA (03:00 dağıtımı):** WP-E icra turu (iki-motor tek yasası `broker.entry_law`,
  marketable stop-limit + gap-yolları, E2 slipaj defteri, E3 kötümser bant, E4 gece/gündüz) ·
  SIP-geçmiş-yasası (ilk canlı kanıt: `alpaca_sip_skipped_current_session`) · pano 8-kalemi ·
  BT-1 damga-migrasyonu UYGULANDI (95/95 `replay_seed`, gerçek-canlı sayaç 0'dan başladı) ·
  round-2 karantina (8 defter onarıldı) + `bars_integrity.json` (61 sembol) · regime `entry_gates`
  üretici düzeltmesi (SMA/VIX kapıları İLK KEZ ateşleyebilir durumda; knob'lar kapalı, tarih
  birikiyor) · tick-progress bekçisi (asılı-tick sınıfına) · Suite: **~2.900 test, 0 kırmızı.**
- **GECENİN ÖLÇÜM HÜKÜMLERİ:** 52wh ARŞİV · volshock ARŞİV (canlı eşik aklandı; ham rvol20 anlamlı)
  · MAX ARŞİV (yön ters — yüksek-MAX bizde İYİ) · EAP ARŞİV (güç-yeterli) · WP3.1 4/4 birinci-el
  (CMP birebir → insider arşivi kesinleşti; ToM YENİ KART ölçümde) · trend kolu YAŞIYOR (rafine
  bekliyor) · KOŞUYOR: WP-R rampa-P3 (K=4) + SMA/ToM ikizleri.
- **E4 İLK OKUMA (tohum-etiketli):** kaybın %84'ü GECE bacağında; tek pozitif dilim (8-15g)
  kazancını GÜNDÜZDEN yapıyor; giriş-gap p90 +100bps → %1 limit tavanı bağlayıcı olacak.
- **A1:** ilk tam-anayasa tick'i ilerliyor (IEX bacağı 252/253 teslim; onarım soğuma-içi-bekleme
  kokusu sabah listesinde); monitör-v2 + 3sa-gevşetilmiş bekçi nöbette.
- **Operatöre sabah kalemleri:** MNST 2005 ×0,48 bütünlük yorumu · delist-bar kararı (QuantConnect
  vs Massive planı) · bildirim kanalı · FMP planı · VIX kaynağı · shares-outstanding kaynağı.
- **DENETİM KUYRUĞU (2026-08-02 gecesi; kaynak `docs/SISTEM-DENETIMI-2026-08-02.md`):** KOVA A
  **9/9 İNDİ** (d50b03b defter+kadans · 395920e veri-hattı · 8a38248 gözetim; 44 yeni test, hepsi
  kırmızı-önce/canlı-kopya doğrulamalı). **KOVA B 16/16 İNDİ (2026-08-02 gündüz, operatör onayıyla — üç dalga):**
  90a6663 icra-güvenlik (C9/C23/C8) · 6020fa0 yapı (C3/C5) · 84fcf69 öğrenme-politika (C14/C16/C17) ·
  9b8327e küçükler (C1/C25) · 0a4453f iki-motor (C11/C18/C13/C19) · 6aba956 dalga-3 (C24/C12) ·
  0170cc0 borçlar + takip hükümleri (v76 fikstürü, Y3 ölçülemedi-notu). Dağıtıldı 14:00/14:30 UTC;
  birim migrasyonu yapıldı. 25 bulgunun 25'i kapalı ya da bilinçli-beyanlı.
- **Hermes-CLI yapılandırma dersi (2026-08-02, canlı vaka):** A1 taşınmasında ~/.hermes yapılandırması
  taşınmadı (hiçbir kanalın parçası değildi), senkron tek-atımlık olduğundan kendini onarmadı, hiçbir
  bekçi "yerel ajan yapılandırılmış mı" ölçmüyordu — LLM ikinci-görüşü 6 gün sessiz öldü. Kalemler:
  (a) servis açılışında senkron-doğrulama (GEMINI_API_KEY dolu + CLI modelsiz → yeniden senkron + olay);
  (b) pano senkron-sonucu zaman-damgalı (bayat OSError vakası); (c) bekçi: agent_call boş-serisi
  "kota" ile "yapılandırmasız"ı ayırt etsin; (d) RPD bütçesi ağa HİÇ çıkmamış çağrıyı saymasın —
  canlı vaka: ölü zincir 150/150'yi 06:19'da yaktı, gerçek Gemini kotası el değmemişken inceleme
  tüm gün bütçe-reddi yedi (sayaç korumaya çalıştığını ölçmüyor); (e) `review_candidates` dolu cevabın
  filtreden sıfır görüşle çıktığı hâlde OLAYSIZ None dönüyor (hermes.py ~2109) — ham cevabın ilk
  ~300 karakteriyle bir `candidate_review_empty_parse` uyarısı gerekir (2026-08-02 canlı vaka:
  Gemini dolu cevap verdi, kayıt yok, sebep görünmez).
- **VERSİYONLU-STATE DAĞITIM BOŞLUĞU (2026-08-02 akşam, canlı doğrulandı — KRİTİK SINIF):**
  bounds.yaml/goal.yaml versiyonda AMA rsync state/'i dışlar → hiçbir dağıtım bunları canlıya
  taşımıyor. Canlıda w_turnover YOK (sıfır turnover-örneklemesinin C15'ten bağımsız İKİNCİ kök
  nedeni — knob hiç doğmamış), heat_hard_r YOK (guard fail-safe aynı değerlerde; sahiplik canlıda
  gerçekleşmemiş). ÇÖZÜM toplu pencerede: canlı↔repo diff (canlıda repo-dışı satır varsa DUR) →
  worker durmuşken scp → doğrulama. KALICI KALEM: dagit'e versiyonlu-state adımı (diff-göster +
  onaylı-kopya) eklenmeli.
- **Denetim turunun bıraktığı küçük kuyruk (ajan-beyanlı):** `same_evening_bars` fırlatmayan arıza
  yolu hâlâ `empty` yazıyor (bacaktaki ikinci HATA≠BOŞ deliği; kapanış yolu: calls/fails deltasını
  `_fetch_alpaca_session` üzerinden taşı) · `conftest._clear_module_caches` `scheduler._state`i
  sıfırlamıyor (test_regime_patch sıraya-bağlı düşüş — kısmi `-k` seçimlerinde; tam suite düzeninde
  görünmez) · pano `_patOK/_patNote` `dedektor_dustu/olculemedi` bilmiyor (düşen dedektör yeşil
  görünür — S2R-3/app.js kalemi) · mutation.py `dedektor_dustu`yu okumuyor.

**DURUM PANOSU (2026-07-31 sabah — eski §2; bayat, GÜNCEL DURUM §1 tarafından güncellenir):**

| Eksen | Durum | % |
|---|---|---|
| Çalışma ortamı (A1 7/24 + bekçiler + yedek zinciri) | canlı; tick-bekçisi + fail-notify + VM-dışı yedek | 95 |
| Veri hattı (aynı-akşam IEX + sip-sabah + onarım + takvim/karantina/bütünlük kapıları) | canlıda; delist-bar kısıtı açık | 90 |
| İcra sadakati (iki-motor tek yasası + E2 defteri) | KOD canlıda; ilk gerçek emir sınavı bugünkü seans | 70 |
| Ölçüm yönetişimi (kartlar + K + DSR/PBO + donmuş holdout + kod-damgası) | işliyor; skor kartı 39/100 → yeniden puanlama bekliyor | 85 |
| Öğrenme otomasyonu (sprint/dolgu/Eksen-2/karne) | kadanslar canlı; ilk tam gece verisi birikiyor | 80 |
| Edge envanteri | 9 aile ölçülmüş-arşiv · 1 YAŞIYOR (trend) · 3 ölçümde (rampa-P3, SMA, ToM) | — |
| Pano dürüstlüğü | 8 kalem canlıda; operatör doğrulaması bekliyor | 85 |
| Gerçek-canlı kanıt | n=0 (damga sonrası dürüst sayaç) — birikim bugün başlıyor | 0 |
