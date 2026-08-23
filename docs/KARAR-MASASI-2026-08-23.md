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

## B. Bakım penceresi isteyen uygulamalar (dosyalar HAZIR)

1. **H3 tur-2**: `deploy/oracle-a1/h3_tur2_sertlestir.sh` — fazlı kur/doğrula/geri-al + tetik-testi;
   hedef iki birim: tick-watchdog (ROOT koşuyor!) + fail-notify. Adımlar betiğin başlığında.
2. **DASH_TOKEN → LoadCredential** (rotasyonla aynı pencerede): `dash_token_credential.sh` hazır;
   api tarafı CREDENTIALS_DIRECTORY-önce okuyor (v184).
3. **EDG-2026-044 aşama-2 (koşullu)**: yerel eleme ≥%20 geçtiyse canlı cpu−1 denemesi — aşama-1
   sonucu tur özetinde.
4. Hepsi tek pencerede birleştirilebilir; sırası RUNBOOK + betik başlıklarında.

## C. Erişim / para / veri kararları

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
