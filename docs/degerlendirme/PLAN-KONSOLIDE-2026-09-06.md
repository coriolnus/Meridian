# Konsolide plan — 2026-09-06 akşam (ROADMAP tam yeniden değerlendirme sonrası)

Kaynak: 52 açık TSK + 9 aktif cephe + §5 operatör masası + 12 aktif kart, 24 salt-okunur ajan (ham: `ROADMAP-DEGERLENDIRME-2026-09-06-{tsk,wp}.json`);
hafıza sayfaları (S1 bağımlılık, S2 hedef-sapma) ipucu olarak kullanıldı, kanıt olarak DEĞİL (13/22 iddia bayat çıktı). Hüküm Rol-1'in;
DROPPED yalnız öneri, karar operatörün. Bu belge ROADMAP'in yerine geçmez; o anki sırayı ve kapıları tek sayfada verir.

## 0. Güncelleme — 2026-09-07 sabah (09:5xZ, Rol-1)

| Kalem | Durum | Kapı / sonraki adım |
|---|---|---|
| TSK-159 S5 tohum değişimi (A) | ✅ OPERATÖR ONAYI (sabah) → plan 9764130 · Task-1 `ops/tohum_pit_yenile.py` + v433 main'de (030d6d1) · **dağıtım #24** 75a0d1f 08:27Z · ruling 1-6 (kaynak=replay_seed kalır, sv=91, arşiv, eğri dokunulmaz, store kapısı, **bitiş = eski tohum sınırı 2026-07-24** — canlı dönemle örtüşmez) | A1 kuru koşum 08:58Z'den beri (Monitor) → rapor kabul bandı n∈[800,884], sızıntı 0 → rapor **scp+commit** (dagit `--delete` siler) → **20:45Z pencere**: worker stop → DB yedek → `--uygula` → `trade_id_yeniden_numarala` (canlı T00096… korunur) → start/healthz → ROADMAP/kart/günlük |
| TSK-138 brifing denetçisi (dilim-1 teşhis) | ✅ main'de (9894456) ve **dağıtım #25** 23b0904 09:31Z: olaya `model` künyesi + `cevap_bas` (süzgeçli 200 kr); v434 22 çivi 11/11 mutasyon | ilk gerçek ölçüm **22:04Z** brifingi → hipotez (SOUL "SESSIZ" ↔ JSON) doğrulanırsa dilim-2 (istem sertleştirme / ayrı denetçi profili); künye 'istenen model'dir, 'cevaplayan' değil (kapı sabitliyor) |
| EDG-080 K2 pilot gün-1 | 05:00Z cron → min_refresh_interval ile **15:20:57Z**'ye ertelendi (op 13edb4ee pending) | 15:27Z zamanlayıcı: llm_requests/mental_models kontrolü → kart kaydı |
| Pazartesi seans | 13:30Z açılış | 13:47Z zamanlayıcı: EDG-078 gölge sıralama ilk seans, TSK-156 as_of ilk yazımı, TSK-143 20:32Z sessizlik |
| Canlı triyaj (03Z+) | bilinen kalemler: `korumasiz_motor_disi_pozisyon` (ROADMAP'te), MECHANISM_STALE (16,6 gün, TSK-102 hükmü), massive/fmp uyarıları; bar uyarıları kendi kuru koşumumdan | yeni kalem yok |
| Zamanlayıcılar (oturum cron'u) | 13:47Z · 15:27Z · 20:43Z (yalnız hatırlatıcı; prosedür planda) | oturum cron'u güvenilmez → uyanışta `date -u` ile telafi |
| S5 kuru koşum sonucu (10:23Z) | ✅ KABUL: n 843 (band 800–884), sızıntı 0, avg_r ≈ aynı; rapor repoda (61904e3) | pencere İKİ PARÇA: 20:45Z durdur+yedek → 21:03Z uygula+id yeniden numaralama+başlat (nabız 900 s eşiği) |
| Operatör kararlarının icrası (11:57–12:5xZ) | ✅ EDG-2026-085 tick pilotu kartı (TSK-013 ACTIVE; ADIM-0 ölçüldü: sembol/gün maks 14, tek bağlantı → q-abonelik) · TSK-175 uyuyan yol belgesi (öncül bayat: 10 plan, VLO işlem, CRM keşif; öneri: kalsın + 2 hijyen) · TSK-064 §6 Vault Faz-2 eki (pinli ikili, file backend, loopback HTTP, Shamir 1/1 0400, ExecStartPost oto-unseal, Vault Agent template) | TSK-013 pilot kodu S5 + 09-13/14 sonrası; Faz-2 ayrı dalga (Faz-0/1 sonrası); uyuyan yol kararı yeniden sorulmaz |

## 1. Bu gece (uçuşta / zamanlanmış — bildirimli)

| Kalem | Durum | Kapı / sonraki adım |
|---|---|---|
| EDG-067 kıyas → TSK-060 hükmü | ✅ HÜKÜM 22:4xZ: KALDI (bölüm@3 %0 vs %27,8; dosya@3 %13,9 vs %55,6; p50 44 s vs 0,6 s) | TSK-060 OPERATOR: sökme kararı 083/084 hükümleriyle (09-13/14); TSK-163 recall temelinde açılmaz; TSK-167 sqlite-vec |
| TSK-172 + TSK-173(a) | ✅ CANLIDA — dağıtım #23 471c8bf 20:57Z (suite #31 10686/1 → RUNBOOK+korpus yeniden üretildi) | kapandı |
| 22:04Z akşam brifingi (06) | ✅ teslim; denetçi 2/2 şema dışı → llm_dustu, HAM teslim (model/cevap ölçülemedi) | → TSK-138 dilim-1 enstrümanı canlıda (#25); 07 akşamı ilk ölçüm |
| 00:05Z araç sondası | ✅ nemotron-super/ultra + m2.7 tool_calls; gemma 429 | ✅ reflect yedek zinciri 01:11Z canlı (m3→m2.7→nemotron-super) |
| 00:10Z S3/PK/NK · 00:45Z S4–S8 | ✅ 00:17Z / 01:10Z, 8/8 içerik, 120–561 s | ✅ 11 sayfa gün-1 sayımı 449/478 (%94), PK/NK geçti; R4 kuralı 7. gün için kayıtlı |
| 03:00Z ingest r5 · 03:30Z yedek · 05:00Z pilot cron | ✅ r5 04:15Z ok 4 / kalıcı 4 (TSK-144 DONE) · yedek rc=0 · pilot cron tetikledi, tazeleme 15:20Z'ye ertelendi (semantik) | 15:27Z kontrol (§0) |

## 2. Hafta — ölçüm pencereleri (dokunulmaz)

| Kart / kalem | Hüküm günü | Not |
|---|---|---|
| EDG-080 K2 pilot (TSK-142) | 09-13 | minimax payı ≤10/gün |
| EDG-083 üç sayfa (TSK-160) · EDG-084 beş sayfa (TSK-171) | 09-13 · 09-14 | uydurma + gerçek kullanım + bayatlık; toplam minimax ≤55/gün |
| EDG-081 konsolidasyon zinciri (TSK-157) | ~09-12/20 | konsolidasyon m3'ten 27 çağrı yedi — kill#5 gözlemi |
| EDG-078 gölge sıralama (TSK-126→078) | 40 seans, ~11-03 | ilk seans 09-08 |
| TSK-156 as_of ilk yazımı · TSK-143 sessizlik · EXE-003 20 seans | Pazartesi (BUGÜN 09-07) | 13:47Z zamanlayıcı; S5 penceresi seans DIŞI (20:45Z) |
| EDG-042 haftalık koşum #5 (PRG-01 23b, B4) | 09-12 | dört kova eşik altı; sıradaki koşum |

## 3. Sırada (kapı açık, Rol-1)

| Kalem | Öncelik | Kapı |
|---|---|---|
| TSK-162 triyajda recall | bu hafta | disiplin + 2 hafta sayım; kod yok |
| TSK-020 [UYGULA-3] bars→Parquet | ✅ KOD MAIN'DE 09-07 13:5xZ (67b86f4: bar_arsivle + bar_sorgu, v435/v436) | dağıtım #26 S5 sonrası → S4 A1 ilk arşiv + kapsam raporu (Rol-1); 3.3 canlı yol ayrı kart |
| TSK-167 pano anlamsal arama | ✅ dilim-1 KOD MAIN'DE 09-07 19:0xZ (hafiza_ara CLI + haftalık tazeleme birimi) | A1 kurulum + ilk sorgu dağıtım #26 sonrası; dilim-2 pano ucu |
| TSK-064 sır yönetimi Faz-0/1A/1B (+Faz-2 Vault) | gelecek hafta | tek dalga; son basamak KARARLI: HashiCorp Vault, oto-unseal dosya |
| TSK-137 Ağustos defteri kırpma | Ekim başı | aylık bakım |
| TSK-132 palet artıkları | bu ay | eski sayfalar jetonlar.css |
| TSK-012 dalga-B (pano sohbet) | bu ay | icra sırasına alınmalı |
| TSK-170 (a) denenenler sayfası + mekanik çivi | EDG-083 hükmü | (b) kart_benzer canlı |

## 4. Kapılı (tetik bekliyor)

| Kalem | Tetik |
|---|---|
| TSK-161/163/164/165/166/168/169 (hafıza genişlemeleri) | EDG-083 hükmü GEÇTİ (09-13); 163 ayrıca EDG-067 |
| TSK-066/067/068 (⑥ sinyal serisi) | TSK-159 S5 (bugün 20:45Z uygulanıyor) + EDG-069 hükmü (kod KOVA C sırasında) |
| TSK-016/093 (skill öz-iyileştirme, karışık üretici) | EDG-019 kill#4 + EDG-063 ölçümü |
| TSK-043/063 (Faz-6 kilitleri) | kanıt 11/20 + INTRADAY_ARM operatör onayı |
| TSK-015/018/010/096/097/104 | tetik olayları (Ajan-B, alarm sınıfı, filo erişimi, trend sorusu, çok-kullanıcı, EXE-011 ilk hafta) |
| TSK-131 disk | /opt/veri ≥120 G (~09-13) |

## 5. Operatör masası — 2026-09-07 10:12–11:22Z tek tek soruldu (10 karar)

| Kalem | Karar |
|---|---|
| ~~TSK-159 S5~~ | ✅ sabah: A varyantı → icra §0 |
| TSK-060 Hindsight | ✅ **MELEZ**: sayfalar kalır, recall arama katmanı olmaktan çıkar, arama sqlite-vec (TSK-167); yürürlük 09-13/14 hükümlerine bağlı (KALDI → sök) |
| TSK-044 FINVIZ Elite | ⏸ BEKLEMEDE (4.) — önce risk-azaltma/tavan kuralları |
| TSK-045 FMP planı | ⏸ BEKLEMEDE (4.) — insider kanıt göstermeden para yok |
| EDG-2026-070 mid-cap üst-sınır kartı | ✅ ONAYLANDI, sıraya (ADIM-0 S5 + pencereler sonrası) |
| TSK-131 disk 120 G | ⏸ eşik günü yeniden sorulacak (bekçi 110 G) |
| TSK-064 sır yönetimi son basamak | ✅ **HashiCorp Vault** (OpenBao değil), unseal otomatik — anahtar dosyası A1'de; BEKLEMEDE-7 kapandı |
| B-AJAN-TAVAN | ✅ model kademeli: Sonnet 25 · Opus 10 · Haiku 40 |
| TSK-013 tick Senaryo-A | ✅ kart YAZILDI (EDG-2026-085); pilot kodu S5 + pencereler sonrası |
| dormant_setup uyuyan yol | ⏸ "daha detaylı bakalım, şimdilik kalsın" → TSK-175 belgesi YAZILDI (öncül bayat; öneri: kalsın) — karar istendiğinde §4 tablosuyla |
| §7 düşürme önerileri | ⏸ "daha sonra sor" |
| TSK-063 INTRADAY_ARM | sorulmadı — kanıt 11/20, dolunca sorulur |
| B-DELIST-KAYNAK | sorulmadı — EDG-070 ADIM-0 sonucu girdi üretecek |
| Remote Control | operatör tarafında; bu oturum hâlâ inactive |

## 6. Bugün kapananlar (kanıtlı)

TSK-151, TSK-153, TSK-154, TSK-058, TSK-126, TSK-047, TSK-174 (zaten uygulanmış), TSK-172, TSK-173 (dağıtım #23); §6 EDG-071 (KISMİ→GEÇTİ notlu), EDG-072 (KALDI), EDG-079 (KALDI, icrası TSK-159);
§5 B-QC-LOGIN, B-AJAN-GIT ✅; cepheler PRG-06 🟢, PRG-07/09 🔶; PRG-05 gövdesinde 13, PRG-02'de 3, PRG-08'de 2, PRG-09'da 3 madde tarihçe.

**09-07 sabah ilerleyenler (kapanmadı):** TSK-159 S5 Task-1 main'de + dağıtım #24 (uygulama 20:45Z); TSK-138 dilim-1 main'de + dağıtım #25 (ölçüm 22:04Z). Dağıtım sayacı: #23 → #25.

## 7. Düşürme önerileri (karar operatörün — DROPPED yazılmadı; 2026-09-07: 'daha sonra sor'; TSK-013 listeden çıktı — Senaryo-A kartı açılıyor)

| Kalem | Gerekçe |
|---|---|
| PRG-02 "08-04 kitap yazımı — ÖLÇÜLEMEDİ, beyanlı" | kalıcı çözümsüz beyan; SB-4 geleceği koruyor |
| PRG-03 çapa-etiketi kuralı | CLAUDE.md §2 genel kural oldu |
| PRG-05 M1 kıyas-kirlenmesi | KYS-2026-001 ölçüldü, arşiv, fark önemsiz |
| §6 Retro kuyruk satırı | aktif kart değil, arşiv özeti |
| TSK-013 tick programı ücretsiz kaynak | geri dolum ölçülüyor, TSK-131 kararı kapsıyor (Rol-1 önerisi) |

## 8. Riskler

minimax 100/gün üç kart arasında (tavan 55); A1 4 OCPU — reflect/kıyas/geri dolum sıralı; hafıza bayatlığı — sayfa okuması ölçülenle doğrulanır (CLAUDE.md §2 kapısı);
ssh izleyicileri kopuyor — kısa yoklama deseni; bugünkü okuma hataları (yorum≠kod, kimlik deposu) hafızada.
YENİ (09-07): dagit rsync `--delete` A1'deki repo-dışı ölçüm çıktısını siler (S5 raporu önce scp+commit); sef brifingi kuru koşumu >300 s (model+denetçi çağrıları) — A1'de `timeout` ile koşulmaz, yetim hermes bırakır; oto-mod sınıflandırıcısı arka plan dagit'i ve komut gömülü cron'u reddediyor (ön plan / plana işaret eden cron).
