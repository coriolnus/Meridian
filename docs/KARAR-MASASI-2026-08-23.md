# KARAR MASASI — 2026-08-23 sabahı (Rol-1 hazırladı; karar mercii OPERATÖR)

Gece filosu kapısız stokun tamamını bitirdi. Aşağıdaki her kalem SENİN kararını bekliyor;
hiçbiri birbirini bloke etmiyor, sıra önerisi kolaydan zora. Kimlikler §5 tablosuyla aynı.

## A. Şimdi verilebilir kararlar (5 + 2 yeni)

| # | Kimlik | Soru | Seçenekler | Rol-1 tavsiyesi |
|---|---|---|---|---|
| 1 | `B-CHOP-BUTCE` | Chop kapalılığı politika mı yan etki mi? | A: kasıtlı say (tahta+hermes kapsamı) · B: eşik kartı · Üçüncü yol: A'nın sonucu şimdi + gerekirse B'nin kartı | **Üçüncü yol** — @chop hipotez israfını kes; tek temiz kaldıraç chop tabanı, kart-önce. Brief: `docs/KARAR-BRIEF-CHOP-BUTCE-2026-08-22.md` |
| 2 | `B-PENCERE-KAYDIR` 🆕 | Tarama/emir penceresi ~13:45'e kaysın mı? | Evet (kart-önce uygulanır) · Hayır · Daha veri | **Evet yönünde güçlü kanıt:** EDG-047 kendi verimizde −%42,3 [−%44,3, −%40,1] risk daralması; bedel medyan +4,65 bps (|m2| 55 geniş). Strateji-kimliği değişikliği — kartı ancak sen "evet" dersen yazarım |
| 3 | `B-E1-LIMIT` 🆕 | Limit bacağı (execution_v2) ne olacak? | Kapalı kal (varsayılan) · Güç-artırma ölçümü iste · Aç (önerilmez) | **Kapalı kal + 042 birikimini bekle** — E1 hükmü yeniden açık ama H2 ölçülemedi, Ö3 CI'ları 4/4 sıfır-içi; bugünkü kanıt hiçbir yönü desteklemiyor. D5 de bu pakete bağlı |
| 4 | `B-RUNBOOK-KAPSAM` 🆕 | RUNBOOK üreticisi `dagit.sh` başlığını da okusun mu? | Evet (tek satır BETIK_KUMESI) · Hayır | **Evet** — sürüm-terfisi sözleşmesi kaynağında yazılı, belgeye de aksın; emsal (seçenek-C) senin onayınla genişlemişti |
| 5 | 25a/25c/25d | "Beklet" sürsün mü? | Sürsün · Kaldır (25b 5/6 zaten damgalandı) | Nötrüm — envanter hazır, iş S boyutlu; 25a'daki `backtest_gate`/`kill_switch_file` yanıltıcılığı kaldırmayı hak ediyor |
| 6 | Uyuyan kurulum (dormant_setup) | Ön-bağ arkaya bağlansın mı? | Bağla (kart-önce) · Bağlama · Damgala | Ölçüm kartı yazılmadan bağlanmaz; istersen kartı yazarım (31 plan / 0 işlem envanteri hazır) |
| 7 | ARSENAL politikası | 15e giriş + 29 çıkış kanıt çıtası | çerçeve senin | 15d tasarımı indi (`docs/TASARIM-15D-PIT-FAKTOR-SETI-2026-08-23.md`) — ARSENAL çerçevesine girdi olur |

## B. Bakım penceresi ✅ KAPANDI (2026-08-23 ~10:50 — operatör+Rol-1 birlikte yürüttü)

H3 tur-2 canlıda (tetik-testi kanıtlı; iki alet vakası yakalandı-düzeltildi) · LoadCredential faz-1 canlıda (401-kanıt) · N1 uçtan uca ölçüldü. OPSİYONEL kalan: LoadCredential --faz2 (ortam kanalını kapatır; betik şartı kendisi ölçer). Eski liste:

1. **H3 tur-2**: `deploy/oracle-a1/h3_tur2_sertlestir.sh` — fazlı kur/doğrula/geri-al + tetik-testi;
   hedef iki birim: tick-watchdog (ROOT koşuyor!) + fail-notify. Adımlar betiğin başlığında.
