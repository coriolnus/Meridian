> **⚠ GEÇERSİZ — 2026-08-06 akşamı operatör kararıyla ASKIYA ALINDI.** v195 serisi durduruldu ve
> yeniden-tasarım programı baştan başladı; ayrıca manda genişledi: "hiçbir UI öğesi muaf değil"
> + "neyi nerede ve hangi biçimde gösterdiğin de değişebilir". Bu brief'in 5'li gruplaması artık
> BAĞLAYICI DEĞİL — yeni bilgi mimarisi işe-göre envanterden (docs/BASELINE-2026-08-06.md)
> türetilecek. Belge TARİHSEL KAYIT olarak duruyor: ölçülmüş adım-sayımları (② 8 tık→6, ③ 6 tık→2),
> geri-uyum kısıtı (ROUTE_ALIAS) ve 23-test/6-dosya maliyeti hâlâ geçerli GİRDİLERDİR.

# BRIEF — v195-c · Sayfa birleşmesi 7 → 5 (+ bağlı davranış kalemleri)

**Durum:** operatör onayı alındı (2026-08-06, üç-soruluk shape turu) · **uygulama henüz YOK**
**Kaynak denetim:** `docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md` (§7 + Ö2/Ö11/Ö16)
**Ön koşul:** v195-b (kart sözleşmesi / collapse) CANLIDA olmadan başlamaz — sırası kasıtlı.

---

## 1. İş ve kitle

Tek operatör (ürün sahibi), günde birkaç kısa bakış, masaüstü, Türkçe arayüz.
Ziyaretçi modu: **Operate** — taranabilirlik, tutarlılık ve gerçek kullanım sahnesi ifadenin
önünde. Bu bir yeni görsel dünya işi değil; Omega/iki-zemin dünyası aynen korunur.

Kanonik üç görev (PRODUCT.md'de kayıtlı):
① 10 saniyelik sağlık/dün-gece kontrolü · ② REVIEW planını onayla → arm et → aynaya
gittiğini gör · ③ alarm/ihlal triyajı.

## 2. Sonuç ve kanıt

Görev ①: tek yüzeyde biter, sayfa değiştirmeden.
Görev ②: ölçülen **8 tık + 7 kaydırma + 3 sayfa** → **6 tık + 0 kaydırma + 0 sayfa**.
Görev ③: ölçülen **6 tık + 3 sayfa + 1 harici belge** → **2 tık + 1 sayfa**.
Kanıt kaynağı: denetimin adım-adım yürüyüşü (kod üzerinden sayıldı, tahmin değil).

## 3. Seçilen yön — yapısal tez

**Sayfalar içerik türüne göre değil GÖREVE göre gruplanır.** Beş sayfa:

| # | Sayfa | Birleşen | Bölümler | Görev |
|---|---|---|---|---|
| ① | Genel Bakış | (değişmez kap) | + **triyaj şeridi** | ① |
| ② | **Karar & Emir** | `kosu` + `portfoy` | `adaylar` · `onaylar` · `brifing` · `mutabakat` · `intraemir` (+ detay: `kapilar`, `performans`) | ② |
| ③ | **Gözetim & Veri** | `gozetim` + `veri` | `operasyon` · `veriboru` · `market` · `intraday` | ③ |
| ④ | Öğrenme | (değişmez) | 7 bölüm, 5'i varsayılan-kapalı (v195-b'den gelir) | haftalık |
| ⑤ | Kilitler & Yapılandırma | (değişmez) | `mudahale` · `ayarlar` | müdahale |

**Etkileşim tezi — Genel Bakış eylem yüzeyi olur (ADR S2R-4 revizyonu):** 12-durumlu triyaj
şeridi Portföy'den Genel Bakış'a taşınır; çip **sayfa değiştirmez, çekmece açar**. "Başka hiçbir
şey" kuralı yalnız bu şerit lehine gevşer — Genel Bakış hâlâ kart-dökümü değil.

**Odak an:** sabah panoyu açtığında ilk viewport "senden şu bekleniyor"u söyler ve o işi
*yerinde* yaptırır; ikinci bir yüzeye gitmek gerekmez.

## 4. Kapsam ve sınırlar

**Dahil (operatör onayı: gruplama + davranış kalemleri):**
- Sayfa/bölüm taşıma: `VIEWS` · `ALAN_BOLUMLERI` · `EKRAN_SORUSU` (27→25) · `ROUTE_ALIAS`
  (12→14) · `DURUM_SAYFALARI` (2→1) · `RAIL_ICON`; `index.html` `.page` kapları 7→5;
  `palette.js` `SAYFA_ADI`/`BOLUMLER`.
