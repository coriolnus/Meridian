# Konsolide plan — 2026-09-08 (Rol-1; ROADMAP'in tamamından; 09:0xZ)

> Üretim yöntemi: ROADMAP 156 maddesi makineyle ayrıştırıldı (44 açık: 15 ACTIVE · 19 GATED · 8 QUEUED · 2 OPERATOR); 7 okuyucu + 3 bölüm okuyucusu (cepheler/operatör blokları/pencereler) + her çıktı için bağımsız çürütücü + tek sentez (workflow, 18 ajan); tamlık denetimi makineyle (44/44). Önceki sürüm: `PLAN-KONSOLIDE-2026-09-06.md` (§0–0d sabah masası orada kalır).

> Kaynak: ROADMAP tamamı (§2 tahta · §3 cepheler · §4 öneri havuzu · §5 operatör blokları · §6 kart hükümleri · §7 karar günlüğü) + kart dosyaları + bu oturumun olay defteri. Bu belge ROADMAP'in kopyası değil, **çalışma sırası görünümü**dür. HEAD `5ba0b3e` (2026-09-08 08:45Z), ağaç temiz.

## 0. Özet sayılar

| Kova | Adet | Kalemler |
|---|---|---|
| Uçuşta | 2 | TSK-064, TSK-176 |
| Ölçüm penceresi | 6 | TSK-142, TSK-145, TSK-160, TSK-171, TSK-162, TSK-012 (+TSK-168/169 EDG-083'e asılı) |
| Sırada (kapı açık) | 8 | TSK-159, TSK-156, TSK-043, TSK-138, TSK-014, TSK-020, TSK-167, TSK-132 |
| Kapılı (tetik bekliyor) | 17 | TSK-060, 066, 067, 068, 104, 128, 131, 137, 013, 015, 016, 018, 093, 161, 163, 164, 165, 166, 170 |
| Operatör masası | 6 | TSK-063, 044, 045, 097, 096, 010 (+açık kararlar §5) |
| Düşürme adayı | 1 | TSK-157 |

**Bayat ROADMAP satırları (düzeltilmesi gereken):**

| Kalem | Ne yanlış |
|---|---|
| TSK-159 | status ACTIVE, ama S5 2026-09-07 19:44Z uygulandı — kapanış yazımı eksik |
| TSK-156 | status ACTIVE, tüm dilimler git'te tamam — DONE'a çekilmeli |
| TSK-157 | ACTIVE + "ÖNCELİKLİ", ama kartı (EDG-077) KALDI ve minimax 09-08'de ücretli oldu — öncül geçersiz |
| TSK-137 | status QUEUED, ama canlı ilk kırpma 2026-09-05'te yapıldı |
| TSK-132 | başlık üç sorunu açık gösteriyor, ikisi kapandı (yalnız dilim-2 açık) |
| TSK-131 | başlıktaki projeksiyon geçersiz; güncel ölçüm ~09-13 diyor |
| TSK-066 | "TSK-159 hükmü tamamlanmadı" notu bayat; girdiler fiilen tamam |
| TSK-020 | UYGULA-1 "sıradaki adım" ama gövdesi H9 ile canlı — §4 ↔ WP6/H9 tek-kaynak ayrışması |
| TSK-012 | §2 TAHTA H1 satırı 2026-08-31'den beri donuk; dalga-B canlı, EDG-086 penceresi açık |
| TSK-142 / EDG-080/081 | kart eşikleri minimax'e dayanıyordu; model zinciri 09-08'de değişti, kartlara işlenmedi |
| TSK-163 | başlık iki-şartlı; EDG-067 zaten KALDI (09-06), fiilen tek şart kaldı |
| TSK-170 | "QUEUED, trigger —" ama bacak (b) canlıda, bacak (a) EDG-083'e kapılı |
| TSK-015 | tetiğin yarısı (Ajan-B canlı) 09-08'de gerçekleşti, metne işlenmedi |
| TSK-014 | "DONE damgası 09-04 gözlemine" ifadesi bayat; 09-05/06/07'de yeni arıza sınıfları çıktı |
| TSK-013 (§7 düşürme satırı) | anlamsız — kart 09-07'de açıldı, listeden çıktı |

## 1. Uçuşta

| Kalem | Durum | Kapı / sonraki adım |
|---|---|---|
| TSK-064 sır yönetimi (Vault) | D5+D6 bağımsız incelemesi koşuyor (09:04Z) | İnceleme bitince donmuş suite → merge → dağıtım #31 |
| TSK-176 altyapı-kod (Terraform+Ansible) | A1 fazı Task 2 ajanı koşuyor | Task 2/3 bitişi → inceleme+merge → T1; T2/T3 öncesi operatör kısa onayı |

## 2. Ölçüm pencereleri (dokunulmaz)

| Kalem | Durum | Hüküm günü / kapı |
|---|---|---|
| EDG-2026-042 gerçek friksiyon | dört kova eşik altında, "measuring kalır" | sıradaki haftalık koşum 2026-09-12 (VRTX çift-satır anomalisi işlenmemiş) |
| EDG-2026-080 K2 (TSK-142) | pilot sürüyor; K1 geçti | 2026-09-13 — hükümde model-zinciri sapması (minimax → ling-fin) not edilmeli |
| EDG-2026-083 (TSK-160/164/165/166/168/169) | measuring, R4 sayımı 460/478 (%96) | 2026-09-13 |
| EDG-2026-084 (TSK-171) | measuring, 5 sayfa kurulu | 2026-09-14 |
| EDG-2026-081 (TSK-145) | K1 erken sağlandı; K2 sürüyor | kart içi tutarsız: 09-13 mi 09-20 mi — Rol-1 netleştirmeli |
| EDG-2026-086 pano sohbet (TSK-012) | pencere dağıtım #29'dan (09-08 04:33Z) açık | 10 seans ∧ ≥100 mesaj → Rol-1 hükmü; kod dondurulmuş kalır |
| EDG-2026-078 gölge sıralama | pencere bugün açılıyor | ~2026-11-03 (40 seans) |
| TSK-162 recall sayımı (kartsız) | 2 haftalık sayım sürüyor | 2026-09-21; 09-08 çağrısı ölçülemedi |
| EXE-2026-003 / EDG-052 / EDG-055 | kart dosyaları ~2 haftadır güncellenmemiş | Rol-1 A1'de örneklem sayıp kartı tazelemeli (bu ajandan ölçülemedi) |

## 3. Sırada — kapı açık, Rol-1

**Bu hafta (ilk beş):**

| Kalem | Durum | Kapı / sonraki adım · gerekçe |
|---|---|---|
| TSK-159 PIT tohum yeniden kurulumu | iş bitti, kayıt eksik | Raporu EDG-082 kartına + ROADMAP'e işle, DONE — üç kalemi (066/156) birden serbest bırakır |
| TSK-156 S&P500 PIT kaynağı | tüm dilimler canlı | Sadece kapanış yazımı — beş dakikalık iş, bayat satırı temizler |
| TSK-043 Faz-6 edge_verdict okuması | hiç ölçülmemiş (born 08-14) | A1'de tek satır okuma; Faz-6 kilit tablosunun gerçek durumunu ilk kez gösterir |
| TSK-138 SOUL denetçisi dilim-2 | iki gecedir denetçi kendi altyapısından düşüyor | Model/bütçe kararı (super mi 240s mi) + "cevaplayan model" ölçümü |
| TSK-014 SOUL kural denetimi dilim-2 | TSK-138 ile aynı arıza, kod tarafı serbest | Önce A1 journal'da 22:00Z yük ölçümü, sonra kodla |

**Bu ay / sonra:**

| Kalem | Durum | Kapı / sonraki adım · gerekçe |
|---|---|---|
| TSK-167 docs anlamsal arama | dilim-1 canlı | Dilim-2: `/api/arama` + pano arama kutusu — MELEZ kararının tüketici bacağı |
| TSK-020 backend mimari dizisi | UYGULA-1'in ana gövdesi zaten canlı (H9) | Önce §4 ↔ WP6/H9 ayrışmasını düzelt; kalan gerçek iş yalnız Kademe C |
| TSK-132 palet artıkları | dilim-1 canlı | Dilim-2 mekanik: üç eski sayfa jetonlar.css'i doğrudan yüklesin |

## 4. Kapılı (tetik bekliyor)

| Kalem | Durum | Tetik |
|---|---|---|
| TSK-131 geri-dolum disk kararı | bekçi canlı, tavan kendini durduruyor | /opt/veri ≥ 120G (projeksiyon ~09-13); 110G'de erken uyarı |
| TSK-104 seyrelme gözlem paketi | EXE-011 canlı 09-02'den beri | ilk hafta birikimi (~09-09) → Rol-1 A1'de sayar, karta hüküm |
| TSK-066 ⑥a AN yeniden kurulumu | kart EDG-069 yazılı, kod yok | TSK-159 kapanışı + EDG-079/082 (fiilen tamam) — Rol-1 kapıyı resmen kapatmalı |
| TSK-067 ⑥b akış dengesizliği | kart yazılmadı | TSK-066 hükmü + IEX temsiliyet (~%2) ölçümü |
| TSK-068 ⑥c spread/zamanlama | kart yazılmadı | TSK-066 ve TSK-067 hükümleri |
| TSK-013 tick pilotu (Senaryo-A) | ADIM-0 taban örnekleyici A1'de koşuyor | EDG-083/084 hükümleri (09-13/14) |
| TSK-060 Hindsight kurulumu (MELEZ) | karar verildi, uygulama beklemede | EDG-083 (09-13) + EDG-084 (09-14) hükümleri |
| TSK-161 ajan brifingi sıkıştırma | tasarım hazır | EDG-083 GEÇTİ |
| TSK-163 bot recall (derlenmiş sayfa) | EDG-067 kolu düştü | EDG-083 GEÇTİ (tek şart kaldı) |
| TSK-164 öneri akıbeti sayfası | — | EDG-083 GEÇTİ |
| TSK-165 CLAUDE.md bakım sayfası | operatör ertelemesi | EDG-083 GEÇTİ |
| TSK-166 haftalık geriye bakış | operatör ertelemesi | EDG-083 GEÇTİ |
| TSK-168 defter özeti besleme | — | EDG-083 GEÇTİ |
| TSK-169 A1 gece başsız analist | — | EDG-083 GEÇTİ ∧ günlükte ≥2 "kaynak: zihin modeli" atfı (sayaç ölçülemedi) |
| TSK-170 denenenler defteri | bacak (b) kart_benzer canlı | bacak (a) EDG-083'e kapılı; mekanik çivi kapısız |
| TSK-128 validation_ledger kırpma | learn kapalıyken satır düşmüyor | learn kapısının yeniden açılması |
| TSK-137 defter rotasyonu | kod tamam, ilk kırpma canlı | Ekim başı bakım penceresi (TSK-155 sensörü izliyor) |
| TSK-015 ajan kalıcı hafızası | tetiğin yarısı doldu (Ajan-B canlı #28) | semantik-arama ihtiyacının ölçülmesi + operatör vetosu |
| TSK-016 Hermes öz-iyileştirme | kod yok | EDG-019 kill#4 ölçümü ∧ EDG-063 ilk gerçek koşumu |
| TSK-093 karışık-üretici ileri kalemler | rapor fail-closed | bir skill'in aynı anda det+LLM görüş taşıması (EDG-063) |
| TSK-018 olay-tetikli filo geçişi | kayıt, kod yok | "saatler kritik" bulgu sınıfının doğması (kanıt yok) |

## 5. Operatör masası

**Açık — cevap bekleyen:**

| Karar | Ne soruluyor | Kapı |
|---|---|---|
| TSK-064 icra | OpenRouter'ın iki yeni anahtarıyla `sudo ./deploy/oracle-a1/sir_rotasyon.sh --openrouter` (A1, bakım penceresi) | Anahtarlar üretildi (09-08 sabah); iki deneme (06:13Z, 07:23Z) betik hatasıyla geri alındı, dosyalar yedekle birebir; D5+D6 incelemede → dağıtım #31 → Rol-1 "hazır" der, operatör aynı komutu koşar |
| TSK-131 disk | 120G'de ne yapalım: dur / disk büyüt / sıkıştır | Operatör 09-07: "eşik günü yeniden sor" (~09-13) |
| TSK-063 Faz-6 | INTRADAY_ARM'ı açalım mı | Önce dört kilit kanıtla dolmalı (Faz-5 örneklem 11/20); sonra sorulacak |
| TSK-044 FINVIZ Elite | Ücretli token alalım mı | BEKLEMEDE 4. kez (09-07 10:13Z); yeni kanıt yokken sorulmaz |
| TSK-045 FMP plan | Ücretli plana geçelim mi | BEKLEMEDE 4. kez (09-07 10:14Z); EDG-011 askıda |
| B-DELIST-KAYNAK | Delist barları QC'den mi Massive'den mi alalım | Henüz sorulmadı; EDG-070 ADIM-0 girdi üretecek |
| TSK-175 uyuyan kurulum | İcraya bağlansın mı, tavsiye mi kalsın, geri mi alınsın | "Daha detaylı bakalım, şimdilik kalsın" (09-07); inceleme belgesi masada |
| TSK-138 dilim-2 | Denetçi modeli/bütçesi hangisi olsun | Operatör 09-08 06:30Z detay istedi, karar verilmedi |
| TSK-097 çok-kullanıcı | Çok kullanıcıya geçelim mi | Karar verilmedi; paket ondan önce açılmaz |
| TSK-096 metrik trendi | — | "Zamanla nasıl değişti" sorusu doğar ve mevcut yüzeyler cevaplayamazsa |
| TSK-010 filo MCP | — | Üç tetikten biri (cloud erişimi / bot-bot / Desktop'tan filo) |
| Remote Control | Bu oturum/istemci bağlantısı | Genel olarak açık (09-06) ama bu istemci "inactive" notu var — ölçülemedi |
| Düşürme onayları | PRG-02 kitap yazımı · PRG-03 çapa satırı · PRG-05 M1 kirlenmesi · §6 retro kuyruk | Dördü de "daha sonra sor" (09-07) |

**Bayat satırlar:** B-FAZ6-HUKUM (karar değil, bilgi) · TSK-013 §7 düşürme satırı.
**Ölçülemedi:** hermes SOUL.md + config.yaml masa satırı — F9 raporu bu oturumdan okunmadı; ayrı kalem mi yoksa üç profilin dizin kaydı mı belirsiz, Rol-1 netleştirmeli.

## 6. Cepheler

| Cephe | Durum | TSK'sız açık alt-kalemler |
|---|---|---|
| PRG-01 İcra/Friksiyon | AÇIK 🔴 | E1/E2/E4/E5 kuyruğu (B4 kararıyla kapalı, EDG-042 bandı dolmadan açılmaz) · WP1-C scale-out trail kusuru (alet kapalı) — 23b TSK-085'te |
| PRG-02 Sermaye/Koruma | KAPALI | — |
| PRG-03 Öğrenme | AÇIK 🔴 | 28c tekrar-deseni kökü (kart yok) · geçmiş retlerin 560'lık tabanla yeniden değerlendirilmesi (kart yok) |
| PRG-04 Veri/Evren | AÇIK 🔶 | S&P400/600 üyelik kaynağı yok (SEC 13(f) hiç çalışılmadı) · Massive plan kapsamı doğrulanmadı · EDG-055 earnings fail-open hükümsüz · EDG-056 MNST split kodu yok — 159/156/065/084 kimlikli |
| PRG-05 Ölçüm altyapısı | AÇIK 📋 | Faz-5 örneklem 11/20 · cf çıkış-yasası sapması (beyanlı borç) · M2 PBO/DSR tabanı · skill görüş canlı kanıtı (A1'de sorulmalı) · WP5-C donmuş-çekim aracı yok · WP5-D U6 mimari kararı |
| PRG-06 Sistem bütünlüğü | AÇIK 🟢 | H11 süre-tavanı canlıya alma kararı (kod hazır) — 176/078 kimlikli |
| PRG-07 Skill katmanı | AÇIK 🔶 | 24b SOUL.md kilidi etkisi hiç ölçülmedi · 24h skill rozeti damgası (damgala mı kaldır mı) |
| PRG-08 Pano/Operatör | AÇIK 🟡 | F3/F4/F11/F12 backend + F6/F7 viz akıbeti 08-31'den beri doğrulanmadı · D3-c LEAN/delist modülleri · app.js'te 31-33 ham hue jetonu · yazı-tipi turu |
| PRG-09 QuantConnect | AÇIK 🔶 | FREE kuyruk ②③④⑥⑦ · LEAN yerel pilot (dotnet/docker yok) · QC katman yükseltmesi kararı · bileşen-ders kartları (5 adet) |
| PRG-10 Referans verisi | KAPALI | — |
| PRG-11 Strateji/Seçilim | AÇIK 🔶 | WP11-G ölü yerel değişken (kaldır mı damgala mı) — 15c/15d/15e TSK-081'de |

## 7. Düşürme adayları (karar operatörün)

| Kalem | Gerekçe |
|---|---|
| TSK-157 minimax konsolidasyonu | Kartı (EDG-077) KALDI ile kapandı, iş EDG-081/TSK-145'e geçti, üstelik minimax 09-08'de tümüyle ücretli oldu — öncül teknik olarak imkânsız |
| PRG-02 "08-04 kitap yazımı ölçülemedi" | Kalıcı çözümsüz beyan; SB-4 geleceği koruduğu için düşürülmesi Rol-1'ce önerilmiyor |
| PRG-03 çapa-etiketi satırı | Kural CLAUDE.md §2'ye taşındı; ROADMAP satırı yedek/tarihçe |
| PRG-05 M1 kıyas-kirlenmesi | KYS-001 ölçüldü ve arşive alındı, kalan fark önemsiz |
| §6 retro kuyruk satırı | Aktif kart değil, yalnız arşiv özeti |

## 8. Bağımlılık zinciri

- **TSK-159 kapanışı** → TSK-156 kapanışı → TSK-066 (⑥a) → TSK-067 (⑥b) → TSK-068 (⑥c)
- **EDG-083 hükmü (09-13)** → TSK-161, 163, 164, 165, 166, 168, 169, 170(a) + TSK-060 (EDG-084 ile birlikte) + TSK-013 pilot kodu
- **EDG-080 K2 (09-13) / EDG-084 (09-14)** → TSK-142 Faz-2 yazma yolu · TSK-060 MELEZ uygulaması
- **EDG-081 hükmü** → TSK-145 kapanışı
- **Faz-5 örneklem 20/20** → TSK-063 dört kilit → operatör INTRADAY_ARM → Faz-6
- **EDG-063 ilk koşumu** → TSK-016 ve TSK-093 birlikte
- **learn kapısının açılması** → TSK-128 · **EXE-011 ilk hafta (~09-09)** → TSK-104 · **/opt/veri 120G (~09-13)** → TSK-131 · **EDG-070 ADIM-0** → B-DELIST-KAYNAK → TSK-065/084

## 9. Riskler

1. **09-13/14 tıkanması:** sekiz kalem, disk eşiği ve tick pilotu aynı iki güne yığılıyor; hükümler o gün sırayla verilmezse zincirin tamamı kayar.
2. **Ön-kayıt sapması:** EDG-080/081 eşikleri minimax'e göre yazıldı, model 09-08'de zorunlu değişti ve kartlara işlenmedi — hükümler ön-kayıtsız model üzerinden verilirse ölçüm geçersiz sayılabilir.
3. **Bayat ROADMAP satırları:** 15 satır fiili durumu yansıtmıyor (TSK-159/156/157/137/020 dahil); operatör yanlış öncelik verebilir, tek-kaynak yasası fiilen ihlalde.
4. **Kart bayatlığı:** EXE-003, EDG-052, EDG-055 kartları ~2 haftadır güncellenmemiş; pencereleri dolmuş olabilir ve kimse bakmıyor.
5. **Sır rotasyonunun yarım kalması:** OpenRouter'ın iki anahtarı hâlâ dönmedi ve iki otomatik deneme geri alındı — TSK-064 "tamamlandı" sayılırsa açık kalan kanal gözden kaçar.

## Envanter dışı (okuyucu ölçemedi)

Yok — envanterdeki eksik kimlik listesi boş geldi; bu belgede her açık TSK bir kez geçer.

## 10. Arşiv — kapanmış kararlar (operatör kararı 2026-09-08: kapananlar arşivde durur; §5 yalnız açık kararları taşır)

**Cevaplananlar (tarihçe, tek satır):** B-RUNBOOK-KAPSAM · B-PENCERE-KAYDIR · B-CHOP-BUTCE · B-KORUMA-KUR · B-BILDIRIM-N1 · B-PULLBACK-SILAH · B-KORUMA-POLITIKA · B-E1-LIMIT · B-ORACLE-TASIMA · B-OCI-BUCKET · B-DD-ESIK (0.16) · B-TAVAN-502 (A) · B-PG-ROTASYON · B-AJAN-TAVAN (Sonnet 25/Opus 10/Haiku 40) · TSK-046 QC login · TSK-047 beyin çeşitliliği · TSK-048 · TSK-049 · TSK-050 · TSK-064 ürün (Vault) · TSK-060 MELEZ · TSK-013 kart aç · TSK-159 S5 onayı · TSK-176 K1-K5 · EDG-070 kart onayı.

ROADMAP tarafında aynı ilke: §5.0 operatör masasındaki kapanmış girdiler §8 ARŞİV alt bölümüne taşınır (2026-09-08), tam metin korunur.
