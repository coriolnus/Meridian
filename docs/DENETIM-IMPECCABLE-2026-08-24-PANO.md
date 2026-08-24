# IMPECCABLE DENETİMİ — `meridian/web/index.html` (2026-08-24, Dub dönüşümü sonrası)

_Mod: **Operate** (PRODUCT.md: tek operatör, kontrol paneli — pazarlama değil)._
_Yöntem: dedektör + tarayıcıda ÖLÇÜM (1180×1500 masaüstü ve 375×812 mobil), gerçek canlı
fikstürle. İddia edilen her bulgu ölçüldü; **üçü yanlış pozitif çıktı ve öyle kaydedildi**._

## SAĞLIK TABLOSU

| # | Boyut | Skor | Kilit bulgu |
|---|---|---:|---|
| 1 | Erişilebilirlik | **3/4** | Odak halkası, etiketler, yer imleri, başlık sırası temiz; hedef boyu 23px'ti → düzeltildi |
| 2 | Performans | **4/4** | 656 düğüm · `will-change` 0 · 17 SVG · yerleşim çırpınması yok |
| 3 | Duyarlılık | **3/4** | 375px'te sayfa yatay KAYMIYOR; dört öğe kabında kırpılıyordu → düzeltildi |
| 4 | Tema | **4/4** | Tam jeton sistemi, iki eksiksiz palet, bileşen CSS'inde 0 ham renk, testle eş-doğrulanıyor |
| 5 | Uygulama bütünlüğü | **4/4** | Ürüne özgü, tutarlı; dedektörün iki bulgusundan biri beyanlı yanlış pozitif, biri kısmen gerçek |
| | **Toplam** | **18/20** | **Excellent — küçük cila** |

## UYGULAMA BÜTÜNLÜĞÜ HÜKMÜ: **GEÇTİ**
Yüzey ürüne özgü bir sistem konuşuyor: iki-tema jeton sözleşmesi, altı adlandırılmış rol
(yapı · şiddet · yön · mod · veri ölçekleri · gezinme), "ölçülemedi" atomu, payda beyanları,
kart-önce damgası. Hiçbiri jenerik bir şablondan gelmiyor ve hiçbiri dekoratif değil —
her biri bir yasanın (UYDURMA YASAĞI, YASA 6, rol ayrılığı) görünür karşılığı.

## DÜZELTİLEN İKİ KALEM
| # | Bulgu | Ölçüm | Düzeltme |
|---|---|---|---|
| F1 | `.pv-mbtn` hedef boyu | **23px** (WCAG 2.2 AA 2.5.8 eşiği 24×24) | `min-height:24px` — dolgu değil, dolgu satır ritmini bozardı |
| F2 | Dar ekranda ölçü kırpılması | 375px'te `.ab-olcu` sağ kenarı **731px** | Ölçüler esnek kapta akar; `nowrap` KALDI (ölçü ortadan kırılmasın), ≤980px'te akış açıldı. Bir alarm ölçüsünü kırpmak YASA 6'nın yazdırdığı sayıyı görünmez kılardı |

## ÜÇ YANLIŞ POZİTİF — ölçülerek elendi, kayda geçiyor
1. **"İki `<input>` etiketsiz"** → YANLIŞ. İkisi de `labels: 1` ("Parola" / "Parolayı tekrar"),
   `for=` ile bağlı. İlk taramam `e.labels`'ı yanlış değerlendirdi.
2. **"İki `<h1>`"** → YANLIŞ. İkincisi giriş kapısında ve kapsayıcı `hidden` + `display:none`,
   yani erişilebilirlik ağacında değil.
3. **"HALT düğmesi mobilde 0×0, erişilemez"** → YANLIŞ ve en önemlisi bu. Seçicim önce gizli bir
   `<option>` yakalamış. Gerçek düğme (`BUTTON.halt`) **53×44, sağ kenar 359/375 — görünür ve
   dokunulabilir**. PRODUCT.md operatörün telefonda acil durdurma tuttuğunu söylüyor; bunu
   doğrulamadan raporlamak yanlış bir güvensizlik yaratırdı.

## DEDEKTÖRÜN İKİ BULGUSU
**`overused-font: Inter` → BEYANLI YANLIŞ POZİTİF.** Skill'in kendi kuralı: _"The brief wins.
Honor pinned aesthetics… even when they conflict with a saturated-pattern warning."_ Inter
operatörün pinlediği Dub sisteminden geliyor **ve ölçümle kazandı**: `1`/`l` @28px 0,968 vs
Recursive Sans 0,931 · `0`/`O` 0,774 vs 0,663 (`docs/HUKUM-2026-08-24-YAZITIPI.md`). Bir alım-satım
panosunda rakam okunaklılığı, yüzün yaygınlığından önce gelir.

**`flat-type-hierarchy` (10/11/12px) → KISMEN GERÇEK, açık kalem.** Ölçtüm:
- **33 kural** 10/12px'i `var(--mono)` ile kullanıyor → meşru. Bu, PRODUCT.md'nin adıyla andığı
  **imza etiket idiomu** (mono, BÜYÜK HARF, `0.16em` aralık). Sans rampasıyla yarışan bir basamak
  değil, ayrı bir *register*. `.gate-l` yorumu (v195-a) bu ayrımı zaten gerekçelendirmiş: bir
  parola etiketi okunmak zorunda olduğu için idiomdan çıkarılıp 11px'e taşınmış.
- **26 kural** 10/12px'i SANS ile kullanıyor → savunma bunları KAPSAMIYOR. Sans rampasının
  başlık basamağı 11px (`--t-cap`); yanında 10 ve 12 durunca üç boy 1,2 kat içinde sıkışıyor.
- **3 kural** 11px'i mono ile kullanıyor → bandı bulandırıyor.

**Bu turda düzeltilmedi ve nedeni:** 29 kuralın boyunu değiştirmek dağıtımdan hemen önce
yapılacak bir iş değil; v209 rampa çivisi ve dört yüzeyin `:root` birebirliği birlikte
doğrulanmalı. Kalem `docs/`e açık yazıldı, tur kapanışında ya da sabah operatör onayıyla
işlenir. **Sessiz bırakılmadı.**

## AÇIK KALAN — PRODUCT.md DRIFT (bu turda DÜZELTİLMEDİ, bilinçli)
PRODUCT.md'nin "Brand Commitments" bloğu hâlâ **Omega** dünyasını ve **Geist**'i "incumbent"
diye anlatıyor; ölçülen değerler `omega.nextjsshop-preview.workers.dev`'den alınmış. Bu gece
dünya **Dub**'a, yüz **Inter + Recursive Mono**'ya geçti (`KARAR-2026-08-24-B`,
`HUKUM-2026-08-24-YAZITIPI`). Skill'in kuralı: _"Never repair drift as a side effect of a
design task."_ Bu yüzden dokunulmadı — ama bir sonraki tasarım turu bu bloğu okursa **yanlış
dünyaya** çalışır. Operatör onayıyla güncellenmeli.
