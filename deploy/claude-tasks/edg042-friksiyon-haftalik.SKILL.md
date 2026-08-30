---
name: edg042-friksiyon-haftalik
description: EDG-2026-042 haftalık friksiyon ölçümü — eşik dolunca otomatik hükümlü koşum (Cumartesi 10:23)
---

Meridian deposunda çalışıyorsun: cd /Users/erdemozturk/AI-Trading (canlı sistem A1'de, ubuntu@130.61.126.87:/opt/meridian). Türkçe çalış. Bu görev operatörün 2026-08-22 talimatıyla kuruldu: "haftalık betimleyici tekrarı zamanla, eşik dolunca hükümlü koşumu otomatik başlat." Sen bu koşumun Rol-1'isin (hüküm işleme yetkin var); commit+push kalıcı yetkiyle atılır (CLAUDE.md madde 8).

GÖREV — EDG-2026-042 (gerçek friksiyon tahmini) haftalık koşumu:

[0] ÖNCE research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml kartını TAMAMINI oku. Eşikler, kovalar, kill kriterleri, karar kuralları ORADA DONUK — bu prompt kartın yerine geçmez, kart kazanır. CLAUDE.md ve MERIDIAN_ENGINEERING_LOG.md'nin oturum disiplinine uy.

[1] BİTİŞ KONTROLÜ (revize 2026-08-31, operatör kararı — P-3/AYRIK'ın ikinci yarısı): kartta
EŞİĞE ULAŞABİLEN ÜÇ kova da (giris_1345, cikis_hedef, cikis_stop) hükümlü verdict taşıyorsa
HİÇBİR ŞEY KOŞMA — operatöre "EDG-042 tamamlandı, edg042-friksiyon-haftalik zamanlanmış görevini
silebilirsiniz" de ve mümkünse görevi kendin devre dışı bırak. `giris_once` kolu BİTİŞE SAYILMAZ:
P-3 kararı gereği (AYRIK, ts anahtarı) o kol n=15'te DONUKTUR, eşiği (30) tanımı gereği hiç
dolamaz — dörtte-dört şartı korunsaydı bu görev kendini asla kapatamazdı (imkânsızın üstünde
sonsuz bekleyici). Eski üç-kova metni bu revizyonla değişti; tarihçesi kartta.

[2] ÖLÇÜM (dosya-ayrık, salt-okunur): DONMUŞ REÇETEYİ KARTTAN OKU — kartın "GÜNCEL DONUK
REÇETE İŞARETÇİSİ" kaydı hangi research/olcumler/ dizininin yürürlükte olduğunu söyler; bu
görev metni reçete dizini/sha TAŞIMAZ (revize 2026-08-31: buradaki sabit işaretçi İKİ KEZ
bayatladı — 08-24'te R2, 08-31'de ts revizyonu — ve bayat metin otomatik koşumu yanlış reçeteye
gönderirdi; tek-kaynak yasası: kopya değil işaret). Yeni tarihli dizin aç (research/olcumler/edg042_kosum_YYYY-MM-DD/), iki betiği BAYT-ÖZDEŞ kopyala (sha256'ları KOMUT.txt'e yaz), ssh-stdin deseniyle canlıdan salt-okunur snapshot çek (ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && ./.venv/bin/python -' < canli_cek.py > canli_ham.json), ölçümü snapshot üzerinde koş. CANLIYA VE state/'E TEK BAYT YAZMA. Kartın kill kriterleri aynen: kayıtlı bps alanı kullanılır (yeniden türetme yasak), broker_teyit=teyitli olmayan çıkış satırı olculemedi'ye düşer, tohum kıyasa girmez, kovalar birleştirilmez.

[3] EŞİK KONTROLÜ (kartın donuk eşikleri — sonuc.json'dan): giris_1345 n≥30 VE ≥10 ayrı
seans (P-3/AYRIK sonrası K1'in hüküm üretebilen TEK kolu budur); K2/K3 çıkış kova başına n≥15
VE ≥6 seans. `giris_once` HİÇBİR EŞİĞE TABİ DEĞİL: kalıcı betimleyici taban, her koşumda kartın
ÖLÇÜLEMEDİ damgasıyla yayımlanır, eşik beklemez, "yakında dolacak" diye sunulmaz.

[4a] EŞİK DOLMAYAN kova → BETİMLEYİCİ: CI hesaplama; kartın damga biçimini aynen bas ("ÖLÇÜLEMEDİ (n=X < eşik) — sayılar betimleyicidir, istatistiksel hüküm taşımaz.").

[4b] EŞİK DOLAN kova → HÜKÜMLÜ KOŞUM (otomatik — operatör talimatı): SEANS-kümeli bootstrap CI hesapla (B=5000, seed=20260812, yeniden örneklenen birim=SEANS/gün, yüzdelik CI — kartın features_asof damgası). Kartın karar kuralını AYNEN uygula (EDG-040 başabaş bandı [5,15] bps/bacak'a karşı): CI-alt>15 → "GERÇEK FRİKSİYON BAŞABAŞIN ÜSTÜNDE" (EDG-040 ACİL kalemi rakamla doğrulanır — operatör penceresi); CI [5,15]'i kesiyor → "BELİRSİZLİK BAŞABAŞIN İÇİNDE" (hüküm yok, ölçüm sürer, slippage_bps DEĞİŞTİRİLMEZ); CI-üst<5 → "MODEL MUHAFAZAKÂR" (şerh). Tek seans kova örnekleminin yüzde 40'ından fazlasını taşıyorsa CI şerhsiz yayımlanamaz (kill kriteri).

[5] ROL-1 İŞLEME: sonuçları karta işle — betimleyici turda kısa tarihli ara_kosum notu ekle; hükümlü turda verdict bloğu yaz (kova bazında; EŞİĞE ULAŞABİLEN üç kova — giris_1345, cikis_hedef, cikis_stop — hükümlüyse status → measured; giris_once sayılmaz, bkz. [1]). ROADMAP.md güncelle: §2 TAHTA'daki Ö-54 satırına durum, §7 KARAR GÜNLÜĞÜ'ne en üste tek satır. CI-alt>15 çıkarsa H0 tablosunun tepesindeki 🔴 ACİL kalemine "RAKAMLA DOĞRULANDI" notu düş ve raporunda operatör penceresini belirgin yaz. SİLME YOK — tarihçe korunur.

[6] DOĞRULAMA + KAYIT: kapsam testleri koş (uv run pytest tests/test_kart_kimlik_v219.py tests/test_kart_hukum_damgasi_v251.py tests/test_nous_eval_v131.py tests/test_wpm_sasi_v173.py) — TAM SUITE KOŞMA, DAĞITIM YAPMA (dagit.sh'a dokunma). codelaw kontrolü: uv run python -c "from meridian import codelaw; print(codelaw.report()['ok'])" True olmalı. Commit AÇIK YOL LİSTESİYLE (git add -A YASAK): kart + ROADMAP + yeni ölçüm dizini. Sonra git push origin main.

[7] RAPOR: kova tablosu (n/seans/medyan/p25-p75/damga ya da CI+hüküm), önceki haftayla değişim, bir sonraki eşiğe kalan tahmini mesafe. UYDURMA YASAĞI: canlıya erişilemezse ya da bir kill kriteri tetiklenirse ölçme, nedenini yaz, kısmi sonucu tam gibi sunma.
## EK — PENCERE HAKEM ADIMLARI (2026-08-23, EXE-2026-009 sözleşmesi)
Betimleyici koşumdan SONRA her hafta: (1) `python3 research/olcumler/edg042_kosum_2026-08-22/pencere_cek.py`
(canlıdan salt-okuma E2 çekimi) → (2) `python3 research/olcumler/edg042_kosum_2026-08-22/pencere_altbant.py`
— K1'i pencere alt-bantlarında (1330/1345) raporlar ve öneri-tetiğini değerlendirir. Çıktıdaki
`geri_al_onerisi` beyanı varsa operatör raporuna AYNEN taşı (geri alma otomatik değil). `orneklem_birikimde`
ise yalnız sayıyı yaz. Donuk 042 reçetesine (olcum.py/KOMUT.txt) DOKUNMA.

## REVİZYON KAYDI (2026-08-31)
Operatör onayı: "(a)'yı onaylıyorum, görev dosyasını da güncelle" — ai-trading-dc (Rol-1)
oturumunda, P-3/AYRIK kararının yan etkisi ai-trading-85 tarafından bulunduktan sonra.
Değişen üç bölge: [1]/[5] bitiş koşulu (ulaşabilen-üç-kova), [2] reçete işaretçisi (karta
devredildi), [3] eşik cümlesi (giris_1345 + giris_once muafiyeti). Eşiklerin DEĞERLERİ, karar
kuralı, kill kriterleri, bootstrap künyesi DEĞİŞMEDİ. Bu dosyanın VERSİYONLU KAYNAĞI depoya
alınacak (deploy/ altında, F9 sınıfı) — ~/.claude kopyası ondan türer; ayrışma orada görünür.
