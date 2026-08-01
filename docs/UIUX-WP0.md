# UIUX-WP0 — Keşif Raporu (2026-08-01; onay bekliyor — onaysız kod değişmez)

> İş emri: `docs/UIUX-WORKORDER.md` (v5-uiux). ÖNEMLİ MUTABAKAT NOTU: iş emri resmîleşmeden ÖNCE,
> operatörün aynı-gün talimatlarıyla ("hepsini paralel uygula") v5'in bir kısmı FİİLEN indi ve
> canlıda (aşağıda "fiilî durum" sütunu). WP0 bu gerçeği saklamaz; kalan işi ona göre böler.

## 1) Stack envanteri (ölçüldü)

| Katman | Gerçek |
|---|---|
| Sunum | **Vanilla JS SPA-benzeri** — `meridian/web/app.js` (~5.200 satır), tek `index.html` (~1.100 satır, CSS satır-içi `<style>`), `theme.js` (gündüz/gece), `palette.js` (⌘K, 933 satır, CSS'i JS-enjekte) |
| Şablon/framework | YOK (React/Vue/şablon motoru yok); `RENDER.{12 görünüm}` el-yapımı görünüm kaydı; hash-tabanlı sayfa geçişi |
| Çizim | **Kütüphane YOK** — el-yapımı SVG: `_bellSVG` (dağılım), `_bullet` (Few bullet + sparkline); tablolar `.tbl`/`.trow` ızgara |
| Stil sistemi | **59 CSS custom-property** (de-facto token: `--bg/--tx/--s2..s6/--r-ctl|card|bar/--red|amber/--line…`), iki tema `data-theme` ile; DTCG `tokens.json` YOK |
| Servis | FastAPI `api.py` — statik dosyalar AD-AD rota (StaticFiles montajı bilinçli yok); auth `x-meridian-token`; CSP `script-src 'self'` (satır-içi işleyici yasak, test-çivili) |
| Gerçek-zaman | 15 sn `refreshStatus` poll + WS ayna (dolum akışı); nabız-bayat beyanı var |
| Test rejimi | Kaynak-çivili pytest (`test_pano_*`, `test_web_csp`, `test_edge_dashboard`) + `node --check`; YEREL SUNUCU YASAK (CLAUDE.md §5) — görsel doğrulama kanalı ekran görüntüsü/canlı-A1 |

**Strangler uygunluğu:** iş emrinin "yeniden yazım yasak, token+bileşen giydir" kuralı bu stack'le
birebir uyumlu — mevcut CSS-değişken katmanı DTCG'ye kaynaklık edebilir (S1-T1).

## 2) Ekran envanteri (koddan; görüntüler operatörden BEKLENİYOR)

12 görünüm (`RENDER.*`): bugun · kararlar(onaylar) · market · operasyon · intraday · ogrenme(ajan/
hermes/skiller/hafiza karması) · ayarlar · adaylar · brifing · performans + `landing` + `workflow`.
Her ekran için "cevapladığı soru" cümlesi hazırlandı — TEK KAYNAK: `app.js::EKRAN_SORUSU` (S1-T5 ile panoya işlendi; buradaki 4 örnek özet):
- **Bugün** — "Dün gece ne oldu, bugün ne silahlı, sermayem ne durumda?" (J1'in evi; sermaye-köken
  bloğu bugün eklendi)
- **Operasyon** — "Sistem sağlıklı mı; değilse NE ve NEREDE?" (Sessiz-Hat + alarm-bütçesi burada)
- **Intraday** — "Bugünkü akış/silahlanma canlı ne durumda?"
- **Öğrenme** — "Makine ne öğreniyor; gölge kollar/karne ne diyor?" (J3'ün evi — İŞ EMRİNİN
  6-alan hiyerarşisine göre EN KALABALIK ve bölünme adayı)
- (kalanı `app.js::EKRAN_SORUSU` — kopya liste bilinçli tutulmuyor, ayrışırdı)
**İSTEK (iş emri 13/2):** operatörden güncel ekran görüntüleri — özellikle Bugün, Operasyon,
Öğrenme, Market (gündüz+gece birer adet yeter).

## 3) Nielsen-10 masa-denetimi (kod-tabanlı; görsel teyit gereken satırlar işaretli)

| # | İlke | Durum | İhlal/borç (şiddet 1-4) | Ekran |
|---|---|---|---|---|
| 1 | Sistem durumu görünürlüğü | GÜÇLÜ | Sessiz-Hat + asof/nabız-bayat + WS göstergesi bugün canlıya çıktı | operasyon/tümü |
| 2 | Gerçek-dünya dili | GÜÇLÜ | Operatör-dili yerleşik ("onarım geçidi", "karne") | tümü |
| 3 | Kullanıcı kontrolü | İYİ | ⌘K + Esc + iki-adım onay; **dokunmatik palet girişi yok (2)** | palet |
| 4 | Tutarlılık | İYİ | İki sayı-grameri bugün tekleşti; **gündüz teması saf-beyaz (2)** — jeton yeniden-değerleme turu | tümü |
| 5 | Hata önleme | GÜÇLÜ | İki-adım onay + silahlama-durumu canlı-türetme (tahmin yok) | palet/operasyon |
| 6 | Hatırlama değil tanıma | İYİ | Palet kısayol-ipuçları; **`g d`-tarzı sayfa atlama + `?` haritası kısmi (2)** — 1-7 var, g-kısayolu yok | global |
| 7 | Esneklik/verim | GÜÇLÜ | ⌘K, 1-7, yoğun düzen | global |
| 8 | Estetik/minimalizm | **GÖRSEL TEYİT GEREK** | "Ekrana dök" riski en çok Öğrenme'de (3?) — ekran görüntüsüyle karara bağlanacak | ogrenme |
| 9 | Hatadan kurtulma | ZAYIF | **Runbook YÜZEYİ YOK (3)** — alarm satırı→runbook linki hedefsiz; palet 'runbook'u /workflow'a bağlamak zorunda kaldı | operasyon |
| 10 | Yardım/doküman | ZAYIF | `?` kısayol haritası paletten var ama runbook/teşhis rehberi eksik (2) | global |

## 4) En kritik 5 UX borcu (öncelik sırasıyla)

1. **Runbook yüzeyi yok (İ9, şiddet 3):** J2 (olay triyajı) zinciri "alarm→teşhis→runbook→çözüm"
   son halkasız. Alarm satırları + Sessiz-Hat sapmaları hedef gösteremiyor.
2. **DTCG tokens.json yok (Program V):** 59 CSS değişkeni tek-kaynak değil; lint ("token-dışı
   renk yasak") yalnız palette.js'te gelenek, sistemde kural değil.
3. **J1 60-sn turu ölçülmedi (Program IA):** Bugün ekranı J1'in evi ama "≤60 sn + kaydırmasız
   tek-ekran" hiç ölçülmedi; Öğrenme ekranı IA'nın 6-alan hiyerarşisine göre bölünmemiş.
4. **Kapsama ısı-matrisi + gölge küçük-katlar yok (Program D / eski P9):** 5 çekirdek grafikten
   ikisi eksik; kalan üçü (bullet, equity, şelale) bugünkü standarda çekildi.
5. **Gündüz teması + axe/odak-halkası denetimi (Program V/X):** gece teması saf-değersiz
   doğrulandı; gündüz `#ffffff` jeton-yeniden-değerleme turu bekliyor; axe hiç koşulmadı.

## 5) S1 bilet önerileri (fiilî-durum mutabakatlı)

**Fiilen S1-S4'ten BUGÜN İNENLER (yeniden yapılmayacak):** Sessiz-Hat v1 (S2) · alarm-bütçesi
KPI + flood-toplama temeli (S3) · ⌘K palet (S4) · tnum/sabit-ondalık + slashed-zero ölçülmüş-
gereksiz kararı (S1'in tipografi yarısı) · dürüstlük desenlerinin None/staleness/provenance üçlüsü
(S2) + sermaye-köken · gauge yasağı/bullet (D) · reduced-motion (R) · kontrast spot-raporu (V kısmi).

| Bilet | İş | DoD |
|---|---|---|
| S1-T1 | **DTCG tokens.json**: 59 değişkenden türet; iki tema token-katmanında; üretim CSS'i tokens.json'dan üretilir ya da eş-doğrulanır (lint testi: token-dışı hex yasak) | tokens.json + lint çivisi yeşil |
| S1-T2 | **Kontrast denetim RAPORU (tam)**: tüm metin/grafik çiftleri 4.5:1-3:1 tablosu, iki temada; gündüz-beyazı kararı için veri | docs/kontrast-denetimi.md |
| S1-T3 | **Runbook yüzeyi iskeleti** (borç#1'in S1'e çekilmesi — J2 zinciri kırık kalamaz): mevcut runbook içeriği nerede yaşıyorsa (ops/? docs/?) tek okunur sayfa + alarm-satırı bağları | alarm→runbook tıklanabilir |
| S1-T4 | **`g`-kısayolları + `?` haritası tamamlama** (İ6) | klavye tur notu |
| S1-T5 | **Ekran-başına "soru cümlesi"nin panoya işlenmesi** (başlık-altı tek sönük satır; "ekrana dök" denetiminin çıpası) | 12 ekranda satır + Ek-A güncel |

## 6) Onay istenen kararlar
1. Bu WP0 + S1 bilet seti onaylanıyor mu? (Onaysız kod yok — iş emri 13.)
2. Ekran görüntüleri: 4 ekran × 2 tema (İ8 kararı + görüntü envanteri için).
3. Borç#1 runbook: içerik kaynağı olarak ne kullanılsın? (Mevcut yazılı runbook YOK gibi görünüyor
   — ops/ betik başlıkları + MERIDIAN_ENGINEERING_LOG'dan türetme önerim var; onayla birlikte
   S1-T3 kapsamı netleşir.)
