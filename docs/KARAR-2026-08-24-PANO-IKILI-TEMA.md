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


---

## ⚠ ROL-1 DÜZELTMESİ (2026-08-24, operatör "font yasağımız yok" dedi → ölçüm yapıldı)

Bu belgenin İKİ İDDİASI YANLIŞTI. Kayda geçiyor (uydurma-yasağı: yanlış beyan silinmez, düzeltilir):

**① "Harici font CDN'i YASAK" → YARIM DOĞRU.** CSP `font-src 'self'` (deploy/Caddyfile:107)
gerçekten harici origin'i kapatıyor — ama bu bir yasak değil, **D4 sertleştirmesinin sonucu**
(2026-08-07: Google Fonts CDN kaldırıldı, iki üçüncü-taraf origin CSP'den DÜŞTÜ). Yani font
kullanımı serbesttir; şart **kendi-barındırma**. Satoshi/Inter istenirse woff2 olarak indirilip
`meridian/web/fonts/` altına konur, CSP değişmez. Operatör haklı.

**② "İkili tema KURULACAK" → ZATEN KURULU.** Ölçüm: `meridian/web/tokens.json` 68 jeton taşıyor;
23'ü temadan bağımsız, **45 renk jetonunun 45'i de `:root[data-theme="gece"]` bloğunda override
ediliyor** (index.html:113 ve :335) — yani İKİ TAM PALET var, `theme.js` ilk boyamadan önce
`data-theme` koyuyor. Karar "ikili tema kur" değil, **"var olan ikili temayı Dub değerlerine
göre yeniden ayarla"** olarak okunur.

**③ (bonus, benim çıkarımım da yanlıştı) VARSAYILAN TEMA KOYU DEĞİL.** Yerleşik dünya
2026-07-27 Omega dönüşümüyle **AÇIK zemine** geçmiş: `#ffffff` + sıcak kemik paneller
(`#f8f5f2`/`#f1ece8`) + sıcak hairline (`#e7e3df`), 12px kart yarıçapı, tam-pill kontroller,
**HİÇBİR YERDE GÖLGE YOK** — "ayrım hairline + ton". Koyu artık `gece` varyantı. Ben WP8-B'nin
dark-cockpit doktrin METNİNİ okuyup YAPILMIŞ ESERİ okumamıştım.

**SONUÇ — işin niteliği değişti:** Bu bir DÜNYA DEĞİŞTİRME değil, **AYNI DÜNYANIN daha iyi
icrası**. Yerleşik yön sözleşmesi (index.html DIRECTION CONTRACT) operatörün çıtasını zaten
"Linear · Vercel · Raycast" diye adlandırıyor — Dub'ın kendi DESIGN.md'si de "Similar Brands"
başlığında AYNI üçünü sayıyor. Yani referans, mevcut dünyanın daha rafine bir akrabası.
Asıl iş operatörün söylediği yerde: **bilgi mimarisi** (101 kart · tutarsız rozet dili ·
bağlamsız sayılar · öne çıkmayan aciliyet).


---

## ⚠ ROL-1 DÜZELTMESİ #2 (2026-08-24, envanter turu sonrası — ÜÇÜNCÜ hatam)

**"Varsayılan tema: KOYU (Rol-1 seçimi)" cümlesi YANLIŞTI ve bağlayıcı bir kararla ÇELİŞİYORDU.**
Envanter ölçtü (`DESIGN.md:552-555`, beyanlı sapma #3): brief karanlık-tek tuval varsayıyordu ama
**bağlayıcı operatör kararı (2026-07-31) İKİ ZEMİN + GÜNDÜZ VARSAYILAN**. "Koyu daha iyi okunur"
iddiası `deploy/HANDBOOK-PLAN.md:463-472`'de zaten ÇÜRÜTÜLMÜŞ. Yani:
- Kontrol-odası doktrini BENİMSENDİ, **koyu TUVAL benimsenmedi** — ikisi ayrı şeydi, ben
  birleştirmiştim.
- Operatörün 2026-08-24 "iki tema" seçimi yeni bir şey getirmiyor; **var olan bağlayıcı kararla
  BİREBİR AYNI** yerde duruyor. Varsayılan GÜNDÜZ kalır.

## DUB'DAN NE ALINIR — ENVANTERİN ÖLÇTÜĞÜ GERÇEK (kapsam beklediğimden DAR)
**Doğrudan alınabilir (3):** 12px kart yarıçapı (zaten aynı) · 4px boşluk tabanı (zaten aynı) ·
medium-500 başlık ağırlığı.
**ALINAMAZ, gerekçeleriyle (6):**
- **Elektrik-mavi aksan** → `v197` koşulsuz-emisyon tavanı **0**: dekoratif/marka rengi yapısal
  olarak imkânsız. Meridian'ın *Money Rule*'u: renk YALNIZ ölçüme aittir (yeşil/amber/kırmızı).
- **6 gölge kademesi** → `--elev: none`, "hiçbir yerde gölge yok" yasası.
- **9999px hap** → üç-yarıçap sözlüğü (Dub'ın pill mimarisi alınmaz).
- **Soğuk nötrler** → *Warm Rule* (Meridian sıcak kemik/hairline ailesinde).
- **16px gövde** → yoğunluk yasası.
- **Google Fonts** → `font-src 'self'` (self-host şartı; Recursive ölçümle seçilmiş).
**SONUÇ:** Dub bir GÖRÜNÜM kaynağı değil, bir DOĞRULAMA: aynı ailenin daha rafine üyesi olduğu
için Meridian'ın mevcut yasalarını (hairline-önceli elevasyon, gölgesizlik, kompakt yoğunluk)
DIŞARIDAN teyit ediyor. Redesign'ın değeri renkte değil **bilgi mimarisinde** — operatörün
söylediği yerde.

## REDESIGN ÖNCESİ KAPANMASI GEREKEN İKİ BORÇ (envanter buldu)
1. **`DESIGN.md` gündüz jeton tablosu BAYAT** (`:190-210`): `--bg` `#ffffff` yazıyor, gerçek
   `#fbf9f8`; 9 jeton ayrışmış. Çivi CSS↔`tokens.json`'ı denetliyor ama DESIGN.md'yi denetlemiyor →
   tasarımcı YANLIŞ tabandan türetir. **Redesign'dan ÖNCE tazelenmeli + çivi kapsamı genişletilmeli.**
2. **`app.js`'te 53 satır-içi DEĞER-jetonu, 0 ROL-jetonu** (`var(--sev-*)`=0). ROADMAP WP8-D bunu
   **33** diye kaydetmiş — sayım farkı çözülmedi (None+neden). Rol-jetonu katmanı olmadan iki temayı
   tutarlı yeniden ayarlamak imkânsız.
