# KEŞİF TURU — WP-M · WP-K · WP-P (2026-08-09)

**Yazan:** keşif ajanı (salt-ölçüm + plan; kod/dağıtım yetkisi YOK).
**Okuyucu (YASA 6):** Rol-1 (dalga önceliklendirmesi) + bir sonraki mühendis.
**Ölçüm penceresi:** 2026-08-09 ~15:50–16:30 (yerel), depo salt-okunur.
**Girdi:** `ROADMAP.md` (1851 satır) · `MERIDIAN_ENGINEERING_LOG.md` · `docs/SABAH-TRIYAJI-2026-08-09.md`
(bağlam-sahibi, dağıtımlardan SONRA ölçülü — en otoriter) · `docs/TASARIM-YONU-2026-08-07.md`
(WP-UX bağlayıcı yön) · `docs/RUNBOOK.md` · `research/cards/` · `tests/test_kart_kimlik_v219.py`.

**Sınır beyanı:** git komutu KOŞULMADI · dağıtım YAPILMADI · `serve.sh` KOŞULMADI · broker'a emir
YOK · `meridian/` ve `tests/` altında HİÇBİR dosyaya dokunulmadı · canlı state'e YAZILMADI. Bu,
depoda yazılan **TEK** dosyadır (görev sözleşmesi).

---

## 0. GÖREV ÖNCÜLÜNÜN DÜZELTİLMESİ (ölçümle — "ne kadarı kapandı, ne kaldı")

Görev, gece inen pano işini **"D0-D6, WP-UX D3-b F1/F2/F14, görünürlük turu"** diye adlandırdı.
Ölçüm bu adlandırmayı **kısmen çürüttü** — dürüstlük gereği kayda geçiyor:

- **WP-UX D0-D6 İNMEDİ.** ROADMAP'te D0 hâlâ `🔄` (mod-görünürlüğü/ffill-rozeti/`162 ?? 0`
  triyajı — hepsi açık), D1-D6 hâlâ `📋` (ROADMAP:702-717). WP-UX yalnız tek satırda anılıyor
  (ROADMAP:697); §7 karar günlüğünde WP-UX'in ilerlediğine dair **hiçbir giriş yok**. Yeniden-tasarım
  programı **bütünüyle açık**.
- **D3-b F1-F15 İNMEDİ.** `TASARIM-YONU` (08-07) F1-F15'i "YENİ — sıraya alındı" diye listeliyor
  (satır 140-158); hiçbiri `✅` değil. Gece belgeleri (08-09) F-kalemlerini anmıyor. F1/F2/F14 dahil
  **on beşi de kuyrukta.**
- **GECE FİİLEN İNEN, DÖRT DAĞITIM (ROADMAP:23-34, 835-855):** WP-N kanıt-hızı dalgası (v216-v219) ·
  koruma×süpürücü kök düzeltmesi (v220+v221) · dalga-2 sahte-yeşil avı (v222-v226) · null-sıfır
  kapısı (v196). "Görünürlük turu" = **WP-N N5** (v219+v225+v226, ROADMAP:380-383) — WP-UX değil
  WP-S2 görünürlük borçlarının icrası (app.js/api.py gösterim ailesi).

**Sonuç:** Gece pano işi GERÇEK ama **WP-N/WP-S/WP-S2 hattında** indi; **WP-UX yeniden-tasarımı
(D0-D6 + F-kalemleri) hiç ilerlemedi.** Bu, aşağıdaki (ii) örtüşme bölümünün eksenidir.

Gece kapananlardan bu turda **DÜŞÜLENLER** (görev talimatı): v196 null-sıfır kapısı · v214 codelaw
kör-noktası (B-2/B-4) · kart tekillik/kimlik testi (`tests/test_kart_kimlik_v219.py`) · 5. kova
çok-yazarlı tarama (`CIFT-KAYNAK-TARAMASI`) · 6. kova devir tatbikatı (N6).

---

## (i) ÜÇ WP'NİN KALAN AÇIK İŞİ (gece kapananlar düşülmüş)

### WP-M — Metodoloji / Yasa Borçları (ölçüm altyapısının kendisi)

Gece kapananlar düşüldükten sonra **11 kalem gerçekten açık** (9 metodoloji/yasa + 1 PBO/DSR taban
[restart-şartlı] + 1 araç-kör-nokta artığı). Kaynak: ROADMAP:483-510 kuyruğu + PBO ölçümü.

