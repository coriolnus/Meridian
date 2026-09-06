# Konsolide plan — 2026-09-06 akşam (ROADMAP tam yeniden değerlendirme sonrası)

Kaynak: 52 açık TSK + 9 aktif cephe + §5 operatör masası + 12 aktif kart, 24 salt-okunur ajan (ham: `ROADMAP-DEGERLENDIRME-2026-09-06-{tsk,wp}.json`);
hafıza sayfaları (S1 bağımlılık, S2 hedef-sapma) ipucu olarak kullanıldı, kanıt olarak DEĞİL (13/22 iddia bayat çıktı). Hüküm Rol-1'in;
DROPPED yalnız öneri, karar operatörün. Bu belge ROADMAP'in yerine geçmez; o anki sırayı ve kapıları tek sayfada verir.

## 1. Bu gece (uçuşta / zamanlanmış — bildirimli)

| Kalem | Durum | Kapı / sonraki adım |
|---|---|---|
| EDG-067 kıyas → TSK-060 hükmü | ✅ HÜKÜM 22:4xZ: KALDI (bölüm@3 %0 vs %27,8; dosya@3 %13,9 vs %55,6; p50 44 s vs 0,6 s) | TSK-060 OPERATOR: sökme kararı 083/084 hükümleriyle (09-13/14); TSK-163 recall temelinde açılmaz; TSK-167 sqlite-vec |
| TSK-172 + TSK-173(a) | ✅ CANLIDA — dağıtım #23 471c8bf 20:57Z (suite #31 10686/1 → RUNBOOK+korpus yeniden üretildi) | kapandı |
| 22:04Z akşam brifingi | zamanlı | TSK-138 + TSK-014 doğrulaması (events.jsonl kayıtları) |
| 00:05Z araç sondası | zamanlı | tool_calls üreten ücretsiz model → reflect yedek zinciri (sabah) |
| 00:10Z S3/PK/NK · 00:45Z S4–S8 | zamanlı, sıralı | sabah: dokuz sayfa uydurma tablosu + PK/NK + bayatlık sütunu |
| 03:00Z ingest r5 · 03:30Z yedek · 05:00Z pilot cron | zamanlı | TSK-144 kapanışı; gece özeti |

## 2. Hafta — ölçüm pencereleri (dokunulmaz)

| Kart / kalem | Hüküm günü | Not |
|---|---|---|
| EDG-080 K2 pilot (TSK-142) | 09-13 | minimax payı ≤10/gün |
| EDG-083 üç sayfa (TSK-160) · EDG-084 beş sayfa (TSK-171) | 09-13 · 09-14 | uydurma + gerçek kullanım + bayatlık; toplam minimax ≤55/gün |
| EDG-081 konsolidasyon zinciri (TSK-157) | ~09-12/20 | konsolidasyon m3'ten 27 çağrı yedi — kill#5 gözlemi |
| EDG-078 gölge sıralama (TSK-126→078) | 40 seans, ~11-03 | ilk seans 09-08 |
| TSK-156 as_of ilk yazımı · TSK-143 sessizlik · EXE-003 20 seans | Pazartesi | |
| EDG-042 haftalık koşum #5 (PRG-01 23b, B4) | 09-12 | dört kova eşik altı; sıradaki koşum |

## 3. Sırada (kapı açık, Rol-1)

| Kalem | Öncelik | Kapı |
|---|---|---|
| TSK-162 triyajda recall | bu hafta | disiplin + 2 hafta sayım; kod yok |
| TSK-020 [UYGULA-3] bars→Parquet | bu ay | tasarım belgesi var (2026-09-06); implementer |
| TSK-167 pano anlamsal arama | bu ay | EDG-067 sonucu + A1 CPU; küçük ve ölçülebilir |
| TSK-064 sır yönetimi Faz-0/1A/1B | gelecek hafta | tek dalga; OpenBao operatörde |
| TSK-137 Ağustos defteri kırpma | Ekim başı | aylık bakım |
| TSK-132 palet artıkları | bu ay | eski sayfalar jetonlar.css |
| TSK-012 dalga-B (pano sohbet) | bu ay | icra sırasına alınmalı |
| TSK-170 (a) denenenler sayfası + mekanik çivi | EDG-083 hükmü | (b) kart_benzer canlı |

## 4. Kapılı (tetik bekliyor)

| Kalem | Tetik |
|---|---|
| TSK-161/163/164/165/166/168/169 (hafıza genişlemeleri) | EDG-083 hükmü GEÇTİ (09-13); 163 ayrıca EDG-067 |
| TSK-066/067/068 (⑥ sinyal serisi) | TSK-159 S5 + EDG-069 hükmü (kod KOVA C sırasında) |
| TSK-016/093 (skill öz-iyileştirme, karışık üretici) | EDG-019 kill#4 + EDG-063 ölçümü |
| TSK-043/063 (Faz-6 kilitleri) | kanıt 11/20 + INTRADAY_ARM operatör onayı |
| TSK-015/018/010/096/097/104 | tetik olayları (Ajan-B, alarm sınıfı, filo erişimi, trend sorusu, çok-kullanıcı, EXE-011 ilk hafta) |
| TSK-131 disk | /opt/veri ≥120 G (~09-13) |

## 5. Operatör masası

| Kalem | Karar |
|---|---|
| TSK-159 S5 | tohum değişimi (A varyantı önerilen), bakım penceresi |
| TSK-060 Hindsight kurulumu | EDG-067 KALDI → sök / yalnız sayfalar için tut / recall'ı taban yaklaşımıyla değiştir — 083/084 hükümleriyle birlikte |
| TSK-044 / TSK-045 | FINVIZ Elite / FMP plan — para kararı |
| TSK-063 | INTRADAY_ARM onayı (kanıt dolunca) |
| TSK-131 | disk 120 G eşiği yaklaşınca |
| B-DELIST-KAYNAK, PIT mid-cap üst-sınır, B-AJAN-TAVAN, OpenBao | §5 kimlik tablosu, bekliyor |
| Remote Control | bu oturumun (Meridian App Main) bağlanması |

## 6. Bugün kapananlar (kanıtlı)

TSK-151, TSK-153, TSK-154, TSK-058, TSK-126, TSK-047, TSK-174 (zaten uygulanmış), TSK-172, TSK-173 (dağıtım #23); §6 EDG-071 (KISMİ→GEÇTİ notlu), EDG-072 (KALDI), EDG-079 (KALDI, icrası TSK-159);
§5 B-QC-LOGIN, B-AJAN-GIT ✅; cepheler PRG-06 🟢, PRG-07/09 🔶; PRG-05 gövdesinde 13, PRG-02'de 3, PRG-08'de 2, PRG-09'da 3 madde tarihçe.

## 7. Düşürme önerileri (karar operatörün — DROPPED yazılmadı)

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
