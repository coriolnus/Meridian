# S2R — Pano YENİDEN TASARIMI (ADR + hedef IA) — 2026-08-02, operatör talebi

## Karar (ADR)
Operatör geri bildirimi: kademeli-giydirme birikimi panoyu DAHA karmaşık hissettirdi; beklenti
baştan tasarımdı. KARAR: iş emrinin (docs/UIUX-WORKORDER.md §3) hedef IA'sı ŞİMDİ kurulur —
"redesign replaces": eski yerleşim referans değil, kanıt; yeni dünya iş emrinin cam-kokpit tezi.
SINIRLAR: (a) motor korunur — vanilla JS + RENDER kaydı + CSP-self + kaynak-çivili test rejimi
(stack göçü DEĞİL, ADR'siz zaten yasak); (b) YASA-6 KORUNUMU — bugün panoda okunan her API/tablo
alanı yeni IA'da bir eve taşınır YA DA bilinçli-gerekçeli emekli edilir (öksüz tablo = kırmızı);
(c) veri semantiğine/eşiklere sıfır dokunuş.

## Hedef IA (12 görünüm → 1+6+detay)
- **GENEL BAKIŞ (Overview — J1'in evi, TEK EKRAN KAYDIRMASIZ):** Sessiz-Hat (zaten global) ·
  "dün gece ne oldu" tek paragraf-blok (son döngü: seans/aday/plan/silahlı) · sermaye-köken kartı ·
  bugün-ne-var (silahlı planlar / bekleyen onaylar sayacı) · alarm-bütçesi tek satır · 3 mini-trend
  (equity+DD, karne, kapsama) — HEPSİ özet; her kartın "→ alan sayfası" tek bağı. BAŞKA HİÇBİR ŞEY.
- **VERİ SAĞLIĞI:** kapsama/tazelik/karantina/bütünlük + intraday akış durumu (eski market-sağlık +
  intraday-veri parçaları buraya).
- **KOŞU & DÖNGÜ:** günlük döngü karnesi, koşu şelalesi, onarım geçidi, seans işleme geçmişi.
- **PORTFÖY & EMİRLER:** pozisyonlar, silahlı planlar, dolum akışı/mutabakat, sermaye detayı,
  reddedilen emirler (eski bugün+intraday'ın emir yarısı).
- **ÖĞRENME:** karne, gölge kollar (küçük-katlar hedefi), bileşen-IC+EB, hipotez/sprint, K-defteri
  (eski ogrenme+ajan+hermes+skiller+hafiza+performans BİRLEŞİR — en büyük sadeleşme burada).
- **GÖZETİM & ALARMLAR:** alarm gelen kutusu (runbook bağlı), bekçi ayrıntıları, alarm-bütçesi
  detayı, olay günlüğü (eski operasyon'un gözetim yarısı).
- **KİLİTLER & YAPILANDIRMA:** kilit paneli (pozitif çerçeve), bayraklar, ayarlar, tema/yoğunluk
  (eski ayarlar + operasyon'un müdahale kolları — müdahale ⌘K'da da yaşar).
- **Detay katmanı (istek-üzerine):** bir koşu / bir işlem / bir hipotez — alan sayfalarından bağla.
- landing/workflow/runbook bağımsız sayfalar olarak kalır. `brifing`/`adaylar`/`kararlar`
  içerikleri: kararlar→Portföy&Emirler(onay kuyruğu)+Gözetim; adaylar→Koşu&Döngü; brifing→Overview
  "dün gece" bloğunun kaynağı.
- Navigasyon: kalıcı SOL RAY (7 madde, ikon+etiket), Sessiz-Hat her sayfada sabit üstte;
  g-kısayolları+palet yeni haritaya güncellenir.

## "Ekrana dök" yasağı uygulaması
Her alan sayfası başındaki soru-cümlesi ARTIK SÖZLEŞMEDİR: sayfadaki her kart o soruya hizmet
etmeli; etmeyen kart taşınır/emekli edilir. Emekli edilen her görsel bileşen için: okuyucu-kaydı
kontrolü (codelaw) + karar notu (bu dosyanın Ek'ine işlenir).

## Uygulama planı (gece, kademeli — her adım ayrı commit + testli)
- **S2R-1:** kabuk — sol ray + 7-sayfa iskeleti + yönlendirme (eski görünümler geçici olarak yeni
  evlerine ALIAS'lanır; hiçbir içerik kaybolmaz) + Overview v1 (yukarıdaki kompozisyon, mevcut
  bileşenlerin ÖZETLENMİŞ kartları).
- **S2R-2:** içerik göçü — eski 12 görünümün kartları yeni evlerine taşınır; Öğrenme birleşimi;
  kart-başına "soruya hizmet" denetimi; emekli listesi.
- **S2R-3:** cila — yoğunluk/boşluk ritmi, kart hiyerarşisi, palet/g-kısayol/CSP/test güncellemesi;
  kontrast yeniden-doğrulama; ekran görüntüsüyle operatör onayına sunum.
Testler: mevcut kaynak-çiviler taşınan seçicilerle güncellenir; YASA-6 okuyucu haritası
test_edge_dashboard/test_pano_* ailesinde yeni IA'ya çekilir; her aşamada tam grep.

## Geri-dönüş
Her aşama ayrı commit; eski görünüm fonksiyonları S2R-2 sonuna dek silinmez (alias) — tek
`git revert` ile dönüş mümkün. Operatör sabah beğenmezse: revert maliyeti dakikalar.
