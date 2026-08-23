# BAĞLAYICI OPERATÖR KARARI — Pano görsel dili: İKİLİ TEMA (2026-08-24)

**Karar mercii ve yetkisi:** Operatör (Erdem Ozturk), 2026-08-24. Operatör kendi ifadesiyle:
*"operatör benim ve benim dediğim bağlayıcı olur."* Bu belge o kararın kaydıdır.

## Karar
Pano görsel dili **Dub tasarım sistemi** referansıyla yenilenir (referans:
`https://styles.refero.design/style/b0d80806-b724-4ed1-a1d1-074edd3c9bc9`; ekler: `DESIGN.md`,
`tokens.json`, `variables.css`, `theme.css`). Uygulama biçimi: **İKİLİ TOKEN KATMANI** —
her token hem AÇIK (Dub'ın kendi değerleri) hem KOYU karşılığıyla tanımlanır; pano bir tema
anahtarı kazanır.

**Varsayılan tema: KOYU** (Rol-1 seçimi, operatör aksini söyleyene dek). Gerekçe: davranış-nötr
geçiş — canlı operatör yüzeyi bugünkü hâliyle açılır, açık tema opt-in gelir. Tek kelimeyle
çevrilir.

## Önceki doktrinle ilişkisi — GENİŞLETME, İPTAL DEĞİL
`docs/TASARIM-YONU-2026-08-07.md` (operatör onaylı, bağlayıcı) koyu temayı kontrol-odası kanıt
tabanına dayandırıyordu: HP-HMI/ISA-101, Airbus **dark-cockpit** ilkesi (karanlık = normal,
ışık = dikkat), EEMUA 191, Few/Tufte. Bu karar o gerekçeyi ÇÜRÜTMEZ; koyu temayı VARSAYILAN
olarak korur ve yanına ikinci bir tema koyar. **Şart (Rol-1, doktrinin korunması için):** açık
temada alarm/uyarı görünürlüğü YENİDEN TASARLANIR — ışık artık "normal" olduğu için dikkat
sinyali renk+kontrast+ikon üçlüsüyle taşınır; açık tema, alarm görünürlüğü kanıtlanmadan
varsayılan yapılamaz.

## Değişmezler (redesign bunları KIRAMAZ)
Dürüstlük-UI yasaları (None ≠ 0 · "ölçülemedi" ayrımı · provenance/kaynak rozetleri ·
nabız-bayat beyanı · sermaye-köken) · v196 çırçır tavanı · v197 koşulsuz-emisyon kapısı ·
v198 kart tabanı · v194/v205 yerleşim-taşma çivileri · CSP `script-src 'self'` (CDN ve inline
YOK — Dub'ın Inter/Satoshi/Geist Mono aileleri ancak yerel gömülü ya da sistem-yığını
karşılıklarıyla; harici font CDN'i YASAK) · tabular-nums disiplini.

## Yürütme yolu
1. Envanter (uçuşta): `docs/ENVANTER-PANO-YUZEYLERI-2026-08-24.md` — yüzeyler, değişmezler,
   Dub-eşleme taslağı, risk listesi.
2. **Claude Design projesi:** "Meridian Pano — Design System" (`86d04f07-1340-4c31-ba85-fca3cc02bc99`)
   — bileşen kütüphanesi ikili token'larla orada kurulur ve önizlenir (canlı pano DEĞİŞMEZ).
3. Onaydan sonra `app.js`/CSS'e uygulama: bileşen bileşen, çivi-önce (her aile için görsel
   çivi + değişmez çivisi yeşil kalacak).