| # | Kalem | Kanıt | Tür | Bağ |
|---|---|---|---|---|
| M1 | **KIYAS-KİRLENMESİ düzeltmesi** (olay-penceresi-dışı kıyas) | ROADMAP:505-506; EAP yan bulgusu | kod+ölçüm | **TÜM evren-medyanı ölçümlerini etkiliyor** — en yüksek kaldıraç |
| M2 | **PBO/DSR tabanı** — 0/204, `pencere_id` damgasız 124/124 satır → sert PBO kapısı canlıda NO-OP | ROADMAP:1394, 1449-1452; ENG-LOG:628 | ölçüm + **restart** | canlı yazar R1-rotasyon öncesi kodu koşuyor; taban restart'a kadar boş |
| M3 | **2B blok-bootstrap CI standardı** | ROADMAP:504 | ölçüm-şablonu | — |
| M4 | **2C empirical-Bayes küçültme** | ROADMAP:504 | ölçüm-şablonu | — |
| M5 | **A4 tahmin-isabeti bandı** | ROADMAP:505 | ölçüm | EDGE ölçütü #3'ün tabanı |
| M6 | **PK4/PK5 yol-tutarlılık kontrolleri** ölçüm-şablonu standardı | ROADMAP:507; ENG-LOG:583-585 | ölçüm-şablonu | tek-enstrüman pozitif-kontrol körlüğü dersi |
| M7 | **prescreen raporlarına kod-sürümü damgası** | ROADMAP:507, 136 | kod (ucuz) | canlı-defter↔Search şiddet farkı teşhisi |
| M8 | **K-defteri ↔ kart senkronu** (retro kartlar) | ROADMAP:508 | bakım/hijyen | kart disiplini boşluğu |
| M9 | **Chen-2022 t-hurdle dengeleme notu** (K-cezası kalibrasyonu — referans, gevşetme değil) | ROADMAP:509-510 | doküman/referans | K-cezası şeffaflığı METODOLOJİ bacağı (SURFACE = F13, WP-UX) |
| M10 | **2D R2 holdout rotasyonu** — koşullu ("zamanı gelince") | ROADMAP:505 | ölçüm | ertelenmiş; tetik-şartlı |
| M11 | **Araç-kör-nokta artığı:** KATMAN-4 alan merceğinin plan defterinin ~20 kontrol alanına genişletilmesi (bir sonraki kova) | ROADMAP:314-315 | araç/tarama | 4./5./6. kova indi; alan-düzeyi genişleme kaldı |

**Açık kuyruk (M-bitişik):** `hermes.py:644` `ship_calibration` askıda-durumu beyne taşımıyor
(ROADMAP:500-501 "AÇIK KUYRUK"). Küçük, ayrı tur.

**Kart disiplini boşlukları haritası (görev item-1):** tekillik/kimlik testi ✅ kapandı (v219) ·
eşik-dilbilgisi + ham-getiri yasağı = DERS olarak kayıtlı, mekanik çivi YOK (ROADMAP:483-488) ·
K-defteri↔kart senkronu = M8 (açık).

### WP-K — Kurulum / Aile Genişletme

**Temel bulgu:** *"WP-K'da ölçülmemiş hipotez KALMADI"* (ROADMAP:478). WP-K'nın **kendi orijinal
kuyruğu tükendi** (trend/pullback/in-play/VCP/net-issuance/... hepsi ölçüldü ya da arşiv). Kalan iş
iki gruba ayrılıyor: **(a) 3 artık kalem** + **(b) genişleme hattı** (WP-QC/HEDEF-5'te park).

**(a) WP-K kendi kalanı — 3 kalem:**

| # | Kalem | Durum | Kanıt |
|---|---|---|---|
| K1 | **G5 in-play (EDG-011)** | ASKI SÜRER — tanım tarafı: "t'de BİLİNEN takvim" lafzı ex-post kaynakla karşılanamaz; PIT defteri **0 satır** (snapshot hiç doğmamış); canlı `earnings.csv` bayat (tazeleme dağıtımdan beri koşmamış) | ROADMAP:465-469; SABAH-TRIYAJI Kalem 7 (FMP 402) |
| K2 | **G6 koşullu-kısa** | RAF — 5 yüzeyin 4'ü yok; 12-kalem motor inşası; EDG-005 karşı-gözlemi (SPY<200MA'da long hâlâ pozitif) | ROADMAP:472-476 |
| K3 | **EDG-021 delist ikinci-koşum** | tanım-eşitleme hakkı — @20 fazla CI-0-içi; evren-kompozisyon farkı şüphesi | ROADMAP:640-644 |