2. **DASH_TOKEN → LoadCredential** (rotasyonla aynı pencerede): `dash_token_credential.sh` hazır;
   api tarafı CREDENTIALS_DIRECTORY-önce okuyor (v184).
3. ~~EDG-2026-044 aşama-2~~ **DÜŞTÜ (2026-08-23 sabahına doğru):** aşama-1 kazancı %17,49 < %20 —
   kart kapandı, tavan kalır; canlı denemesi gündemden çıktı.
4. Hepsi tek pencerede birleştirilebilir; sırası RUNBOOK + betik başlıklarında.

## C. Erişim / para / veri kararları

- ~~OCI bucket~~ ✅ **TAMAMLANDI 2026-08-23 akşam:** S3 replica canlı + geri-yükleme tatbikatı geçti (893/27.034,92 birebir)
- **QC**: blok gerekçesi düzeltildi — login DEĞİL makine kurulumu (dotnet/docker yok, boyut L).
  Karar: kurulum işi açılsın mı?
- **Massive planı**: artık ~son 2 ay — 2004'e giden bar arşivi YENİDEN ÜRETİLEMEZ kalıntı;
  üçüncü yedek kopya + delist-bar kaynağı kararı bununla birleşik.
- **OCI bucket** (off-box PITR) · **`dataset.load`↔bars_integrity kapsamı** · **insider-veri yolu**
  (15d'nin A6 adayı için FMP-plan vs EDGAR-ingest).

## D. Bilgin olsun (karar istemez)

- **F8 açık soruları A3/A4** (hermes üretici adı; `n_ok` tipi) — tasarım belgesinde, acele yok.
- **042 haftalık** Cts 10:29 otomatik; ilk anlamlı tekrar 08-29. K2/K3 reconcile damgası bekliyor.
- **Ajan-durdurma notu**: F9/H3 ajanını gece durdurmuşsun (muhtemelen bekleyici temizliğinde) —
  işi bitmiş kalitedeydi; kalan iki küçük parçayı ops/doküman istisnamla ben tamamladım (82b84a0).
  İtirazın varsa `git revert` ile tek commit'te geri alınır.
- İki yasak bekleyici betiği (dün 16:14, benim hatam) 10 saat sonra yakalandı, öldürüldü,
  ders kalıcı hafızada.

## E. Gece-2 eklemeleri ✅ HEPSİ SONUÇLANDI (12/12 — brainstorm turu + iki canlı op kanıtla bitti) (2026-08-23 geç)
- **bars_intraday retention** 🆕: arşivde tavan yok (~2,3GB/yıl; disk 39G boş — acele değil). Karar: retention süresi (öneri: 180 gün + bucket'a aylık arşiv) — 13-tasarımının açık sorusu.
- **registry budaması uygulaması** (dry-run temiz: 3 alan × 133 örnek) — tek komut, istediğin an:
  `ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && .venv/bin/python ops/registry_olu_alan_budamasi.py --uygula'`

## F. Insider (15d-A6) fizibilite soruları (2026-08-23 gece — belge: TASARIM-15D-A6-INSIDER)
Öneri EDGAR-ingest (bedava, M-boy). Beş ayrık onay: (1) yol onayı (EDGAR mi) · (2) hedef katman (research-arşiv mi canlı-defter mi — öneri: research) · (3) ~9k isteklik dikiş koşusu izni (kibar kadanslı, bir gece) · (4) derivative-tablo kapsam kararı · (5) kart sırası (A2 gelir-momentumundan önce mi sonra mı — öneri: sonra).

## G. Eleme-gecesi eklemeleri (2026-08-24)
- **C4/NOUS_MODEL kapanış adayı:** 24c'nin kapanışı KOVA-3'ün gerekçesini düşürdü — C4 bloğunun kapanış onayı senden.
- **EDG-019 vakası bilgin:** görüş katmanı kill#1 ile kapatıldı (kartsız sevk + p95 ihlali); yeniden açılış resmî kart koşumuyla — istersen o ölçümü kampanya ÖLÇ sınıfına ekleriz.