- **Ö16** kaydırma-konumu hafızası (`sessionStorage`, sayfa başına; `go()` yalnız YENİ sayfada 0'a döner).
- **Ö11** bütünlük ihlalleri gelen-kutusuna alarm satırı olarak düşer (kart Veri'de kalır, satır Gözetim'de doğar).
- **Ö2** "aynaya gönder" onay çekmecesinin içine ikinci iki-adımlı düğme olarak taşınır (uç aynı, ikinci emir-yolu YOK).
- ADR revizyonu `docs/UIUX-S2R-REDESIGN.md` (S2R-4) + 23 test fonksiyonu / 6 dosya güncellemesi.

**Dokunulmaz:** Omega iki-zemin dünyası ve jeton sözlüğü · `.pm-*` hücre dili (üçüncü dil
doğmaz) · ⌘K paleti sözleşmesi · karne matrisi · onay yasası (`girise_uygun` tek koşul noktası,
NO_GO onaylanamaz) · dürüstlük yasaları (ÖLÇÜLEMEDİ≠0, paydasız çubuk çizilmez, renk yalnız
anomalide, EEMUA bütçesi) · CSP-self · Geist · yoğun-uzman düzeni.

**Karşı-hedefler:** sayfa sayısını düşürmek için kart silmek · Genel Bakış'ı kart dökümüne
çevirmek · accordion (bağımsız collapse korunur) · numaralı "Bölüm N" başlıklarını taşımak
(B22: numara artık yalan bir sıra vaat ediyor — birleşmede düşer).

## 5. Durumlar ve aralıklar

| Durum | Davranış |
|---|---|
| Boş — bugün döngü yok | "Son döngü: …" yaşıyla + nedeni; sıfır **uydurulmaz** |
| Boş — onay bekleyen yok | Şerit "bekleyen yok" der ve **çip üretmez** (sahte iş yaratmaz) |
| Yüklenme | Mevcut iskelet yok; bölüm gelene dek yer tutar, düzen zıplamaz |
| Hata — bölüm | Mevcut `BÖLÜM YÜKLENEMEDİ` çerçevesi |
| Hata — satır | v194 `satirKoru`: bozuk satır dürüst satıra döner, bölüm ayakta kalır |
| HALT | Müdahale durumu ①'de görünür; ⑤ dışında hiçbir yerden tetiklenemez |
| Taşma | ④ 39 kart (5 bölüm kapalı) · ③ ~12 bütünlük jetonu · alarm hedefi ≤10/gün |

Gerçekçi aralıklar: aday 0-10 · plan 0-6 · silahlı 0-5 (tavan `max_open_positions`) ·
açık pozisyon 0-5 · ihlal jetonu ~12 · Öğrenme 39 kart.

## 6. Etkileşim ve yerleşim

- **Topoloji:** 5 sayfa · sayfa → bölüm → kart → çekmece. Derinlik bir kademe azalır
  (bugünkü en derin yol: sayfa → bölüm → kart → alt-başlık → tablo satırı).
- **Gezinme:** ray ikonları 5'e iner; ⌘K bölüm-adreslerini aynen çözer.
- **Geri uyum ZORUNLU:** eski `kosu#…` / `portfoy#…` / `gozetim#…` / `veri#…` adresleri
  `ROUTE_ALIAS` ile yeni sayfalara çözülmeye devam eder (RUNBOOK bağları ve çekmece çipleri
  bu adresleri taşıyor) — kırık bağ bırakılmaz.
- **Geri bildirim:** çip → çekmece açılışı kaydırma konumunu bozmaz; onay sonrası gönderim
  aynı çekmecede sonuçlanır (Ö2), mesaj çekmece kapanınca kaybolmaz (B5 dersi).
- **Erişilebilirlik:** kart/çip `<button>`, Tab+Enter, `aria-modal` çekmece, odak tuzağı ve
  odağın karta dönüşü korunur; `prefers-reduced-motion`.

## 7. Kısıtlar ve açık kararlar

- **Sıra kilidi:** v195-b (kart sözleşmesi) canlıya inmeden başlamaz — sözleşmesiz birleşme
  ②'yi 21 kartlık tek sütuna çevirir (denetimin açık uyarısı).
- **Tek otoriter suite + tek dagit** Rol-1'de; ajan kapsam testi koşar.
- **Test maliyeti ölçülü:** 23 test fonksiyonu / 6 dosya (`s2r2_goc` 8 · `s2r1_kabuk` 5 ·
  `uiux_s1b` 5 · `s2r3_cila` 2 · `market` 2 + ADR eşitlik çivisi). Bu testler sayfa yapısını
  yasaklamıyor; iki listenin sessizce ayrışmasını yasaklıyor — **çiviler zayıflatılmaz,
  yeni gerçekle güncellenir.**
- **Uygulayıcının icat etmeyeceği kararlar:** hangi bölüm hangi sayfada (yukarıdaki tablo
  bağlayıcı) · Genel Bakış'ın kart dökümü olmaması · ikinci emir-yolu açılmaması ·
  "Bölüm N" numaralarının düşmesi.
- **Açık:** ④ Öğrenme'nin kart bütçesi yazılmadı (bugün yok). v195-b sözleşmesi bütçeyi
  getirirse burada da uygulanır; getirmezse ayrı kalem.