**İzleme (borç değil):** trend gölge-kitap KOD-HAZIR, İLK GİRİŞ **2026-09-01** ay-sonu kararıyla
(ROADMAP:460-463) · ⚠ canlı skorun kesit-içi sıralaması knob'u = öğrenme-döngüsü/operatör
(ROADMAP:478-480).

**(b) Genişleme hattı — yeni aile adayları (kart-önce; WP-QC/HEDEF-5'te yaşıyor):**

- **HEDEF-5 halef aileleri:** transkript-LLM skoru (aynı text-veri ailesi, look-ahead disiplini;
  ROADMAP:180) · 13F uzun-ufuk önceliklendirme (Y6-13F→WP-U; ROADMAP:453, 961).
- **WP-QC (b)-kovası (8 aday, tam liste Ek-B):** ilk-3 = **354 idio-skew** (EDG-004'ü AÇIKLAMA
  potansiyeli) · **16 overnight-ayrışımı** (sıfır ek veri, ÖZELLİK olarak) · **269+125
  kesitsel-mevsimsellik** (tek kart, 125 grid-hücresi) — ROADMAP:688-690.
- **Bileşen-ders kartları (Ek-B ①-⑤, YAŞAYAN kolun üstünde çalıştığı için öncelikli):**
  rejim-kadranı · korelasyon-çarpanı CF(ρ̄) · çıkış-mimarisi (vol-genişleyen eşik) · dinamik-evren
  vs statik-251 · ikili-bayrak skoru — ROADMAP:681-690.

**Aile-genişletme disiplini (görev item-2):** ön-kayıt kartı ZORUNLU (`research/cards/`, ölçümden
önce) · eşik sonradan değişmez · kill-list dokunulmaz · K grid'de ÇARPILARAK · **taban-fazlası
ölçüt** (ders #3: ham-getiri okuma YASAK — EDG-010 vakası, ROADMAP:483-485) · PK4/PK5 yol-tutarlılık
(M6 borcuna bağlı).

### WP-P — Pano / Operatör Arayüzü

**Temel bulgu: WP-P'nin YÜZEY programı (P1-P10) KAPALI.** ROADMAP:722-750 — P1 sessiz-hat ✅ ·
P2 alarm bütçesi ✅ · P3 gauge yasağı ✅ · P4 tipografi ✅ · P5 belirsizlik ✅ · P6 zemin ✅ ·
P7 ⌘K paleti ✅ · P9 ısı-matrisi ✅ · P10 hareket ✅ · P8 zaten mimaride. Eski "8-K vekili + P9
dışında WP-P tamam" kaydındaki P9 de indi.

**WP-P'nin WP-UX'ten AYRI TEK canlı borcu — operatör el kitabı içeriği:**

| # | Kalem | Kanıt | Tür |
|---|---|---|---|
| P-A | **`docs/RUNBOOK.md`'de 32 "runbook girdisi henüz yazılmadı"** — alarmların Çözüm/betik prosedürü boş (HEARTBEAT_STALE, ROLLBACK, CIRCUIT_BREAKER, DATA_QUALITY, HALT_ACTIVE, MIRROR_DRIFT, BROKER_REJECT, TRAIL_DESYNC, MECHANISM_STALE, ARMING_READY, AUTHORITY_CHANGE, GOAL_FAILURE, NAKED_POSITION, scheduler_poll, hermes_poll, warmup_sprint, cf_advance, p5_calibrations, mirror_reconcile, ...) | `grep -c` = **32**; WP-S2 ①: "31 girdi" (ROADMAP:275) — bir artmış | operatör-prosedürü içerik yazımı |

Bu borç **kaynak-sözleşmeli/oto-üretilmiş** (`ops/runbook_uret.py`; t3 çivisi log↔runbook eşitliğini
kapıyor) — uydurmaz, onaylı kaynak (betik başlığı / mühendislik günlüğü) alarm adını literal anmadığı
için "yazılmadı" der. Kapatmak GERÇEK prosedür/betik yazmayı ister (yüzey değil, içerik).

**WP-P'nin ikinci rolü (borç değil, işlev):** WP-P'nin kontrol-odası doktrini (HP-HMI/ISA-101,
EEMUA 191, Few/Tufte — ROADMAP:720-721) **WP-UX D6 doğrulamasının KABUL ÇITASI**dır. WP-UX yüzeyleri
bu çıtaya karşı ölçülür.

---

## (ii) WP-UX ÖRTÜŞMESİ — net ayrım

**İlke:** WP-P = **GEREKSİNİM/DOKTRİN** (kontrol-odası el kitabı, P1-P10 ilkeleri + RUNBOOK içeriği).
WP-UX = **YÜZEY/İCRA** (D0-D6 yeniden-tasarımı + D3 fırsat yüzeyleri + modüller). İkisi aynı
pano ekranlarına dokunur ama **iş kalemleri ayrık**.

| Alan | WP-P (gereksinim) | WP-UX (yüzey/icra) | Durum |
|---|---|---|---|
| HMI ilkeleri (jeton/renk/hareket/gauge) | P1-P10 ✅ tanımladı | D1 jetonlar + beş renk rolü uygular/yeniden düzenler | WP-P ✅ · WP-UX D1 📋 |
| Tipografi | P4 ✅ (işlevsel çıta: kendi-barındırma/tabular/Türkçe aksan) | D4 font seçimi (Geist EMEKLİ — operatör kararı) | WP-P ✅ · WP-UX D4 📋 · **P4 notu → D4'e taşındı (örtüşür, ayrı değil)** |
| K-cezası şeffaflığı | M9 metodoloji (Chen t-hurdle) | **F13** "örneklem derinliği bedeli beyanı" yüzeyi | METODOLOJİ=WP-M · SURFACE=WP-UX |
| "Neden çalışmıyor" / durum sözlüğü | — | **F8** + D1 durum-kanalı | WP-UX 📋 (WP-S2 `durum` alanı kısmen besledi) |
| İki kademeli eşik + NO_DATA | — | **F14** | WP-UX 📋 (v196 null-sıfır + `universe_drift=unknown` alarmı BİTİŞİK ama F14 değil) |
| Kâğıt-canlı / canlı-backtest ayrışması | — | **F1/F2** (E1/E2 hattı) | WP-UX 📋 (E2 defteri veri üretiyor; yüzey yok) |
| Alarm prosedürü | **P-A** RUNBOOK.md içeriği | D2 runbook.html EMİLİR (yüzey) | **AYRIK:** WP-P = markdown el kitabı içeriği; WP-UX = html yüzeyini panoya emme |

**Gece "görünürlük turu" (N5) ne kapadı, ÖRTÜŞME nerede:** N5 (v219+v225+v226) = 409-yutması
(boş catch 6→0) · `EV_TR` koruma/süpürücü çevirileri · `k.olcum` çizimi (beş kilit) · **hermes
telemetri kartı** · liveness kartı (ROADMAP:380-383). Bunlar **WP-S2 görünürlük borçları**; hermes
telemetri kartı WP-S2'de "D3-UI kalemi" diye anılıyordu (ROADMAP:277) — yani N5 D3-UI'ye BİTİŞİK bir
kartı kapattı, ama **numaralı F1-F15'ten hiçbirini** kapatmadı. D3-b kuyruğu bütünüyle açık.

**Kural (çakışmayı önlemek için):** WP-P yüzey işini YENİDEN AÇMA — P1-P10 bitti ve WP-UX aynı
yüzeyleri yeniden düzenleyecek. WP-P'nin ileriye-dönük ayrık işi YALNIZ **P-A (RUNBOOK içeriği)** +
**D6 kabul çıtası** olma rolü.

---

## (iii) KART GEREKSİNİMLERİ + OPERATÖR-BLOKLARI

### KART gereksinimleri (ön-kayıt `research/cards/` olmadan ölçüm YOK)

- **EDG-2026-019** (skill görüş/yaşam-döngüsü): kart `status: registered`, **ölçüm kodu HENÜZ
  YAZILMADI**; R-figürleri (vcp +0,116R / momentum-burst −0,114R) canlıda YENİDEN-ÜRETİLEMEDİ
  (`eksen2.uretilen=0`). Ç3 katalog düzeltmesi ön şart. (SABAH-TRIYAJI Kalem 11 / §iv; ROADMAP:328-330)
- **WP-K genişleme:** her yeni aile için ön-kayıt kartı — WP-QC (b)-kovası (idio-skew/overnight/
  mevsimsellik) + bileşen-ders Ek-B ①-⑤ + transkript-LLM/13F. Kill-list + K-grid + taban-fazlası.
- **C2-5 delist-dahil evren arşivi** modülü (WP-UX D3-c): kart **ZORUNLU** + Massive kararına bağlı
  (ROADMAP:167, 713).
- **EXE-2026-002-R1** (kill#4 daraltma): kart ön şartı — kod eşleşmeyenleri `sinif_dagilimi` ile
  ayırıyor; kill kapısının BOZULMA sınıflarına daraltılması ayrı tur (ROADMAP:252-255, 335-336).
- **WP-M M8:** K-defteri↔kart senkronu retro kartları.

### OPERATÖR-BLOKLARI (kod değil, hüküm; kaynak §6.1 + SABAH-TRIYAJI §iii)

| # | Blok | Bağ / kaldıraç |
|---|---|---|
| OB-1 | **N1 bildirim kanalı token** (Telegram/webhook boş → fail-notify her koşuda NO-OP; teslim edilmemiş sev-1: korumasız 40 · MIRROR_DRIFT 34 · NAKED_POSITION 8) | EN ACİL; alarm teslimini açar |
| OB-2 | **systemd exit-143 daemon-reload** (birim dosyasında `SuccessExitStatus=143` v225'te YAZILDI ama canlı reload bekliyor) | **OB-1'den ÖNCE inmeli** — yoksa her restart "FAILED" bildirir |
| OB-3 | **N4 cf çıkış-sadakati bakım penceresi** (saatler sürer + state'e yazar → canlı worker durur) | %96 skor havuzundaki +0,039R iyimserliği kapatır |
| OB-4 | **Restart → PBO `pencere_id` damgalaması başlasın** (WP-M M2) | OB-2 ile AYNI pencerede binebilir — çapraz kaldıraç |
| OB-5 | **FMP/Massive plan** (FMP 402 → temel/kazanç/insider katmanı ölü; rejim %60 tek-kaynak) | WP-K K1 (G5 in-play) + WP-D veri |
| OB-6 | Melez pozisyon farkı kapansın mı (iç 54/64/43/33 vs ayna 25/37/22/22, ~%49) — WP-S | operatör |
| OB-7 | Uyuyan yol `dormant_setup` (32 plan / 0 işlem / 1 GO): (a) icraya bağla (b) kapı GO vermesin (c) geri al | ne alıp sattığımızı değiştirir; kart+kill-list gerekir |
| OB-8 | EDG-021 ikinci-koşum tanım-eşitleme — WP-K K3 | operatör |
| OB-9 | Skill terfi/emeklilik onayı (motor-içi otomatik bayrak yasağı, 2026-08-06) | EDG-2026-019 karti besler |
| OB-10 | git MEKANİK kapısı (PATH-shim/wrapper — gece 2 ajan `git stash` hasarı) | araç/süreç kararı |
| OB-11 | Font/typeset — Geist EMEKLİ kararı verildi; aday seçimi WP-UX D4 | operatör onaylı yön |

---

## (iv) ÖNCELİKLENDİRİLMİŞ PLAN

**Bağlam:** SIRALAMA'ya göre WP-M + WP-H "sürekli-serpiştirilmiş" (ROADMAP:752-753); aktif dalga
WP-N (N1→N2→N3→N4) + WP-S + (sırada) WP-UX. Aşağısı bu serpiştirmeye slot önerir.

**P0 — Operatör-kapılı, tek bakım penceresinde çapraz kaldıraç (EN YÜKSEK):**
1. **OB-2 (systemd exit-143 reload) → OB-1 (N1 kanal token) → OB-4 (restart→PBO damgalama, WP-M M2).**
   Üçü aynı pencerede: exit-143 kanalı kapılıyor; restart hem worker'ı tazeler hem PBO `pencere_id`
   damgasını başlatır (sert PBO kapısı canlıda NO-OP'tan çıkar). Tek pencere = bir WP-S2 P1-bitişiği
   + bir WP-M borcu birden kapanır.

**P1 — Kod-güvenli, ucuz, serpiştirilebilir:**
2. **WP-M M7** (prescreen kod-sürümü damgası) — tek damga; canlı-defter↔Search teşhisini açar.
3. **WP-M M8** (K-defteri↔kart senkronu, retro kartlar) — hijyen; kart disiplini boşluğunu kapar.
4. **WP-M M9** (Chen-2022 t-hurdle referans notu) — doküman; K-cezası şeffaflığı metodoloji bacağı.
5. **WP-P P-A kısmi** — RUNBOOK'ta betiği ZATEN VAR olan alarmların girdilerini yaz (32'yi düşür);
   gerçekten kablosuz kalanlar beyanlı borç olarak kalır. *Dosya: `ops/runbook_uret.py` kaynak
   eşlemesi + kaynak betik başlıkları (meridian/tests'e dokunmadan içerik).*

**P2 — Metodoloji çekirdeği (ölçüm işi; en yüksek kaldıraçlı M1 önce):**
6. **WP-M M1** (KIYAS-KİRLENMESİ) — olay-penceresi-dışı kıyas; TÜM evren-medyanı ölçümlerini
   düzeltir. Yeni WP-K aile ölçümlerinin tabanını temizler → K-genişlemesinden ÖNCE değerli.
7. **WP-M M3/M4/M5/M6** (blok-bootstrap CI · empirical-Bayes küçültme · A4 isabet bandı · PK4/PK5
   yol-tutarlılık) — ölçüm-şablonu paketi; PK4/PK5 yeni aile disiplininin ön şartı.
8. **WP-M M11** (KATMAN-4 alan merceği → plan defteri ~20 alan) — bir sonraki tarama kovası.

**P3 — WP-K genişleme (kart-önce; M1/M6 tabanı hazır olunca):**
9. **EDG-2026-019 ölçüm kodu** (OB-9'u besler; N2b skill rotasyonunu açar).
10. **Bileşen-ders Ek-B ① rejim-kadranı kartı** (EDG-005 hükmünü yeniden yargılar — YAŞAYAN kola
    en yakın) → ardından idio-skew 354 / overnight 16 / mevsimsellik kartları.
11. **HEDEF-5:** transkript-LLM + 13F aileleri (veri/operatör hazır olunca).

**P4 — Operatör kararları (yüzeye çıkar, kod bekletme):** OB-5..OB-8, OB-10, OB-11. WP-K K1 (G5)
OB-5'e, K3 OB-8'e bağlı; K2 (G6) operatör yeniden-açılışına bağlı.

**AYRI TUT (bu planın DIŞI):** WP-UX D0-D6 + F1-F15 yeniden-tasarımı kendi programı (ROADMAP:697).
WP-P yüzeylerini WP-UX yeniden düzenleyecek — burada YENİDEN AÇILMAZ. WP-P'nin bu plandaki tek
ileriye-dönük payı **P-A** ve **D6 kabul çıtası** olma rolüdür.

---

## ÖZET SAYIMLAR (dönüş)

- **WP-M:** **11 kalem açık** (9 metodoloji/yasa + PBO/DSR taban [M2, restart-şartlı] + araç-kör-nokta
  artığı [M11]). M10 koşullu-ertelenmiş. Gece kapananlar (v196/v214/kart-tekillik) düşüldü.
- **WP-K:** kendi kuyruğunda **ölçülmemiş hipotez YOK**; **3 artık kalem açık** (G5 askı · G6 raf ·
  EDG-021 2. koşum) + genişleme hattı (transkript-LLM/13F + WP-QC b-kovası + bileşen-ders Ek-B) —
  bu hat kart-önce, WP-QC/HEDEF-5'te park.
- **WP-P:** yüzey programı (P1-P10) **KAPALI**; WP-UX'ten **AYRI tek canlı borç = `docs/RUNBOOK.md`
  32 operatör prosedürü (P-A)** + WP-UX D6 kabul çıtası olma rolü.
- **WP-P ≠ WP-UX:** WP-P = gereksinim/doktrin + RUNBOOK içeriği (markdown el kitabı); WP-UX =
  yüzey/icra (D0-D6 + F1-F15 + modüller). Gece inen "görünürlük turu" WP-N N5'tir, WP-UX değil;
  WP-UX D0-D6 **hiç ilerlemedi**.
