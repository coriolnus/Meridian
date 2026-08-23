# ENVANTER — Pano görsel yüzeyleri (2026-08-24)

**Statü:** SALT-OKUMA envanter · hüküm YOK, karar operatörde.
**Sipariş:** operatör panonun görsel dilini yenilemek istiyor (referans: **Dub** tasarım sistemi —
açık kanvas, hairline border, Inter/Satoshi, tek elektrik-mavi aksan). Bu belge, hangi yol
seçilirse seçilsin gereken HARİTAdır.
**Kapsam:** `meridian/web/app.js` (11.109 satır) · `meridian/web/index.html` (1.896 satır; CSS
`:80–1718` arası tek `<style>` bloğu) · `meridian/web/palette.js` (1.048 satır, kendi CSS'ini
enjekte eder) · `meridian/web/theme.js` · `DESIGN.md` · `docs/TASARIM-YONU-2026-08-07.md`.
**Dokunulmadı:** app.js (başka ajan uçuşta — YALNIZ okundu), hiçbir kaynak dosya değiştirilmedi,
git koşulmadı, sunucu açılmadı.

---

## ÖZET — beş cümlede harita

1. **Pano bir tasarım sistemi DEĞİL, ölçülmüş bir sözleşme.** İki katmanlı jeton (DEĞER + ROL),
   üç yarıçap, sıfır gölge, dokuz tipografi basamağı, beş renk rolü — hepsi kaynakta gerekçeli
   ve **52 test dosyası app.js/index.html'i STRING olarak tarıyor** (§2.10).
2. **Dub ile en güçlü örtüşme "border-first elevation"**: Dub'ın 1942 kez kullandığı 1px hairline
   felsefesi Meridian'da zaten daha katı bir yasa (`--elev:none`, her iki temada). **En sert çatışma
   ise elektrik-mavi aksan**: v197 kapısı "koşulsuz emisyon = 0" diyor, yani dekoratif/etkileşim
   rengi yapısal olarak imkânsız (§2.3/E1, §4.3).
3. **Koyu tema doktrini benimsendi, koyu TUVAL benimsenmedi.** ISA-101/EEMUA-191/Airbus dark-cockpit
   kanıt tabanı WP8-B'nin kabul çıtası; ama "brief karanlık-tek tuval varsayıyor, **bağlayıcı karar
   (2026-07-31, operatör) iki zemin + gündüz varsayılan**" (`DESIGN.md:552-555`) — beyanlı sapma #3 (§3.2).
4. **Redesign'ın üç ağır kilidi:** ızgara mimarisi terk edilemez (≥100 `grid-template-columns`,
   ≥300 sabit px — §5/R1) · ellipsis/nowrap hiçbir yerde yasak (§5/R4) · kart sayısı ratchet
   (101 ölçülen / 25 kapaklı — §5/R3).
5. **İki açık borç bulundu:** `DESIGN.md`'nin gündüz jeton tablosu P9 öncesi değerleri taşıyor
   (§3.6) ve app.js'in 53 satır-içi DEĞER-jetonu rol katmanının dışında kalıyor (ROADMAP bunu
   WP8-D olarak kaydetmiş, orada sayı 33 — §5/R2).

---

## Ölçüm künyesi (yöntem — sayıların nereden geldiği)

| Sayı | Nasıl ölçüldü | Bilinen sınır |
|---|---|---|
| CSS sınıf evreni = **259** | `awk 'NR>=420&&NR<=1718' index.html \| grep -oE '^[^{}/ ][^{}]*\{' \| grep -oE '\.[a-zA-Z][a-zA-Z0-9_-]*' \| sort -u` | Yalnız satır başındaki seçiciler; medya sorgusu içindeki girintili kurallar EKSİK sayılır (alt sınır) |
| app.js `class="…"` emisyonu = **2.322** | `grep -oE 'class="[^"]*"' app.js \| wc -l` | Şablon içi `${…}` ile üretilen sınıflar tek emisyon sayılır |
| app.js satır içi `style="…"` = **605** | `grep -oE 'style="[^"]*"'` | Aynı |
| `grid-template-columns` satır içi = **114** | `grep -oE 'grid-template-columns:[^";]*'` | Aynı |
| app.js içinde **hex renk = 0** | `grep -oE '#[0-9a-fA-F]{6}\b' app.js` | Jeton sözleşmesi TUTUYOR — app.js hiç renk DEĞERİ taşımıyor |
| v198 kayıtlı katlanır kart = **36** | `grep -oE 'katKart\("[^"]+"' \| sort -u \| wc -l` | `KART_KAYDI` defterinden bağımsız doğrulama |

---

# [1] YÜZEY ENVANTERİ

## 1.0 Sayfa / sekme iskeleti

| Yapı | Kaynak | Bugünkü hâli |
|---|---|---|
| **Beş yüzey** (`page-bugun`, `page-karar`, `page-saglik`, `page-ogrenme`, `page-kilitler`) | `index.html:1800,1804,1831,1854,1870` · yönlendirme `app.js:614 go(id)` | `<section class="page">`, tek `.active` görünür; `TASARIM-YONU §3`'ün beş yüzeyi birebir uygulanmış |
| **21 bölüm** (`.alan-bolum`) | `index.html` 21 örnek (`grep -c 'class="alan-bolum"'`) · defter `app.js:1631 ALAN_BOLUMLERI` | Bölüm başlıkları `alanSayfasi()` `app.js:1529` ile üretilir |
| **26 soru cümlesi** (5 yüzey + 21 bölüm) | `app.js:115 soruCumlesi(id)` · `app.js:55 ALAN_ADI` | Her ekran tek cümlelik soru taşır; ilk iki kelime "mertebe"yi söyler ve testte çivili (`app.js:65-75` yorum) |
| **Kabuk** `.shell` = kenar şeridi + ana | `index.html:563-564` · dar ekran `:1679` (tek kolon) | `max-width:1320px`, ızgara **`208px 1fr`**, `gap:32px`, üst dolgu `calc(var(--navh,76px) + 17px)`. Sabit `nav` + sticky `.side` (`:573`, `top:78px`). Ray 2026-07-28'de operatör kararıyla kalıcı genişledi — bedeli: içerik kolonu 152px daraldı (`:568-572`) |
| **Sayfa görünürlüğü** | `index.html:637` | `.page{display:none} .page.active{display:block}` — tek satırlık kural |
| **Yatay taşma** | `index.html:407` | `html{overflow-x:clip}` — `hidden` DEĞİL, bilerek: `hidden` bir kaydırma bağlamı yaratır ve `.side`'ın `position:sticky`'sini öldürürdü (`:403-406`) |
| **Üst bar** `nav` | `index.html:510-512` | `position:fixed`, `--nav-bg` (%82 opak, temayla döner), `backdrop-filter:blur(8px)`, `box-shadow:0 3px 0 -2px var(--line)` — **blur'suz, negatif yayılım: bu bir GÖLGE değil ikinci saç teli** (DESIGN.md:900) |
| **Mod bandı** `body[data-mod]::before` | `index.html:1454-1462` · `<body data-mod="olculemedi">` `index.html:1720` | Sayfanın ÜST KENARINDA 3px tam-genişlik bant; `live` tam opak kroma, `paper` akromatik %65, `olculemedi` KESİK desen. Köşe rozeti DEĞİL — **yapısal taşıyıcı** |

## 1.1 Jeton katmanı (tüm bileşenlerin okuduğu tek kaynak)

İki katmanlı: **DEĞER** jetonları (bir hue'nun adı) ve **ROL** jetonları (bir işin adı).
Sözleşme: *"BİLEŞEN KURALLARI YALNIZ ROL JETONU OKUR"* — `index.html:170`.
Gündüz bloğu `:root{` `index.html:113-291` · gece bloğu `:root[data-theme="gece"]{` `index.html:335-400`.

| Jeton ailesi | Tanım (gündüz / gece) | Gündüz | Gece | Not |
|---|---|---|---|---|
| Yüzey rampası `--bg/--bg2/--card/--card-2/--raise` | `index.html:133` / `:336` | `#fbf9f8 / #f5f4f2 / #f2efed / #ece7e3 / #fbf9f8` | `#1c1a18 / #232120 / #262320 / #2f2b27 / #38342f` | Dört adımlı SICAK rampa; saf beyaz ve saf siyah YOK (P9 turu, katsayı 0,9523 — `index.html:124-132`) |
| Saç telleri `--line/--line-2` | `index.html:136` / `:338` | `#e2deda / #d4cfca` | `#38342f / #4a453f` | Sıcak gri, nötr değil (*Warm Rule*, `DESIGN.md:418`) |
| Mürekkep `--tx/--tx2/--tx3` | `index.html:141` / `:339` | `#050505 / #585450 / #686562` | `#d4d0cb / #b0a9a0 / #95928f` | `--tx3` kart üstünde 5,06:1; `--tx2`den adım 1,30 (B1 düzeltmesi, `:137-140`) |
| Aksan `--accent/--accent-2/--accent-tint` | `index.html:145` / `:340` | `#050505 / #050505 / #eeeeee` | `#d4d0cb / #e8e4df / #302c28` | **ETKİLEŞİM RENGİ YOK** — birincil eylem siyah haptır, kroma taşımaz (`:142-144`) |
| Para renkleri `--green/--amber/--red` (+`-t`/`-h`) | `index.html:153,163,269-270` / `:344,346,364-365` | `#0c6a3b / #6e4a00 / #b3242c` | `#4cc38a / #e0a82e / #f58b8f` | Her biri **kendi %10 tinti üzerinde** ölçüldü; gündüz 4,72/5,57/4,59 · gece 5,31/5,39/5,01 |
| Seri merdiveni `--violet/--violet2/--blue` | `index.html:162` / `:345` | `#3e3c39 / #050505 / #050505` | `#b1afad / #d4d0cb / #d4d0cb` | Ad TARİHSEL (eski indigo dünyası) ve değişmez; **hue eklenmedi** — ayrım kesik-çizgi deseninden |
| ROL 2 ŞİDDET `--sev-1/2/3(+t/h)` | `index.html:212-215` / `:383-386` | `--red/--amber/--green` devralır | aynı adlar | Kroma en yüksek burada; başka hiçbir anlam bu kanalı kullanamaz (`:172-177`) |
| ROL 3 YÖN `--yon-arti/--yon-eksi` | `index.html:219-220` / `:390-391` | `#40654c / #784e4b` (C≈0,059) | `#8ab59c / #d1a0a0` (C≈0,058) | Kroma ŞİDDETİN ALTINDA, ölçülmüş kısıt: gündüz 0,059<0,0917 · gece 0,059<0,1289 (`:179-188`) |
| ROL 4 MOD `--mod-kagit/-canli/-kesif` | `index.html:228` / `:396` | `--tx2 / #723a96 / #635071` | `--tx2 / #c598e7 / #b9a4ca` | **Hue 310° kalıcı olarak bu kanala ayrıldı**; kâğıt AKROMATİK (`:190-199`) |
| ROL 5 · veri güveni `--olcek-guven(+t/h)` | `index.html:239` / `:399` | `--tx2`, halka `rgba(5,5,5,.45)` | `--tx2`, halka `rgba(212,208,203,.45)` | Halka alfası ölçülmüş: .30→2,03/2,12 KALDI · .45→3,12/3,03 GEÇTİ (`:233-238`) |
| ROL 5 · kapsama rampası `--kap-1..4` | `index.html:253-254` / `:352-353` | ink-alfa .06/.14/.23/.30 | aynı alfa merdiveni | Tavan alfa .30 SABİT (`--tx` en koyu bantta 4,68:1; .34'te 4,45'e düşer) |
| ROL 5 · sapma `--dv-n2..--dv-p2` | `index.html:261-262` / `:356-357` | mavi `rgba(46,82,122,…)` ↔ toprak `rgba(134,106,46,…)` | mavi `rgba(138,168,200,…)` ↔ toprak `rgba(198,176,122,…)` | **CVD-güvenli diverging**: protan/deutan kırmızı-yeşili siler, mavi-sarıyı korur (`:255-260`) |
| Bant merdiveni `--band-2` | `index.html:245` / `:349` | `#979491` | `#676665` | Bullet grafiğin orta niteliksel bandı; adımlar 2,45–2,49 |
| Geometri `--r-card/--r-ctl/--r-bar` | `index.html:274` (tek blok, iki temada aynı) | `12px / 10px / 2px` | aynı | **TAM ÜÇ YARIÇAP.** `--r-pill` KALDIRILDI 2026-07-27 — tanımlıydı, hiçbir kural kullanmıyordu (`:275-276`) |
| Yükseklik `--elev` | `index.html:279` | `none` | `none` | **Her iki temada da `none`** — "Referansta ölçüldü: her kartta `box-shadow:none`" (`:277-278`) |
| Tipografi `--sans/--mono/--display/--serif` | `index.html:114-117`; `@font-face` `:103,108` | Recursive Sans / Recursive Mono (kendi-barındırma, SIL OFL 1.1) | aynı | `--display` ve `--serif` `--sans`'ın takma adı: **tek aile + mono kardeşi** |
| Etiket imzası `--label-size/--label-track` | `index.html:281` | `10px / .16em` | aynı | Omega imza mikro-başlığı: mono, BÜYÜK HARF |
| Hareket `--ease/--t/--t-rise` | `index.html:282` | `cubic-bezier(.16,1,.3,1)` / `.15s` / `.34s` | aynı | `--t` v198'in ≤200ms tavanını karşılıyor (§2.4/K8) |
| Genişlik `--max` | `index.html:283` | `1180px` | aynı | ⚠ **PANODA ÖLÜ JETON**: `grep -rn "var(--max)" meridian/web/` = yalnız `landing.html:284,295` ve `runbook.html:202`. `index.html` onu **hiç kullanmıyor** — panonun gerçek genişliği `.shell{max-width:1320px}` (`index.html:563`). Jeton yalnız **jeton-birliği testi** (§2.6/P5) yüzünden duruyor; `--r-pill`in silinme gerekçesinin (`:275-276`) aynısı burada geçerli ama silinmemiş |
| Boşluk `--s1..--s12` | `index.html:119` | 4/8/12/16/20/24/32/40/48px | aynı | Tek 4px tabanı |
| Perde/halka `--scrim/--ink-h/--ink-h-soft` | `index.html:271-272` / `:363,372` | `rgba(5,5,5,.42)` · `.30` · `.18` | `rgba(10,9,8,.66)` · `.30` · `.18` | Gece perdesi ölçüldü: saf siyahla bile tavan 1,34 → ayrım blur + saç teliyle (`:366-371`) |
| Üst bar `--nav-bg` | `index.html:268` / `:361` | `rgba(251,249,248,.82)` | `rgba(28,26,24,.82)` | Beyaz kalsaydı HALT/KRİZ kırmızısı görünmezdi — 1,27:1 arızasının aynadaki hâli |
| Alan kenarı `--field` | `index.html:290` / `:374` | `#86817d` (3,14) | `#7e776e` (3,18) | WCAG 2.2 1.4.11 için AYRI jeton — form kontrolleri `--line-2`yi kullanamaz (`:284-289`) |
| `color-scheme` | `index.html:291` / `:400` | `light` | `dark` | — |

**Ölçülen jeton disiplini (redesign için kritik):**

| Ölçüm | app.js | index.html |
|---|---|---|
| `var(--sev-1/2/3)` | **0** | 27 / 21 / 12 |
| `var(--yon-arti/--yon-eksi)` | **0** | 3 / 3 |
| `var(--mod-*)` | **0** | 10 |
| `var(--olcek-guven)` | **0** | 4 |
| `var(--green/--red/--amber)` (DEĞER jetonu) | **19 / 22 / 12 = 53** | 2 / 3 / 2 |

→ **ROL katmanı yalnız CSS'te (index.html) yaşıyor. app.js'in 605 satır-içi stili ve tüm SVG
grafikleri DEĞER jetonu okuyor** (`app.js:533, 1444, 2679, 2703, 2723, 3678, 3716, 3731, 3734,
3999, 4025, 4885-4886, 8548-8550, 8616-8617, 8645, 8771, 8780, 8787, 9344, 9367-9368, 9511,
9543, 9738`). Bu bir uydurma değil ölçüm: `grep -oE "var\(--sev-1\)" app.js` = 0.

## 1.2 Kart aileleri (dört ayrı kart dili — bugün TEK değil)

| Aile | Üreten fonksiyon (dosya:satır) | CSS | Bugünkü görsel tanım | Varyant | Veri |
|---|---|---|---|---|---|
| **Genel kart** `.card` | serbest şablon; 107 emisyon (`grep -c class="card"`) | `index.html:1116` | `background:var(--card)` · `1px solid var(--line-2)` · `border-radius:12px` · `padding:24px` · gölge YOK | `.card + .card{margin-top:16px}` `:1132`; `.detay-kat .dk-govde > .card` kartlığını KAYBEDER (`:712`) | her yerde |
| **Katlanır kart** `.kat-kart` (v198) | `katKart()` `app.js:2136` · `kartOzeti()` `app.js:2142` · kurucu `katKurulumu()` `app.js:2196` · defter `KART_KAYDI` `app.js:2038` | `index.html:731-765` (`.kk-dugme/.kk-ad/.kk-ok/.kk-ozet/.kk-govde/.kk-kontrol/.kk-hepsi/.kk-butce`) | Başlık bir `<button>`, ok `▸/▾` (`:743-744`), kapalı özet `.pm-*` hücre dilinden, gövde `border-top:1px solid var(--line)` ile ayrılır | **36 kayıtlı anahtar** (`KART_KAYDI`) | her kart kendi bölümünün yükü |
| **Genel bakış kartı** `.gb-kart` | `gbKart()` `app.js:1709` · sayı `_gbSay()` `app.js:1720` · alarm `gbAlarmSatiri()` `app.js:1902` | `index.html:836-856` | `var(--card)` + `1px var(--line-2)` + `12px`; sayı `--mono clamp(20px,2.6vw,26px)` ağırlık 400, `letter-spacing:-.04em` | **6 kart** (`GENEL_KARTLARI` `app.js:1689`: gece / sermaye / bugun / equity / karne / kapsama) | `/api/today` |
| **Durum kartı** `.durum-kart` | `durumKartHTML()` `app.js:2400` · defter `DURUM_KARTLARI` `app.js:2378` | `index.html:870-893` | `<button>`, hover `border-color:var(--line)`, seçili `border-color:var(--accent)`; `.uyari→--sev-2`, `.kopuk→--sev-1` | **4 kart** (dongu / kitap / emir / pozisyon) | nabız + kitap |
| **Metrik kartı** `.mcard` | `mc()` `app.js:8855` | `index.html:1106-1114` (`.mrow` 4 kolon) | **Kartlığı yok**: `background:none;border:none;border-left:1px solid var(--line);border-radius:0` — sol saç teliyle bölünmüş şerit; değer `--mono 28px/400/-.04em/tabular-nums` | tek varyant, `col` parametresiyle serbest renk | öğrenme/skiller |
| **Hipotez kartı** `.hyp` | serbest; `rowAttrs` ile satır-düğmesi (`app.js:403`) | `index.html:1263-1275` | `var(--card)` + `1px var(--line)` + `12px` + `padding:20px 24px`; başlık `--display 17px/400` | `.hyp.rowbtn` (klavye) `:1232` | adaylar |
| **Kahraman** `.hero` / `.hero-grid` | `spineHTML` çevresi ve `nextSessionCard()` `app.js:1209` | `index.html:1163-1182` | `var(--card)` + `12px` + **iç çerçeve** `::before{inset:7px;border:1px solid var(--line)}` — çift kenar; 3 kolon, aralarda `border-left` | dar ekranda 2 kolon + alt satır tam genişlik | bugün |
| **Ayrıntı katmanı** `<details class="detay-kat">` | `detayKatmani()` `app.js:1659` | `index.html:694-714` | `border-top:1px solid var(--line)`; özet mono `11px`, `▸/▾`, `.dk-neden` `max-width:80ch` | 1 | her yer |
| **Sözlük** `<details class="gloss">` | `glossaryCard()` `app.js:1453` · terim satırı `.gterm` | `index.html:1397-1405` | `1px var(--line-2)` + `12px` + `overflow:hidden`; açıkken özetin altında ayraç | 1 | `TERMS` sözlüğü `app.js:77` |

### Kart tabanı — iki ayrı sayı, ikisi de doğru

| Sayı | Ne sayıyor | Kaynak |
|---|---|---|
| **46 kayıtlı kart** = 36 (`KART_KAYDI`, v198 katlanır) + 6 (`GENEL_KARTLARI`) + 4 (`DURUM_KARTLARI`) | **Defterlerde ADI olan** kartlar | `app.js:2038, 1689, 2378`; bu turda `grep -oE 'katKart\("[^"]+"' \| sort -u` ile doğrulandı |
| **101 ölçülen kart** = `{"karar": 27, "saglik": 24, "ogrenme": 45, "kilitler": 5}` | Alan sayfalarında **fiilen basılan** kart | `tests/test_kart_sozlesmesi_v198.py:114` `KART_TABANI` — **ratchet**, bkz. §2.4/K1 |
| **25 kapaklı** = `{"saglik": 4, "karar": 3, "ogrenme": 18, "kilitler": 0}` | Katlanabilir kapağa geçmiş kart | `tests/test_kart_sozlesmesi_v198.py:138` `KAPAK_TABANI` — **taban, altına düşülemez** |

Serbest `class="card"` emisyonu ayrıca **107** (üst sınır; bazıları aynı şablonun tekrarı).
**Redesign uyarısı:** kart konsolidasyonu (ör. Öğrenme'nin 45 kartını 12'ye indirmek) bu iki
ratchet'i birden kırar ve ancak **tabanı beyanla düşürerek** yapılabilir.

## 1.3 Hücre dili (v192) — kart tabanının ALTINDAKİ ortak dil

Tek çıkış noktası: `hucreGovde(o)` `app.js:1964`. Dört katman, sırası SABİT.

| Katman | Sınıf | CSS | Kural |
|---|---|---|---|
| Değer | `.pm-yield` | `index.html:960-970` — `clamp(18px,2.2vw,24px)`, ağırlık 500, `-.045em` | `null`/`""` ise **`.pm-none` "veri yok"** basılır, sıfır UYDURULMAZ (`app.js:1975`) |
| Oran | `.pm-conf` | `index.html:954-955` — 2px iz, `--conf` yüzdesi, `border-radius:2px` | `hucreCubuk()` `app.js:1952`: **paydasız çubuk çizilmez**; oran 0 → boş çubuk ÇİZİLİR, oran null → çubuk HİÇ doğmaz |
| Meta | `.pm-n` | `index.html:971-972` — 12px, `tabular-nums` | En fazla 2 satır |
| Rozet | `.pm-thin` | `index.html:975` — mono 10px/700 | "AZ VERİ" · "ÖLÇÜLEMEDİ" · "BEKLİYOR" · "SERMAYE-RESET" |
| İnce örneklem halkası | `.pm-cell.thin` | `index.html:974` — `inset 0 0 0 1px var(--olcek-guven-h)` (alfa .45) | Ölçüldü: .30 → 2,03/2,12 KALDI; .45 → 3,12/3,03 GEÇTİ (`index.html:236-244`) |
| Sesli hâl | — | — | `hucreSesli()` `app.js:1981` gövdeden TÜRETİR, ikinci kez yazmaz |

**Matris kabı** `.pm-grid` `index.html:941-950`: `170px + repeat(--cols)` ızgara, hücre arası **1px
saç teli boşluk** (`gap:1px` + `>*{background:var(--bg)}` hilesi), hücre `min-height:106px`.
Dar ekranda tek kolona iner (`index.html:1049-1059`).
**Özet şeridi** `.ozet-serit` `index.html:1042-1045` + `ozetSerit()` `app.js:1996`: aynı reçete,
**DÖRT hücre bir bütçedir**, beşinci şeridi taşırır; şerit TIKLANMAZ.

## 1.4 Rozet / çip aileleri

| Aile | Üreten | CSS | Görsel | Varyant |
|---|---|---|---|---|
| **Durum çipi** `.tag` | `_chip(txt,cls)` `app.js:3058` (41 emisyon) | `index.html:1238-1242` | mono 10px/700, `padding:4px 9px`, `radius:10px`, BÜYÜK HARF, `.16em` | **4**: `t-go`(sev-3 tint+halka) · `t-rv`(sev-2) · `t-no`(sev-1) · `t-vi`(accent-tint + `--ink-h` halka = "hüküm yok") |
| **Mod çipi** `.tag[data-mod]` | `modJetonu()` `app.js:491` | `index.html:1465-1467` | `live` → mod-canli tint + halka; `olculemedi` → **`1px dashed`** | 3 (`paper`/`live`/`olculemedi`) |
| **Kapı çipi** `.gc` | `gateLegend()` `app.js:1448` + serbest | `index.html:1518-1522` | mono 10px/700, `radius:10px`, inset halka | 3: `.p`(geçti) `.f`(düştü) `.arrow`(zincir oku, renksiz) |
| **Sayaç hapı** `.pillc` | `buildSidebar()` `app.js:898` | `index.html:631-634` | mono 10px/700, `padding:2px 7px` | 3: dolu(accent) · `.g`(sev-3) · `.q`(sessiz, yalnız halka) |
| **Onay kutusu** `.ck` | serbest (20 emisyon) | `index.html:1361-1364` | 18×18, `radius:0`, mono 10px/700, inset halka | 3: `.ok`(sev-3) `.no`(nötr) `.man`(sev-2) |
| **HUD çipi** `.hudchip` | `renderHUD()` `app.js:2988` | `index.html:1484-1490` | `1px var(--line)` + `var(--card)`, içinde 6×6 `radius:0` LED `.ld` | LED 4 hâl: yeşil/`.bad`/`.warn`/`.off`; kap 1 varyant `.explore`(mod-kesif) |
| **Durum hapı** `.statuspill` | `refreshStatus()` `app.js:514` | `index.html:529-551` | `1px var(--line-2)`, `var(--card)`, mono 12px, `radius:10px`, **height:44px** | nokta `.dot` 3 hâl (sev-3 / `.stale`→sev-2 / `.halt`→sev-1) |
| **Zincir metni** `.chain` | serbest (65 emisyon) | `index.html:1244-1252` | mono 11px `--tx2` | 4 rol niteleyicisi; **özgüllük (0,2,0) ile kap yenilir** — `index.html:1245-1250`'deki not bunun bir kez sessizce kırıldığını belgeliyor |
| **Belirsizlik işareti** `.belirsiz` | `belirsiz(icerik,beyan)` `app.js:3097` | `index.html:1636` | `text-decoration:underline dashed currentColor 1px` + ZORUNLU `title` beyanı | 1 — **RENK TAŞIMAZ** (renk ölçümün kanalı, doldurma ölçüm değil) |
| **Bayatlık solması** `.bayat-1/2/3` | `bayatSinif()` `app.js:3142` | `index.html:1641` | `opacity .78 / .58 / .42` | 3 kademe (1/3/7 gün, `BAYAT_ESIK_GUN` `app.js:3141`) — **opaklık NİCELİK TAŞIMAZ**, sayı hiçbir kademede gizlenmez |
| **Üstü çizili** `.struck` | serbest | `index.html:428` | `line-through`, `--line-2` çizgi rengi, `.75` opaklık | 1 |

## 1.5 Tablolar ve satır aileleri

| Aile | Üreten | CSS | Görsel | Not |
|---|---|---|---|---|
| **Izgara satırı** `.trow` | serbest — **117 emisyon** | `index.html:1187-1234` | `display:grid`, `padding:13px 0`, `border-bottom:1px solid var(--line)`, 13px, `tabular-nums` | **Kolon genişlikleri 114 yerde SATIR İÇİ `grid-template-columns` ile px olarak yazılı** — v205 çivisi (`app.js:6243`) bunun ÖLÇÜLDÜĞÜNÜ söylüyor: 340px diz noktası, 320→340px arası tek-satır oranı %39→%63 |
| Başlık satırı | `.trow.head` | `index.html:1234` | mono 10px/700 BÜYÜK HARF `.16em`, `--tx2` | — |
| Sayı hücresi | `.trow > .num`, `.tbl .num` | `index.html:1317,1328` | sağa dayalı, `tabular-nums` | — |
| **Klasik tablo** `.tbl` | serbest — 40 emisyon | `index.html:1306-1329` | `border-collapse:collapse`, `th` mono `--label-size` 700, `td` alt saç teli | Son satırda saç teli düşer |
| Satır düğmesi `.rowbtn` | `rowAttrs()` `app.js:403` · `openRecord()` `app.js:405` | `index.html:1227-1233` | tam genişlik `<button>`, hover `--card-2`, seçili `--accent-tint` | Klavye sözleşmesi: Tab + Enter/Space |
| Kayıt satırı `.srow` | `pdRow()` `app.js:453` — **194 emisyon** | `index.html` (`.srow` `:1015` civarı grup) | etiket ⟷ değer, `<b>` sağda | Çekmece ve kart içinin ana satır formu |
| Olay satırı `.evrow` | `eventsFeed()` `app.js:1352` | `index.html:1409-1413` | `16px 1fr auto` ızgara, zaman mono 11px tabular | — |
| Kısayol satırı `.krow` | `kbdOverlay()` `app.js:11006` | `index.html:1422-1426` | `34px 110px 1fr` | — |
| Regresyon satırı `.regrow` | `firsatRegresyon()` `app.js:7358` | `index.html:1644-1649` | `130px 1fr auto`; `.live .nm` accent-2/700 | — |
| Hat satırı | `_hatSatiri()` `app.js:6707` · `dagitimSatiri()` `app.js:6622` | `.trow` üstünde | — | — |
| Satır koruyucu | `satirKoru(alan, uret)` `app.js:1588` | — | Bir SATIRIN çizimi patlarsa satır dürüst **"ÖLÇÜLEMEDİ · veri-şekli beklenmedik"**e döner (`app.js:1599-1601`) | YASA 4 |

## 1.6 Sayaçlar, ölçerler, göstergeler

| Aile | Üreten | CSS | Görsel | Kural |
|---|---|---|---|---|
| **Büyük sayı** `.bignum` | serbest | `index.html:1281` | `--mono clamp(24px,6vw,28px)` ağırlık **400**, `-.05em`, `tabular-nums` | Büyük sayı LARGE ve LIGHT, kalın değil (DESIGN.md:589) |
| **Çubuk** `.bar` + `<i>` | `_bar(pct,color)` `app.js:3586` | `index.html:1257-1259` | 5px, `radius:0`, iz `--bg2`, dolgu `--accent` | Lineer metre |
| **Termometre** `.thermo .tube` | `app.js:3745` civarı | `index.html:1565-1568` | 14×86px dikey tüp, `1px var(--line-2)`, `radius:0` | **Gauge Ban'ın istisnası**: yasak RADYAL kodlamaya, dikey bara değil (DESIGN.md:952) |
| **Bullet grafiği** `.bullet` | `_bullet(o)` `app.js:3766` | `index.html:1532-1558` | 150px eksen + 54px okuma = **212px SABİT**; 3 niteliksel bant (`--card-2 → --band-2 → --tx2`) | Few spesifikasyonu; **The Absent-Comparison Rule** (dik çizgi yalnız gerçek kıyas varsa) ve **The Empty-Bar Rule** (ölçüm yoksa çubuk çizilmez, "ölçüm yok" yazılır) — DESIGN.md:958-978 |
| **İkiz çubuk** `.twin .tb` | serbest | `index.html:1513-1515` | mono 11px tabular + gömülü `.bar` | — |
| **Sparkline** | `sparkline(vals)` `app.js:1439` | satır içi SVG 150×30 | `polyline`, `stroke:var(--green|--red)`, `opacity .85` | **DEĞER jetonu** — rol katmanını atlıyor |
| **Piyasa sparkline** | `mktSpark(vals)` `app.js:3993` | satır içi SVG 90×24 | aynı desen | aynı |
| **IC trend** | `icTrend(hist)` `app.js:3879` + efsane `icEfsane()` `app.js:3914` | satır içi SVG 120×28 | Üç seri LUMİNANS merdiveni (`--accent 17,8 → --violet 9,6 → --tx3 5,06`), ayrım **ikinci kanaldan: kesik-çizgi deseni**, efsane deseni GÖSTERİR | Hue eklenmedi — renk körü okuyucu ayıramaz |
| **Bootstrap çan** | `_bellSVG(h)` `app.js:3706` | satır içi SVG | 40 kutu; Δ=0 gri, ortalama, **EŞİK amber kesik çizgi** (`app.js:3731,3734` — koşulsuz `var(--amber)`) | "Görsel kural = matematiksel kural" |
| **Kalibrasyon saçılımı** | `scatter(pts)` `app.js:8642` | satır içi SVG 340×220 | `r=5` daireler, işaret tutarlıysa `var(--green)` değilse `var(--red)` | **DEĞER jetonu + tek kanal (renk)** — ikinci kanal yok |
| **Sermaye eğrisi** | `line(pts,b)` `app.js:9485` + beyan `egriBeyani()` `app.js:9565` | satır içi SVG | Kesinti çizgileri `var(--amber)` kesik (`:9511`), son değer etiketi koşulsuz `var(--green)` (`:9543`) | İki boş hâl ayrı: "hiç nokta yok" ve "tek nokta var" — ikisi de ÇİZİLMEZ (`app.js:9485-9488`) |
| **Kapsama ısı matrisi** | `kmCiz()` `app.js:4106` · bant `_kmBant()` `app.js:4098` · sapma `_kmSapmaBant()` `app.js:4101` | `index.html:1070-1097` | `186px + repeat(--kmc,minmax(74px,1fr))`, 1px saç teli ızgara; hücre `k1..k4` (sequential) veya `dn2..dp2` (diverging) | Tavan alfa .30 (ölçülmüş sınır) |
| **Desen matrisi** | `plotCell()` `app.js:8876` · `renderPlotMap()` `app.js:8903` | `.pm-grid` | Hücre `.pos/.neg` yön zemini (alfa .08/.07) | `signClass()` `app.js:8871` |

## 1.7 Uyarı / alarm / sağlık satırları

| Aile | Üreten | CSS | Görsel | Varyant / kural |
|---|---|---|---|---|
| **Triyaj omurgası** `.spine` | `spineHTML(t,h,rc,ws)` `app.js:1139` | `index.html:903-930` | Tam genişlik şerit, üst+alt saç teli, solda 8×8 **kare** işaret (`::before`, `radius` yok) | **3 hâl**: `.calm`(şeffaf zemin, sönük, damga-yeşili kare) · `.attn`(sev-2 tint + sev-2 kenar) · `.act`(sev-1 tint + sev-1 kenar) |
| **Sessiz hat** `.sessizhat` / `.sh-global` | `sessizHat(sh)` `app.js:3530` · askıda dalı `_shAskidaSatiri()` `app.js:3176` | `index.html:1579-1617` | mono 12px, sticky (`top:var(--navh)`), `:empty{display:none}` | **Level-1 toplama** (ISA-101/HP-HMI atfı `app.js:3159`); açılım TAVANI 4 satır (`SH_ACILIM_TAVAN` `app.js:3165`), kalan "+7 daha" YAZILIR — kırpma sessiz olamaz. `.sh-sap`→sev-2, `.sh-sap.kritik`→sev-1; **askıda ≠ sapma** ve alarm rengine ÇEVRİLMEZ |
| **Alarm bütçesi** `.alarmbutce` | `alarmButce(ab)` `app.js:3563` · kart hâli `gbAlarmSatiri()` `app.js:1902` | `index.html:1623-1628` | mono 12px; `.asim` → sev-2 | Açık risk "alarm seviyesi değildir" — alarm yalnız TAVAN aşıldığında (`app.js:4313-4316`) |
| **Alarm gelen kutusu** | `alertsInbox(a)` `app.js:1379` | `.trow` + `.tag` | — | — |
| **Olay yüzeyi (çekmece)** | `olayYuzeyiHTML(sinif,ad)` `app.js:3455` · defter `OLAY_YUZEYLERI` `app.js:3224` · çözümleyici `olaySinifi()` `app.js:3443` · bağ `olayBagi()` `app.js:3521` | `.pdrawer` `index.html:992-1022` | **DÖRT bölüm, HEP AYNI SIRA**: ne oldu → değerler ŞİMDİ → runbook adımları → mevcut eylemler | **6 sınıf**: `besleme`(:3225) `mutabakat`(:3258) `kill`(:3310) `butunluk`(:3338) `yetki`(:3371) `kota`(:3393). Eşleşmeyen ad SESSİZCE atanmaz → `null` (`app.js:3448`) |
| **Bekçi durumları** | `bekciDurumlari(bd)` `app.js:7786` | `.trow` + `.tag` | — | — |
| **Eşik satırı** | `esikHal()` `app.js:7491` · `esikSatiri()` `app.js:7509` | — | İki kademeli eşik + NO_DATA hâli | F14 |
| **Alarm taksonomisi** | `firsatAlarmTaksonomi(ag)` `app.js:7709` | — | — | F5 |
| **Koruma kartı** | `korumaKurmaKarti(k)` `app.js:7987` · satır `korumaSatirHTML()` `app.js:7967` · sonuç `_korumaSonucSatiri()` `app.js:8095` | — | — | — |
| **Boş hâl** `.empty` | serbest — 51 emisyon | `index.html:1254` | ortalı, mono 12px, `--tx2`, `padding:32px` | — |
| **İpucu** `.hint` | serbest — **272 emisyon** (en kalabalık ikinci sınıf) | `index.html:1380-1385` | 14px, `--tx2`, `max-width:70ch` | 4 rol niteleyicisi (`sev-1/sev-2/warn/guven`) |

## 1.8 Kilit / müdahale / yıkıcı kontroller

| Aile | Üreten | CSS | Görsel |
|---|---|---|---|
| **HALT kolu** `.halt` | `toggleHalt()` `app.js:550` | `index.html:544-546,550` | `1px solid var(--sev-1)`, şeffaf, mono 700 `.1em`, `height:44px`; hover → dolu sev-1 |
| **Kriz kapağı** `.kscover` + `.ksgroup` | `setKs(open)` `app.js:595` | `index.html:1497-1508` | Kapak sev-1 kenar; açıkken dolu sev-1; grup mutlak konumlu panel, düğmeler `min-height:44px`, `.armed` → sev-2 |
| **Merdiven kartı** | `ladderCard(L,faz6)` `app.js:10832` · `faz6Satiri()` `app.js:10789` · `kilitOlcumHucreleri()` `app.js:10711` | — | Otonomi merdiveni |
| **Giriş kapısı** `.gate` | `kapiyiGoster()` `app.js:10875` · `kapiyiKapat()` `app.js:10892` | `index.html:474-491` | Tam ekran `var(--bg)`; kart `max-width:380px`, `1px var(--line-2)`; giriş `1px solid var(--field)`; düğme dolu `--accent` |
| **Yıkıcı düğme** | serbest, satır içi `style="border-color:var(--red);color:var(--red)"` | — | `app.js:3678, 8780, 9738` — **satır içi DEĞER jetonu** |
| **Komut paleti onayı** `.mrdp-onay` | `palette.js:372-379` | palette.js enjekte | `1px solid var(--red)` + `--r-card`; **ince ve dört-kenar** — kalın tek-kenar şerit "jenerik/AI-tell" diye reddedildi (`palette.js:370-371`) |

## 1.9 Kenar şeridi, üst bar, çekmece, palet

| Aile | Üreten | CSS | Görsel |
|---|---|---|---|
| **Kenar şeridi** `.side` | `buildSidebar(today,x)` `app.js:898` · yükseklik `syncNavHeight()` `app.js:574` | `index.html:573-629` | Sticky `top:78px`; `.sitem` `min-height:44px`, 20×20 ikon (`_ico()` `app.js:723`), 2 satırlık canlı özet `.sub` (mono 11px, `-webkit-line-clamp:2`), aktif göstergesi **3px sol şerit** (`::before` `scaleX`) |
| **Hesap bloğu** `.acct` | `buildSidebar` | `index.html:578-582` | Kartlık YOK: `border-top` + satır başına `border-bottom`; değer mono 12px tabular `nowrap` |
| **Tema düğmesi** `.sitem.tema` | `_temaDugmesiHTML()` `app.js:1025` · `theme.js` | `index.html:457-463` | Şeridin AYAĞINDA, üst barda değil (DESIGN.md:982) |
| **Çekmece** `.pdrawer` | `openDrawer()` `app.js:354` · `closeDrawer()` `app.js:368` · kayıt `rec()` `app.js:399` | `index.html:992-1022` | `position:fixed`, `width:min(430px,100%)`, kapalıyken `translateX(101%)` + `visibility:hidden`; başlık `--display 20px/600`; `.pd-stats` 3 kolon; `.pd-warn` sev-2 tint |
| **Komut paleti** `.mrdp-*` | `palette.js` (kendi CSS'ini `stilEnjekteEt()` `palette.js:335` ile basar) | `palette.js:339-387` | `--scrim` + `backdrop-filter:blur(4px)`; panel `min(640px,100%)`, `--card` + `--line-2` + `--r-card`; **`box-shadow:var(--elev)`** (yani `none`); seçili satır `--accent-tint` + 2px sol şerit |
| **Klavye kaplaması** `.kbd-ov/.kbd-panel` | `kbdOverlay(show)` `app.js:11006` | `index.html:1422 civarı` | — |
| **Atlama bağı** `.skip` | `index.html` | `index.html:1653-1655` | `min-height:44px`, odaklanınca `left:0` |

## 1.10 Tipografi envanteri (ölçülmüş)

| Basamak | Boyut | index.html'de kaç kural | DESIGN.md rolü (`DESIGN.md:573-595`) |
|---|---|---|---|
| Label | 10px | 21 | mono mikro-etiket, BÜYÜK HARF `.16em` |
| Micro | 11px | 27 | yoğun tablo metası, çip metni |
| Small | 12px | 29 | yoğun ızgara hücreleri |
| Compact | 13px | 28 | **kart/çekmece varsayılan UI metni** |
| Body | 14px | 14 | akan düzyazı |
| Title | 17px | 3 | kart başlığı |
| Headline | 20px | 5 | bölüm/çekmece başlığı |
| Grid figure | 24px | 1 | matris hücresindeki sayı (ağırlık 500) |
| Display | 28px | 1 | görünümün en büyük başlığı / stat kartındaki sayı |
| (akışkan) | 7 ayrı `clamp()` | — | `clamp(16,1.7vw,20)` · `(18,2.2vw,24)` · `(20,2.6vw,26)` · `(24,3.3vw,28)` · `(24,3.7vw,28)` · `(24,4.6vw,28)` · `(24,6vw,28)` |

- **Dokuz basamak, başka yok** — *Ramp Rule*, `DESIGN.md:575`.
- `tabular-nums` index.html'de **27** kuralda; `.mono-num` app.js'te **165** emisyon.
- `font-family:var(--mono)` index.html'de **69** kuralda. Mono yalnız iki iş için: mikro-etiket ve
  her türlü sayı (`DESIGN.md:594`).
- `@font-face` `index.html:104-113`: `font-display:block` (swap DEĞİL, bilerek — takas anında
  tabular sütun YATAY KAYAR), değişken ağırlık ekseni **400–700**'e daraltılmış (117,9 KB → 79,3 KB).

## 1.11 Hareket envanteri

| Ad | Tanım | Kural |
|---|---|---|
| `--t:.15s` / `--t-rise:.34s` / `--ease:cubic-bezier(.16,1,.3,1)` | `index.html:282` | Design rules ≤300ms (`DESIGN.md:540`); v198 çivisi ≤200ms (`tests/test_kart_sozlesmesi_v198.py:338`) — `--t` ikisini de karşılar, `--t-rise` AYRI jetondur |
| `.rise` / `.rise.in` | `index.html:441,443` | Giriş animasyonu; **124 emisyon** |
| `@keyframes pulse` | `index.html:541` | **YALNIZ `.dot.pulse.stale` / `.dot.pulse.halt`** (`:539`) — sağlıklı nokta durağan. Gerekçe `:532-538`: eski koşulsuz puls "hareketin haber olma kapasitesini tüketiyordu" |
| `@keyframes blinkTag` / `.blink` | `index.html:1510-1511` | `50%{opacity:.25}` |
| `prefers-reduced-motion` guard | çivili: `tests/test_kart_sozlesmesi_v198.py:338` (`@media(prefers-reduced-motion:reduce){*{transition:none!important`) | `DESIGN.md:540` hareketin bu koruma içinde olmasını şart koşuyor |

---

# [2] DEĞİŞMEZLER — redesign'in KIRAMAYACAKLARI

**Sınıflandırma:** 🔒 = ürün yasası (tasarım kararı değil) · ⚙ = ratchet/taban (aşılamaz sayı) ·
📐 = birebir metin çivisi (kaynak dizesi sabit).

## 2.1 Dürüstlük-UI yasaları

| # | Değişmez | Kilitleyen test (dosya:satır) | Assert özü | Redesign'de nasıl korunur (tek cümle) |
|---|---|---|---|---|
| D1 🔒 | **ÖLÇÜLEMEDİ ≠ 0.** Değeri olmayan hücre birebir `<span class="pm-none">veri yok</span>` basar | `tests/test_gorunurluk_v219.py:501` `test_OLCULEMEDI_sifir_YAZMIYOR_ve_gerekce_taşıyor` (assert :510) · sayım `:554` (tam 4) | Boş hücrenin **HTML'i birebir sabit**; "—" ya da boş bırakma yasak | `hucreGovde()`'nin (`app.js:1964`) boş dalı aynen kalır; yeni görsel dil `.pm-none`'ı yeniden BOYAR, yeniden ADLANDIRMAZ |
| D2 🔒 | **0 bir ölçümdür**, "veri yok" dalına düşmez | `tests/test_kart_sozlesmesi_v198.py:238` `test_sifir_bir_OLCUMDUR_veri_yok_dalina_dusmez` | `gecer_sifir`'da `pm-none` yok, `gecer_verisiz`'de var | Sıfır çubuğu ÇİZİLİR (boş görünür), null çubuğu HİÇ DOĞMAZ — `hucreCubuk()` `app.js:1952` |
| D3 🔒 | **Paydasız çubuk çizilmez**; her yüzde `data-payda` ile paydasını beyan eder | `tests/test_kart_sozlesmesi_v198.py:229` `test_paydasiz_CUBUK_cizilmez` (assert :232-234) | Paydasız → boş dizge; tam → `class="pm-conf"` + `data-payda="uygulanabilir desen (7)"` | Çubuk biçimi (2px iz) değişebilir; `data-payda` özniteliği ve boş-dizge dalı değişemez |
| D4 🔒 | **Hücre HİÇ doğmama yasağı** — boş durumda öğe gizlenemez | `tests/test_gorunurluk_v219.py:483` | "hiç doğmaması sorunun sorulmadığını gizlerdi" | Redesign'ın "sadeleştirme" turu boş kartları KALDIRAMAZ |
| D5 🔒 | **Renk yalnız ölçülemeyende** (o yüzeyde) | `tests/test_gorunurluk_v219.py:582` (assert :587-588) | `degerSinif == "warn"` + `rozet == "ÖLÇÜLEMEDİ"` | Rol jetonu değişse de eşleşme korunur |
| D6 🔒 | **Provenance / ayna rozeti tek üretici**; `title` künyesi boş olamaz | `tests/test_ayna_rozeti_v239.py:100` (tek üretici) · `:143` doğruluk tablosu (assert :158-161) · `:49` üç sınıf (`ayna_yok`/`olculemedi`/`None`) | `aynaRozeti(hb)` var, eski tek-alan ifadesi yok; `"ayna uyumlu"` tam 1 yerde | `aynaRozeti()` `app.js:878` fonksiyon adı ve `baslik` alanı korunur; yalnız rozetin kabı yeniden çizilir |
| D7 🔒 | **Nabız-bayat beyanı**: mini eğri bile tazeliğini söyler; gecikme 0 ≠ ÖLÇÜLEMEDİ | `tests/test_wp2d_pano_beyani_v246.py:318` · `:123` · üç hâl `:284` · tek nokta `:310` | Sparkline'a tazelik etiketi ZORUNLU | Yeni sparkline formu da tazelik etiketi taşır; `bayatSinif()` `app.js:3142` opaklık kademesi korunur |
| D8 🔒 | **Pano kendi hesaplamaz** — yalnız uçtan gelen beyanı çizer | `tests/test_wp2d_pano_beyani_v246.py:275` · `:269` | Frontend'de türetilmiş metrik yasak | Yeni bileşen de yalnız çizer; ikinci eşik hesabı açılamaz |
| D9 🔒 | **YASA 6 — her uç alanının panoda okuyucusu var** | `tests/test_wp2d_pano_beyani_v246.py:327` · `tests/test_acil_dogruluk_v196.py:439` | Bir alanı UI'dan kaldırmak = API alanını da kaldırmak | **Redesign "bilgi kırpamaz"**: bir satırı silmek için önce üretimini silmek gerekir |
| D10 🔒 | **Sermaye-köken** — boyut tabanı `realized_pnl`, nakit değil; ters-onarılmış kitap kaynak-farkındalı kimlikte yakalanır | `tests/test_bayat_sermaye_koku_v213.py:92,167,204` · zincir `tests/test_equity_zinciri_v264.py:48` | — | `sermayeKokenSatiri()` `app.js:768` satırı korunur; yalnız tipografisi değişir |
| D11 🔒 | **Mod uydurulmaz** — `MOD ÖLÇÜLEMEDİ` üçüncü hâldir | `tests/test_acil_dogruluk_v196.py:180` · `:219` (`modJetonu()` adı birebir) · `:209` (`class="tag t-vi"` reçetesi) | Hiçbir uydurma mod dizesi yok | `modJetonu()` `app.js:491` adı ve `t-vi` sınıfı çivili — rozet kabı yeniden boyanır, adı değişmez |
| D12 🔒 | **Doldurma (ffill) rozeti** — doldurulmuş satır işaret taşır, bayraksız hâl "sessizce temiz" sayılmaz, beyansız kesik çizgi yok | `tests/test_acil_dogruluk_v196.py:389,400,419,428` | — | `_dolduruldu()` `app.js:3117` + `belirsiz()` `app.js:3097` **RENKSİZ** kalır (renk ölçümün kanalı) |
| D13 🔒 | **Bozuk satır durum UYDURMAZ** — dürüst "ÖLÇÜLEMEDİ" satırına döner | `tests/test_pano_mudahale_satiri_v194.py:180` `test_bozuk_satir_DURUM_UYDURMAZ` · guard sayımı `:207` (tam 4 `satirKoru`) | Bozuk satırda `<button>` yok | `satirKoru()` `app.js:1588` adı ve dört çağrısı korunur |
| D14 🔒 | **Özetsiz kart kapak ALMAZ ve SAYILIR** (YASA 4) | `tests/test_kart_sozlesmesi_v198.py:256` | `if (!ozet)` + `kat="hayir"` + `ozetsiz.push` + `console.warn/error` | Sessiz yutma yasağı; yeni kart dilinde de aynı üç kapı |

## 2.2 v196 "CIRCIR" (çırçır/ratchet) tavanı — `?? 0` / `|| 0`

> **Terim düzeltmesi (ölçüm):** testlerde yazım **`CIRCIR`**tir; `grep -rn 'çırçır' tests/` = 0 hit.

| # | Değişmez | Test (dosya:satır) | Assert | Korunma |
|---|---|---|---|---|
| C1 ⚙ | **Null-sıfır tavanı = 192.** app.js'e tek bir yeni `?? 0`/`\|\| 0` bile eklenemez | `tests/test_acil_dogruluk_v196.py:472` `test_nullsifir_sayisi_CIRCIRI_asmiyor` (tavan `:469`) | `_nullsifir_say(APPJS) <= 192` | Redesign yeni katlama üretmez; yükseltmek `research/olcumler/nullsifir_triyaj_2026-08-06/RAPOR.md` güncellemesi ister. *Bugünkü ham sayım: `?? 0` = 151, `\|\| 0` = 55 (toplam 206; testin sayacı 192 tavanla ölçüyor — sayaç muhtemelen yorum satırlarını eliyor, bu turda doğrulanmadı → **None + neden: `_nullsifir_say` gövdesi okunmadı**)* |
| C2 ⚙ | **İcra/ayna kartında sıfır tolerans** | `tests/test_acil_dogruluk_v196.py:502` (assert :506) | `_nullsifir_say(icra) == 0` | O kart yeniden yazılırken hiç null-katlama kullanılamaz |
| C3 📐 | **Dört eski kalıbın birebir metni yasaklı** | `tests/test_acil_dogruluk_v196.py:489` (assert :496-497) | `"const n = g.bosluk_sayisi ?? 0"`, `"const pend = it.backfill_pending \|\| 0"`, `"${ud.n_stale \|\| 0} endeksten düşen"`, `"const n = w.n_hypotheses ?? 0"` app.js'te YOK | Yeniden yazımda aynı ifadeye dönülemez |
| C4 📐 | **Beş fonksiyon ADA BAĞLI taranıyor** | `tests/test_wpux_d3b_v229.py:384` | `esikHal, esikSatiri, firsatKagitCanli, firsatSapmaKoku, firsatEsikPaneli` gövdelerinde `(\?\?|\|\|)\s*0` yok | **Bu beş fonksiyon yeniden adlandırılamaz/parçalanamaz** (`app.js:7491, 7509, 7529, 7594, 7648`) |
| C5 📐 | Aynısı F5 için | `tests/test_wpux_d3b_f5_v230.py:242` (assert :247) | `firsatAlarmTaksonomi` gövdesi | `app.js:7709` adı çivili |

## 2.3 v197 koşulsuz-emisyon kapısı ve renk rolleri

| # | Değişmez | Test (dosya:satır) | Assert | Korunma |
|---|---|---|---|---|
| E1 ⚙🔒 | **Koşulsuz emisyon TAVANI = 0.** Veri dalına bağlı olmayan hiçbir renk basılamaz | `tests/test_renk_rolleri_v197.py:367` `test_kosulsuz_emisyon_tavani` (assert :379-380); harici ölçüm `research/.../tara_emisyon.py` | `len(kosulsuz) == 0` **ve** `kosullu` boş değil | **Redesign'in en sert görsel çivisi**: dekoratif renklendirme, marka aksanı, statik vurgu İMKÂNSIZ → Dub'ın elektrik-mavisi bu kapıdan geçemez (bkz. §4.3) |
| E2 📐 | **Fiyat seviyesi nötr** — stop kırmızı, hedef yeşil olamaz | `tests/test_renk_rolleri_v197.py:457` | `class="mono-num neg">stop` ve `…pos">hedef` YOK; `class="mono-num">stop ${trn(p.stop, 2)}` VAR | Satırın birebir HTML metni sabit |
| E3 📐 | **Risk büyüklükleri nötr** | `tests/test_renk_rolleri_v197.py:464` | `pos">gerçekleşen`, `warn">açık`, `neg">${v.geri_verilen_r` yok | `app.js:4313-4322` yorumu bunun gerekçesi |
| E4 🔒 | **Bileşen kuralı ham hue okumaz; CSS'te ham renk literali yok; app.js'te ham renk literali yok; tek kuralda birden çok rol yok; gezinme rayı kromatik değil** | `tests/test_renk_rolleri_v197.py:207,218,245,255,263,271` | — | CSS'e `#hex`/`rgb()` yazılamaz — yalnız rol jetonu. **Ölçüldü ve tutuyor: `grep -oE '#[0-9a-f]{6}' app.js` = 0** |
| E5 🔒 | **Mod kanalı YAPISALDIR** | `tests/test_renk_rolleri_v197.py:323` | `body[data-mod]::before{…var(--mod-kagit)}`, `body[data-mod="live"]::before`, `body[data-mod="olculemedi"]::before` + `document.body.dataset.mod = m \|\| "olculemedi"` | **Üç `body[data-mod]` seçicisi ve `::before` bandı silinemez** (`index.html:1454-1462`) |
| E6 🔒 | **İki zeminde ad kümesi EŞİT** — bir zeminde tanımlı olup diğerinde olmayan rol jetonu BUG'dır | `tests/test_renk_rolleri_v197.py::test_iki_zeminde_ad_kumesi_esit` (`index.html:365-370` bu testi adıyla anıyor) · ayrıca `:23,174-186,342` kroma kısıtı | Yön kroması < şiddet kroması (gündüz 0,059<0,0917; gece 0,059<0,1289) | Yeni palet iki zeminde de TAM üretilmeli; ters çevirme yasak (*Tint-Direction Rule*) |
| E7 🔒 | **Dikkat işareti kaynağı**: `data-dikkat="1"` yalnız rozet/şiddetten; yön (`neg`) dikkat üretmez | `tests/test_kart_sozlesmesi_v198.py:244` | — | Negatif değer otomatik uyarı rengi ALAMAZ |

## 2.4 v198 kart tabanı — **bugünkü sayı**

| # | Değişmez | Test (dosya:satır) | Bugünkü taban | Korunma |
|---|---|---|---|---|
| K1 ⚙ | **Ölçülen kart toplamı = taban** | `tests/test_kart_sozlesmesi_v198.py:382` `test_olculen_kart_toplami_TABANLA_ayni` · `KART_TABANI` `:114` | **`{"karar": 27, "saglik": 24, "ogrenme": 45, "kilitler": 5}` = toplam 101** (+ `bugun` yüzeyi bu tabanda ayrı sayılmıyor) | **Kart ekleme/silme/BİRLEŞTİRME testi kırar.** Redesign'da konsolidasyon (ör. Öğrenme'nin 45 kartını 12'ye indirmek) ancak **tabanı beyanla düzenleyerek** yapılabilir |
| K2 ⚙ | **Kapağa geçen kart tabanın altına düşmez** | `tests/test_kart_sozlesmesi_v198.py:391` · `KAPAK_TABANI` `:138` | `{"saglik": 4, "karar": 3, "ogrenme": 18, "kilitler": 0}` = **25 katlanabilir** | Katlanabilir kart sayısı düşürülemez |
| K3 ⚙ | **Her alan sayfasının YAZILI bütçesi var** | `tests/test_kart_sozlesmesi_v198.py:372` | `set(KART_BUTCESI) == set(ALAN_BOLUMLERI)`, her bütçe ≥1 | `const KART_BUTCESI` ve `const ALAN_BOLUMLERI` (`app.js:1631`) sabitleri var olmalı |
| K4 📐 | **Tek çıkış**: ` data-kart="` tam 1 kez, `<span class="kk-ozet"` tam 1 kez | `tests/test_kart_sozlesmesi_v198.py:333` | — | İkinci bir kart üretici fonksiyon YAZILAMAZ |
| K5 🔒 | **Kapalı özet = hücre gövdesi**; `.kk-*` CSS bloğunda `font-variant-numeric`/`tabular-nums` **YASAK** | `tests/test_kart_sozlesmesi_v198.py:321` (assert :427) | — | Kapak başlığına ayrı sayı tipografisi verilemez — üçüncü sayı dili açılmaz |
| K6 🔒 | **Oturum hafızası `sessionStorage`, `localStorage` DEĞİL**; anahtar `` `mrd-kart:${alan}:${kart}` `` | `tests/test_kart_sozlesmesi_v198.py:304` | ≥2 `catch` | `_katAnahtar()` `app.js:2169` biçimi sabit |
| K7 🔒 | **Klavye/ARIA**: `createElement("button")`, `type="button"`, `aria-controls`, `role="region"`, `aria-labelledby`, `aria-expanded` + `govde.hidden`, `.kk-dugme` bloğunda `:focus-visible` | `tests/test_kart_sozlesmesi_v198.py:314` | — | Kapak `<div role=button>` YAPILAMAZ; `.kk-dugme` sınıf adı çivili |
| K8 ⚙ | **Hareket ≤200ms + reduced-motion guard** | `tests/test_kart_sozlesmesi_v198.py:338` | `--t` ≤200ms; `@media(prefers-reduced-motion:reduce){*{transition:none!important` | **NOT:** `--t:.15s` (`index.html:285`) bu tavanı karşılıyor; `--t-rise:.34s` AYRI jeton |
| K9 🔒 | **Accordion değil**; sayfa başına tek global kontrol; başlık metni **taşınır**, kopyalanmaz | `tests/test_kart_sozlesmesi_v198.py:283,293,329` | `kap.className = "kk-kontrol"` tam 1 kez; `while (bas.firstChild) ad.appendChild(bas.firstChild);` | — |

## 2.5 v194 / v205 yerleşim ve taşma çivileri

| # | Değişmez | Test (dosya:satır) | Assert | Korunma |
|---|---|---|---|---|
| Y1 📐 | `kol()` şablonunda `<!--` YOK ve gövdesinde ters tırnak YOK | `tests/test_pano_mudahale_satiri_v194.py:88` (assert :91,93) | Ölçüldü: iki ters tırnak çalışma zamanı `TypeError` atıyor ve ALTI bölümü birden düşürüyor (`app.js:4315-4320`) | `kol()` ve `satirKoru()` **ad + imza** çivili; müdahale satırının iskeleti (`class="kol-satir"`, `data-act="opSoftHalt"`) sabit |
| Y2 📐 | Tehlike işareti **satır içi** kalır; `.tehlike` sınıfı CSS'e DOĞMAMALI | `tests/test_pano_mudahale_satiri_v194.py:151` | `border-color:var(--red)` satır içi | **Bu, §5-R2'deki satır-içi DEĞER-jetonu bulgusuyla ÇELİŞEN bir çividir** — o satırlar bilerek satır içi tutuluyor |
| Y3 📐 | Guard **yeni sınıf açmaz** | `tests/test_pano_mudahale_satiri_v194.py:197` | Guard'ın yazdığı her `.sınıf` CSS'te var olmalı | — |
| Y4 🔒 | `.trow > *` kuralında `min-width:0` **ve** `overflow-wrap:anywhere` | `tests/test_yerlesim_tasma_v205.py:295` | — | `index.html:1219` |
| Y5 🔒 | **`.trow` kapsamlı HİÇBİR kuralda `white-space:nowrap`, `overflow-wrap:normal`, `text-overflow:ellipsis` YOK** | `tests/test_yerlesim_tasma_v205.py:335` `test_sarmalamayi_GERI_ALAN_kural_yok` (regex `(\.trow[^{;]*)\{`) | Tek meşru istisna `.trow > .num`: orada `white-space:normal` YAZILI (nowrap'ı geri alan yön) | **KAPSAM DÜZELTMESİ (bu turda ölçüldü):** yasak GLOBAL DEĞİL, yalnız `.trow` ailesine kapsamlı. Nitekim `.acct .r b` (`index.html:582`) ve `.sessizhat .sh-seg` (`:1591`) `nowrap` taşıyor ve test yeşil. Yine de **tablo satırlarında kırpma imkânsız** — gerekçe `app.js:5809-5812`: ekrandaki ad günlükte greplenen adla AYNI olmalı, yarım ad greplenemez |
| Y6 ⚙ | **Kimlik kolonu tam 340px**, satır oranı ≤ tavan | `tests/test_yerlesim_tasma_v205.py:350` · gerekçe metni `:365` (`"%84"` ve `"340px"` kaynakta YAZILI olmalı) | — | Gerekçe yorumu `app.js:6243-6254` silinemez |
| Y7 ⚙ | **`grid-template-columns` sayısı ≥100** (taban 102) ve sabit `\d+px` kolon sayısı **≥300** (taban 304) | `tests/test_yerlesim_tasma_v205.py:482` | — | **`grid-template-columns` kullanan ≥100 yeri flexbox'a çevirmek İMKÂNSIZ** — redesign ızgara mimarisini terk edemez |
| Y8 🔒 | Sabit-px ızgaraların hepsi `.trow` ailesinde | `tests/test_yerlesim_tasma_v205.py:453` | — | Yeni bileşen sabit px ızgara açamaz |
| Y9 ⚙ | Gerçek font metriğiyle **bindirme ≤ 0**; en uzun ad tam 2 satır | `tests/test_yerlesim_tasma_v205.py:380` / `:419` · metrik kaynağı `:102-106` (`tnum.json` + `measurements.json`) | — | **Yazı tipi değişirse bu iki test yeniden ölçülmeli** — font kararı yerleşim kararıdır |

## 2.6 Palet çivileri (iki ayrı "palet")

### A · Renk paleti / tasarım jetonları

| # | Değişmez | Test (dosya:satır) | Korunma |
|---|---|---|---|
| P1 🔒 | **Jeton ↔ `tokens.json` BİREBİR, iki yönlü** | `tests/test_tasarim_token_v153.py:189` + `:215` | Yeni bir `--jeton` eklemek `meridian/web/tokens.json`'ı da güncellemeyi ZORUNLU kılar |
| P2 🔒 | **Gece teması TAM** — her renk jetonu iki zeminde tanımlı | `tests/test_tasarim_token_v153.py:237` | Tek temaya renk eklenemez |
| P3 🔒 | **Ham renk YOK (altı yüzeyde)**; allowlist istisnası GEREKÇESİZ olamaz | `tests/test_tasarim_token_v153.py:585` + `:603` | Hardcoded renk imkânsız |
| P4 🔒 | **Rol alias zinciri tek gerçek söyler** | `tests/test_tasarim_token_v153.py:437` | `var()` zinciri çözülünce tek doğru |
| P5 ⚙ | **Dört yüzeyde jeton birliği**: `index.html`, `landing.html`, `runbook.html`, `workflow.html` aynı jeton sayısını taşır; yüzey başına **tam iki `:root` bloğu**; emekli jetonlar geri gelmez | `tests/test_jeton_birligi_v208.py:165,176,186,204,216` | **Dört HTML yüzeyi EŞZAMANLI değiştirilmeli** — `workflow.html` emekli edilse bile (TASARIM-YONU §1) jeton bloğu bu teste bağlı |
| P6 🔒 | **Gölge yasağı**: her `shadow` tipli jeton için `lit == "none"` | `tests/test_tasarim_token_v153.py:388` (assert :420-421) — *"gölge geri gelmiş — Omega'da `box-shadow:none` ölçülmüş bir karardır"* | Kart yükseltme, hover gölgesi, modal gölgesi İMKÂNSIZ |
| P7 🔒 | **Radial/donut yasağı**: `_donut`, `_ring(`, `conic-gradient`, `stroke-dashoffset` yok; `.gaugewrap{…border-radius:50%` yok | `tests/test_pano_sessiz_hat_v151.py:189-193` | Dairesel gösterge, radial progress, donut İMKÂNSIZ. `gaugewrap` sınıf ADI korunur |
| P8 📐 | **Bullet göstergenin beş bileşeni** | `tests/test_pano_sessiz_hat_v151.py:196` | `function _bullet(o)`, `class="bl-lab"`, `const centik = [0, ...bantlar]` çivili |

### B · Komut paleti (`palette.js`)

| # | Değişmez | Test | Korunma |
|---|---|---|---|
| P9 | Bulanık arama skorlama sözleşmesi (Türkçe katlama, sıralama yasaları, favori ≤9, grup sırası) | `tests/test_pano_palet_v152.py:78-217` | `P.katla` / `P.bulanikSkor` saf çekirdeği (`palette.js:56+`) korunur |
| P10 | Palet hedefleri app.js görünüm tablosuyla **birebir**; her komut çözülebilir rotaya gider | `tests/test_ia_v199.py:202-216` · `tests/test_s2r1_kabuk_v155.py:371-375` | **Görünüm/rota adları yeniden adlandırılamaz** — `palette.js` ve `app.js` tabloları ayrışırsa test kırılır |

## 2.7 CSP — `script-src 'self'`, CDN YOK, inline YOK

| # | Değişmez | Test (dosya:satır) | Korunma |
|---|---|---|---|
| S1 🔒 | **Satır içi olay özniteliği yok** (`on*="`) | `tests/test_web_csp_uyum.py:52` (taranan yüzey listesi `:36`) | `onclick=` hiçbir zaman kullanılamaz — tüm bağlama `addEventListener` |
| S2 🔒 | **Gövdeli `<script>` bloğu yok** | `tests/test_web_csp_uyum.py:67` | HTML'e inline script gömülemez |
| S3 🔒 | **Her `data-act` kayıtlı, çift yönlü tam** | `tests/test_web_csp_uyum.py:77` + `:101` | **Yeni bir düğme eklemek = izin listesine kayıt ZORUNLU**; delege dinleyici mimarisi (`_eylemCalistir()` `app.js:1076`) sabit |
| S4 🔒 | `eval` / `new Function` yok | `tests/test_web_csp_uyum.py:138` | — |
| S5 🔒 | **Caddyfile `script-src` gevşetilmemiş** | `tests/test_web_csp_uyum.py:118` (assert :128-134) · sunucu tarafı `tests/test_guvenlik_basliklari_v203.py:201` (assert :211) | `_direktif("script-src") == "'self'"` **BİREBİR** — nonce/hash bile eklenemez |
| S6 🔒 | **`font-src 'self'` (D4 sertleştirmesi) geri alınamaz** | `tests/test_guvenlik_basliklari_v203.py:214` | **Google Fonts İMKÂNSIZ** → Dub'ın Inter/Satoshi'si ancak self-host edilirse alınabilir |
| S7 🔒 | **Tüm CDN hostları yasak** (`fonts.googleapis.com`, `fonts.gstatic.com`, `use.typekit.net`, `fonts.bunny.net`, `cdn.jsdelivr.net`, `unpkg.com`) | `tests/test_yazitipi_v201.py:103` (assert :110-111) | **Hiçbir dış kütüphane/font/ikon seti yüklenemez** — redesign tamamen ev-tarafı varlıklarla yapılır |
| S8 ⚙ | **Altı betik yüzeyi var olmaya devam etmeli**: `/app.js`, `/theme.js`, `/landing.js`, `/workflow.js`, `/palette.js`, `/halt.js` | `tests/test_guvenlik_basliklari_v203.py:60` | **Dosya bölme/birleştirme testi kırar** — app.js'i modüllere ayırmak bu çiviye çarpar |
| S9 | `style-src`'deki `unsafe-inline` **borcu beyanlı kalır** | `tests/test_guvenlik_basliklari_v203.py:235` · gerekçe `deploy/Caddyfile:86` | app.js DOM'u satır-içi stille ürettiği için açık; **605 satır-içi stil bu borcun ölçüsüdür** |
| S10 🔒 | `frame-ancestors` / `base-uri` kapalı | `tests/test_guvenlik_basliklari_v203.py:227` | — |
| S11 📐 | Kart kapağında `on*="` yok; `e.target.closest(".kk-dugme")` delege dinleyicide | `tests/test_kart_sozlesmesi_v198.py:349` | `.kk-dugme` sınıf adı çivili |

**Yayın CSP'si (yorum satırı, `deploy/Caddyfile:107`):**
`default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`

## 2.8 `tabular-nums` / `mono-num`

| # | Değişmez | Test (dosya:satır) | Korunma |
|---|---|---|---|
| T1 🔒 | **Rakam hizalaması YAPISAL** — her font kesitinde `rakam_advance == [600]` (0-9 tek advance) | `tests/test_yazitipi_v201.py:331` | **Yeni yazı tipi yapısal tabular olmak ZORUNDA** — Inter `tnum` özelliğiyle sağlar, Satoshi ölçülmeli |
| T2 📐 | "The Tabular Rule" DESIGN.md gövdesinde `"Recursive Mono"`, `"tabular-nums"`, `"slashed-zero"`; Typography bölümünde `"inert"` | `tests/test_yazitipi_v201.py` (assert :523) | Tipografi kararı belgeye çivili — font değişirse DESIGN.md de değişmeli |
| T3 📐 | **`mono-num` sınıfı yeniden ADLANDIRILAMAZ**; bazı satırların HTML'i birebir sabit | `tests/test_wpux_d3b_v229.py:226-229` · `tests/test_renk_rolleri_v197.py:459-467` · `tests/test_kadans_damgasi_v207.py:538` · `tests/test_firsat_yuzeyleri_v200.py:369` | Ölçüm: `.mono-num` **165** emisyon; CSS `index.html:439` |
| T4 🔒 | **İzinli sınıf listesi** (fırsat yüzeylerinde): `chain, mono-num, tag, t-go, t-no, t-vi, t-rv, empty, tx3, warn…` | `tests/test_firsat_yuzeyleri_v200.py:369` | O yüzeylerde **yeni CSS sınıfı AÇILAMAZ** |
| T5 🔒 | Yerleşim ölçümü gerçek font metriğine bağlı (`tnum.json` + `measurements.json` `default_advances`) | `tests/test_yerlesim_tasma_v205.py:102-106` | Font değişimi = yerleşim yeniden ölçümü |

## 2.9 Erişilebilirlik / kontrast beyanları

| # | Değişmez | Test (dosya:satır) | Eşik | Korunma |
|---|---|---|---|---|
| A1 🔒 | **Yeni jetonlar iki zeminde AA** (`--yon-arti`, `--yon-eksi`, `--mod-canli`, `--mod-kesif`, `--olcek-guven`) | `tests/test_renk_rolleri_v197.py:394` | ≥4,5 (çıplak zemin **ve** kendi tinti üstünde) | Yeni renk seçimi **ikili tema × ikili zemin** AA'yı geçmeli |
| A2 🔒 | Matris hücre rakamı ve metası AA | `tests/test_renk_rolleri_v197.py:409` | ≥4,5 | Isı rampası tavanı .30'da sabit |
| A3 🔒 | **Metin-dışı 3:1** — mod bandı ve güven kenarı | `tests/test_renk_rolleri_v197.py:421` | ≥3,0 | WCAG 2.2 1.4.11 |
| A4 🔒 | **Kaynak sırası çakışması**: `.{kap}.{rol}{` kuralı var olmalı | `tests/test_renk_rolleri_v197.py:443` | — | Rol rengi kap tarafından ezilemez (bkz. §5-R4) |
| A5 🔒 | Para renkleri en kötü gerçek zeminde AA | `tests/test_tasarim_token_v153.py:763` | ≥4,5 | *Own-Ground Rule* |
| A6 🔒 | **Odak halkası her zeminde 3:1** | `tests/test_tasarim_token_v153.py:783` | ≥3,0 | Focus ring rengi değiştirilemez |
| A7 | Kontrast rakamları yeniden üretilebilir; rapor "bilinçli istisna" ve "öneri" bölümlerini taşır | `tests/test_tasarim_token_v153.py:746` + `:799` | — | `docs/kontrast-denetimi.md` bağlı |
| A8 ⚙ | Kapsama rampası tavanı AA ile sınırlı | `tests/test_wpp_p9_v171.py:296` | — | Alfa .34'te 4,45'e düşer |
| A9 | **WCAG 2.2 AA standarttır; APCA yalnız tasarım-yardımcısı** | `DESIGN.md:450-454` (*The WCAG-Is-The-Standard Rule*) | — | "APCA geçen, WCAG 2.2 düşen renk YAYINLANMAZ" |

## 2.10 Kaynak-metnini tarayan bekçi testleri (redesign'i en çok kısıtlayanlar)

**52 test dosyası `app.js` ve/veya `index.html` içeriğini STRING olarak tarıyor.** En ağır 12'si:

| Test dosyası | Yüklediği | Neden ağır |
|---|---|---|
| `tests/test_kart_sozlesmesi_v198.py:39-40` | app.js + index.html | Kart sayısı ratchet + tek-üretici + ARIA + CSS blok dilimleme (`CSS_KOD.index(".kk-dugme")`) |
| `tests/test_yerlesim_tasma_v205.py:48-49` | app.js + index.html | `grid-template-columns` ≥100, sabit px ≥300, nowrap/ellipsis yasağı |
| `tests/test_renk_rolleri_v197.py:43-44` | index.html + app.js | Koşulsuz emisyon 0, ham renk literali yasağı, kontrast, `body[data-mod]` |
| `tests/test_acil_dogruluk_v196.py:47-48` | app.js + index.html | `?? 0` cırcırı 192, birebir eski-satır yasakları, `modJetonu()` |
| `tests/test_tasarim_token_v153.py:59,68` | index.html + app.js | Jeton ↔ tokens.json iki yönlü, gölge yasağı, kontrast |
| `tests/test_pano_mudahale_satiri_v194.py:40-41` | app.js + index.html | Şablon içi ters tırnak/`<!--` yasağı, `satirKoru()` = 4 |
| `tests/test_wpux_d3b_v229.py:39-40` | app.js + index.html | Fonksiyon-adına bağlı gövde taraması (5 ad), `ozetSerit([` **tam 6** |
| `tests/test_wpux_d3b_f5_v230.py:37-38` | app.js + index.html | `firsatAlarmTaksonomi` gövdesi, `ozetSerit([` = 6 |
| `tests/test_ia_v199.py:28-30` | app.js + index.html + palette.js | Bilgi mimarisi: görünüm tablosu üç dosyada birebir |
| `tests/test_pano_sessiz_hat_v151.py:26-27` | app.js + index.html | Donut/conic/dashoffset yasağı, `_bullet()` yapısı |
| `tests/test_gorunurluk_v219.py:41` | app.js | `<span class="pm-none">veri yok</span>` birebir, sayım = 4 |
| `tests/test_firsat_yuzeyleri_v200.py:50` | app.js | İzinli CSS sınıf allowlist'i |

**Tam liste (52):** `test_acil_dogruluk_v196` · `test_agent_provider_yonlendirme_v244` · `test_alarm_hijyeni_v192` ·
`test_ariza_turu_v238` · `test_ayna_rozeti_v239` · `test_dalga2_entegrasyon_v226` · `test_dalga2_kucukler_v225` ·
`test_deger_esitligi_deseni_v239` · `test_dsr_hard_gate_v130` · `test_equity_zinciri_v264` · `test_f8_durum_sozlugu_v271` ·
`test_faz5_cikis_v212` · `test_firsat_yuzeyleri_v200` · `test_gemini_olu_model_gocu_v235` · `test_golge_fit_gorunurlugu_v192` ·
`test_gorunurluk_v219` · `test_hafta2_hukum_v110` · `test_hafta2_olcum_v111` · `test_holdout_rotasyon_v129` · `test_ia_v199` ·
`test_icra_gercekligi_v141` · `test_kadans_damgasi_v207` · `test_karar_kaydi_v240` · `test_kart_sozlesmesi_v198` ·
`test_kayan_oturum_v245` · `test_kopukluk_kapatma_v122` · `test_koruma_yeniden_kurma_v211` · `test_kucuk_paket_v275` ·
`test_ledger_contract_v57` · `test_nous_boru_v192` · `test_nous_eval_v131` · `test_pano_durum_kartlari_v191` ·
`test_pano_mudahale_satiri_v194` · `test_pano_palet_v152` · `test_pano_sessiz_hat_v151` · `test_pano_turu_v139` ·
`test_renk_rolleri_v197` · `test_s2r1_kabuk_v155` · `test_s2r2_goc_v156` · `test_s2r3_cila_v160` · `test_seam_registry_v64` ·
`test_tasarim_token_v153` · `test_triyaj_duzeltmeleri_v274` · `test_uiux_s1b_v154` · `test_v195a_quickwin` ·
`test_wp2d_pano_beyani_v246` · `test_wpd_kalanlar_v147` · `test_wpp_p9_v171` · `test_wpux_d3b_f5_v230` ·
`test_wpux_d3b_v229` · `test_yasa6_dort_rapor_v261` · `test_yerlesim_tasma_v205`

Ek olarak dört HTML yüzeyini + `deploy/Caddyfile`'ı tarayanlar: `test_jeton_birligi_v208` · `test_yazitipi_v201` ·
`test_font_rotasi_v202` · `test_guvenlik_basliklari_v203` · `test_web_csp_uyum`.

## 2.11 ÇİVİLENMEMİŞ olanlar (beyan — uydurma yasağı)

| Aranan | Denenen grep | Sonuç |
|---|---|---|
| Genel `border-radius: 0` / radius yasağı | `grep -rn 'box-shadow\|border-radius\|radius' tests/ --include='*.py'` | **BULUNAMADI.** Yalnız 2 hit (`test_pano_sessiz_hat_v151.py:193` `.gaugewrap` %50 yasağı; `test_tasarim_token_v153.py:421` gölge). Üç-yarıçap yasası **DESIGN.md:916'da yazılı ama testte ÇİVİLİ DEĞİL** — yalnız `tokens.json` ikili eşleşmesiyle dolaylı sınırlı |
| `prefers-reduced-motion` yaygın çivi | Yalnız `test_kart_sozlesmesi_v198.py:338` bulundu | Kart kapağı için çivili; genel hareket kuralı için ayrı çivi **bu turda bulunamadı** |
| "çırçır" (ç ile) | `grep -rn 'çırçır\|cirtir' tests/` | 0 hit — doğru terim `CIRCIR` |
| `KART_TABAN` (tekil) | `grep -rn 'KART_TABAN\|kart taban' tests/` | Doğru ad **`KART_TABANI`** |
| `wcag` / `a11y` literal | `grep -rn 'wcag\|a11y' tests/` | 0 hit — kontrast çivileri sayısal (`>= 4.5`, `>= 3.0`) ve `AA` adıyla |
| `_nullsifir_say` gövdesinin sayma kuralı | okunmadı | **ÖLÇÜLEMEDİ** — ham `?? 0`+`\|\| 0` = 206 ile tavan 192 arasındaki farkın nedeni doğrulanmadı |

---

# [3] BAĞLAYICI TASARIM YÖNÜ

## 3.1 `docs/TASARIM-YONU-2026-08-07.md` — özet

**Statü (`:3`):** *operatör onaylı (dört karar, 2026-08-07) · **bağlayıcı** — sonraki her dalga buna
dayanır.* ROADMAP de aynı sözle anıyor: `ROADMAP.md:1707` "yön: `docs/TASARIM-YONU-2026-08-07.md`,
**operatör onaylı, BAĞLAYICI**".

**Dört operatör kararı (§1, `:15-20`):**

| # | Karar | Türeyen hüküm |
|---|---|---|
| 1 | Yan yüzeyler: "mantıklı olanı yap" | `landing.html` **KALIR ve onarılır** · `workflow.html` **EMEKLİ** (halefi C1#4 canlı zaman çizelgesi) · `runbook.html` **EMİLİR** (olay yüzeylerinin içine; "dördüncü, dönüştürülmemiş görsel dünya" ölür) |
| 2 | **Bütün modüller yazılır** | C2'nin altı adayı da programa girer |
| 3 | Yazı tipi: **Impeccable önerisiyle git** | Geist emekli; aday ölçümle seçilir |
| 4 | **Yeni bilgi mimarisi onaylandı** | §3 bağlayıcı: beş yüzeyli IA |

**§2 — beş renk rolü, üç kanal yetmiyor (`:34-52`).** Ölçülen bugün: `--green` ≥4 rol · `--amber` ≥5 ·
`--red` ≥5 · mod kroması için kanal YOK · **164 koşulsuz `pos`/`neg`/`warn` emisyonu**.
Kapatılacak sızıntılar adıyla: stop fiyatı koşulsuz kırmızı · hedef koşulsuz yeşil · açık risk
koşulsuz amber · "KEŞİF MODU" amber'de (mod→şiddet) · "ince örneklem" amber'de (veri güveni→şiddet).

**§3 — beş yüzeyli IA (`:54-77`), BAĞLAYICI:** ① Bugün · ② Karar · ③ Sağlık · ④ Öğrenme · ⑤ Kilitler.
**Olay yüzeyleri (Tier-4):** sayfa değil, herhangi bir alarmdan açılan tam çekmece; dört bölüm.
*Değişmeyenler (ürün yasası, tasarım değil):* tek emir-yolu · dürüstlük yasaları (ÖLÇÜLEMEDİ≠0,
paydasız çubuk yok, uydurma yok) · **iki zemin + gündüz varsayılan** · dopamin yasağı · CSP-self · Türkçe.

**§5 — yazı tipi çıtası (`:104-115`), geçilmesi ZORUNLU:** kendi-barındırma (CSP dış font-host'a izin
vermez) · açık lisans · **tam Türkçe aksan** (ı/İ/ş/ğ/ç/ö/ü) · **gerçek tabular rakam** (yapısal ya da
`tnum`) · ayırt edilebilir `0/O` ve `1/l/I` · **eşlenik mono** · iki zeminde 10-11px okunabilirlik,
gece zemininde halation yok · değişken ağırlık tercih. Yöntem: `/impeccable typeset` turu.

**§6 — dalga sırası ve kapılar (`:117-133`):** D0 acil doğruluk → D1 jetonlar+beş rol → D2 hücre/kart
sözleşmesi+yeni IA+olay yüzeyleri → D3 fırsat yüzeyleri+modüller → **D4 yazı tipi** → D5 sertleştirme
→ D6 doğrulama. *Her dalganın kapısı:* kapsam testleri yeşil → tek otoriter suite → tek `dagit` →
canlı doğrulama. **`bolder`/`delight`/`overdrive` bu üründe KOŞULMAZ** (dopamin ve renk yasaları).

**§7 — tam kuyruk:** D3-b'nin 15 FIRSAT'ı (F1–F15) + F16 "uygulanabilir değil" gerekçesiyle kayıtta ·
D3-c modülleri.

## 3.2 Koyu tema gerekçesi — **doktrin BENİMSENDİ, KOYU TUVAL BENİMSENMEDİ**

Bu, envanterin en çok yanlış anlaşılabilecek maddesi. Ayrıştırma:

| Katman | Statü | Çapa |
|---|---|---|
| **Kontrol-odası doktrini** (HP-HMI / ISA-101 / EEMUA 191 / Airbus dark-cockpit / Few-Tufte) | **BENİMSENDİ** — WP8-B'nin kanıt tabanı | `ROADMAP.md:1779`; `ROADMAP.md:1819` "WP-P = gereksinim/doktrin … = WP-UX D6 kabul çıtası" |
| Doktrinin **renk-rolü mimarisi** | **TAM BENİMSENDİ** | `DESIGN.md:553-555` |
| Doktrinin **"renk = anormallik, normal durum renksizdir"** ilkesi | **BENİMSENDİ** | `deploy/HANDBOOK-PLAN.md:393`; `docs/UIUX-WORKORDER.md:15` ("Ekranın ~%90'ı nötr kalır"); `docs/kontrast-denetimi.md:617` |
| Doktrinin **alarm bütçesi** (EEMUA 80/15/5, <10/10dk, <10 duran alarm) | **BENİMSENDİ ve CANLI** | `ROADMAP.md:1785-1786`; `PRODUCT.md:92`; `app.js:3559` |
| Doktrinin **Level-1 toplama**sı (sessiz hat) | **BENİMSENDİ ve CANLI** | `app.js:3157` "ISA-101/HP-HMI Level-1; klinik alarm literatürüyle aynı bulgu"; `ROADMAP.md:1782-1784` (ASM 5× tespit kanıtı) |
| Doktrinin **KOYU TUVALİ** (dark-only canvas) | ❌ **BENİMSENMEDİ — beyanlı sapma #3** | `DESIGN.md:552-555`: *"The brief assumes a dark-only canvas; the **binding decision (2026-07-31, operator)** is two grounds with daylight as default and night as a low-light shift choice."* |
| Doktrinin **0/2px radius'u** | ❌ **BENİMSENMEDİ — beyanlı sapma #1** | `DESIGN.md:545-548`: *"The brief's 0/2px belongs to an ISA-101 canvas Meridian did not adopt."* |
| "Koyu tema daha iyi okunur" iddiası | ❌ **ÇÜRÜTÜLDÜ** | `deploy/HANDBOOK-PLAN.md:463-472` (**[ZAYIF — ve yönü TERS]**): halation kaynağı hakemli değil; Piepenbrock 2013/14 pozitif polarite lehine. **Hüküm:** koyu tema eklenir ama gerekçesi belgede **"24/7 düşük-ışık ergonomisi"** yazılır, "daha iyi okunur" DEĞİL; açık tema varsayılan kalır |

### *The Polarity-Honesty Rule* — kanonik gerekçe (`DESIGN.md:440-448`)

Gece zemini **24/7 düşük-ışık ergonomisi** içindir, okunabilirlik için değil. Kanıt ters yönde:
Piepenbrock ve ark. (*Ergonomics*, 2013/2014) **pozitif polariteyi** (açık zeminde koyu metin)
okuma hızı ve doğruluğunda üstün buldu; en çok alıntılanan halation kaynağı (Harrison, UBC)
hakemli değil. Yetişkinlerin ~**%40-47**'sinde bir miktar astigmatizm var. Gündüz zemini varsayılan
ve okuma-performansı tercihidir; gece zemini karanlık odada çalışılan vardiya için ortam-konfor
tercihidir, anahtar operatörün. Halation bildirilirse tepki metin luminansını `#cccccc`'ye indirip
ağırlığı artırmaktır — "karanlık daha iyi okunur" savunmasına geçmek değil.

Aynı hüküm üç yerde: `deploy/HANDBOOK-PLAN.md:468-472` (kararın alındığı yer, §H6) ·
`meridian/web/theme.js:54-59` (koddaki uygulama — sistem tercihi yalnız **ilk ziyarette tohum**,
operatörün seçimi işletim sistemini yener) · `DESIGN.md:552-555` (bağlayıcı sapma #3).

> **Kavram uyarısı:** `"light-first"` / `"dark-first"` / `"control room"` terimleri repoda
> **BULUNAMADI** (`grep -rniE` repo geneli = 0 eşleşme). Depo bunu **"iki zemin + gündüz varsayılan"**
> ve **"kontrol-odası doktrini"** olarak adlandırıyor.

## 3.3 "Operatör onaylı BAĞLAYICI" kararların tam listesi

| Karar | Sınıf | Çapa |
|---|---|---|
| **İki zemin, gündüz varsayılan** | **BAĞLAYICI — operatör, 2026-07-31** | `DESIGN.md:552-555` |
| **Geometri iki zeminde birebir aynı** | **BAĞLAYICI** | `DESIGN.md:546` ("by binding decision") |
| **Renk = ölçüm/para** | **operatörün bağlayıcı tercihi** | `deploy/HANDBOOK-PLAN.md:396` |
| **Yeniden-tasarım kapsamı: hiçbir UI öğesi muaf değil** (yeri ve biçimi dahil) | **operatör mandası, bağlayıcı, 2026-08-06** | `DESIGN.md:481-487`; `docs/BASELINE-2026-08-06.md:19` |
| **`docs/TASARIM-YONU-2026-08-07.md` yönü** | **operatör onaylı, BAĞLAYICI** | `ROADMAP.md:1707`; belge `:3` |
| **Bağlayıcı IA = TASARIM-YONU §3** | bağlayıcı | `docs/UIUX-S2R-REDESIGN.md:335` |
| **Bütün modüller yazılır** | operatör kararı | `TASARIM-YONU:78,95` |
| **Koyu tema eklenir; gerekçesi 24/7 düşük-ışık** | operatör kararı (§H6) | `deploy/HANDBOOK-PLAN.md:468` |
| **P9 kontrast turu / P6 gündüz beyazının kaldırılması** | operatör onaylı | `docs/kontrast-denetimi.md:8,435,461,641` |
| **`--red`in en kötü gerçek zemini** | bağlayıcı kısıt (paletin kendisi) | `docs/kontrast-denetimi.md:75,675` |
| **Geist EMEKLİ / font değişimi AÇIK** | operatör kararı — ama *"Geist KORUNUR" bir YASA DEĞİL* | `ROADMAP.md:1790-1792`; `DESIGN.md:567-568` |

**Bağlayıcı OLMAYAN / açıkça çürütülmüş:** "Geist korunur" (`ROADMAP.md:1790-1792`) ·
dark-mode okunabilirlik iddiası (`deploy/HANDBOOK-PLAN.md:463-467`) · APCA-birincil (`DESIGN.md:450-454`) ·
Inter önerisi (2026-08-01'de reddedildi — ama 2026-08-06 düzeltmesiyle *font kapısı yeniden açıldı*).

## 3.4 WP8 ailesi ve WP8-B kabul çıtası

`ROADMAP.md` WP8 gövdesi **satır 1702–1843**.

| Alt paket | Satır | Nedir |
|---|---|---|
| **WP8** | `:1702` | "Pano ve Operatör 🟡" — WP-UX + WP-P + Ö-3 birleşimi. Kapsam (`:1704-1705`): *"Operatörün gördüğü yüzeyin kendisi (WP-UX = icra) ve o yüzeyin kabul çıtası (WP-P = kontrol-odası doktrini) — ikisi ayrı rol, tek cephe."* |
| **WP8-A** | `:1707-1777` | Yeniden-tasarım programı (D0–D6 dalgaları + D3-b/D3-c kalanları) |
| **WP8-B** | `:1779-1821` | **Kontrol-odası doktrini / kabul çıtası** (aşağıda) |
| **WP8-C** | `:1823-1828` | F8 pano durum-sözlüğü; boyut M, öncelik orta |
| **WP8-D** | `:1831-1843` | §4 boşaltması (2026-08-23): *"44. RENK ROL-SIZINTISININ ÖLÇÜLMEMİŞ İKİNCİ EVİ"* — app.js SVG/inline stillerinde **33 ham değer-katmanı jetonu**; §4 çivisi yalnız `index.html` CSS'ini tarıyor |

> **Ölçüm notu:** WP8-D "33" diyor; bu turun bağımsız sayımı **53** (`var(--green)` 19 + `var(--red)` 22 +
> `var(--amber)` 12). Fark muhtemelen sayım kapsamından (`--violet`/`--tx2`/`--accent` dahil mi?) geliyor.
> **Hangi sayımın doğru olduğu bu turda ÇÖZÜLMEDİ** — ölçüm betiği (`research/.../tara_emisyon.py`) okunmadı.

### WP8-B gövdesi (`:1779-1821`)

**Başlık (`:1779`):** *Kontrol-odası doktrini / kabul çıtası — eski WP-P gövdesi; 2026-08-01 UI el
kitabı, gerçekle çarpıştırılmış; kontrol-odası + finans-izleme kanıt tabanı:
**HP-HMI/ISA-101, Airbus dark-cockpit, EEMUA 191, Few/Tufte**.*

| Md. | Satır | Durum | Kabul çıtası maddesi |
|---|---|---|---|
| ZATEN VAR | `:1780-1781` | — | tabular-nums (19 kullanım) · dürüstlük-UI (None≠0 = YASA, provenance rozetleri, sermaye-köken, nabız-bayat beyanı) · **koyu tema** · CSP script-src-self · yoğun-uzman düzeni |
| **P1** Sessiz-Hat | `:1782-1784` | ✅ CANLI (2026-08-01) | 17 bekçi + kilitler + tazelik TEK toplanmış şeritte; sağlıklı = "17/17" sönük tek özet; SAPMADA segment açılır; **renk yalnız anomalide** (ASM 5× tespit kanıtı) |
| **P2** Alarm bütçesi | `:1785-1786` | ✅ CANLI | **EEMUA 80/15/5** + <10/10dk tepe + <10 duran-alarm canlı gösterge; taşkın-toplama |
| **P3** Gauge yasağı | `:1787-1788` | ✅ | 2 gauge → bullet-graph + gömülü-trend + beklenen-aralık bandı (Few spesifikasyonu; tek-hue yoğunluk aralıkları) |
| **P4** Tipografi | `:1789-1795` | ✅ (slashed-zero ölçülüp gereksiz) | slashed-zero + sağa-hizalı sabit ondalık taraması. **DÜZELTME 2026-08-06 (operatör): "Geist KORUNUR" bir YASA DEĞİL.** Değişmeyen: jeton sözlüğü tekliği · **iki-zemin** · geometri/ölçek/gölgesizlik · işlevsel çıta (kendi-barındırma · açık lisans · tam Türkçe aksan · gerçek tabular · eşlenik mono · **iki zeminde küçük-punto okunabilirlik/halation**) |
| **P5** Belirsizlik | `:1796-1797` | ✅ (renksiz kanal) | onarım-dolgu/imputation hücrelerinde belirsizlik-görseli + bayatlık-solması standardı (Sarma/Kay) |
| **P6** Zemin | `:1798-1800` | ✅ TAM (gündüz turu 2026-08-02) | 9 yüzey tek-katsayı, **sıfır saf beyaz**; 148-çift yeniden-ölçüm, 0 hüküm değişimi; `#000`/`#FFF` → koyu-gri zemin + kırık-beyaz metin (halation); **WCAG 2.2 AA UYUMLULUK STANDARDI KALIR** (APCA yalnız tasarım-yardımcısı) |
| **P7** ⌘K paleti | `:1801-1802` | ✅ CANLI | 933 satır, 25+7 komut, iki-adım onay; tek eylem yüzeyi; kilit/nav/filtre; kısayol-ipuçları; CSP-self uyumlu |
| **P9** | `:1803` | ✅ (2026-08-02) | kapsama ısı-matrisi (7×6, None-haritası) + tek-hue sequential + CVD-güvenli diverging; jetonlu, AA-ölçülü |
| **P10** Hareket | `:1804-1805` | ✅ | `prefers-reduced-motion` + ≤300ms puls YALNIZ-anomali; skeleton sınırlaması kural olarak |
| RED/UYARLANDI | `:1806-1808` | — | APCA-birincil **RED** · Inter **RED** · skeleton yaygınlaştırma **RED** (Viget karşı-kanıtı) · ARIA-live genişletme **DAR** (yalnız kritik alarm/kilit) · Doherty 400ms → Nielsen 0.1/1/10 esas · P8 confirmed-state zaten mimaride (E1/mutabakat) |
| KEŞİF | `:1809-1820` | P1-P10 KAPALI | P-A borcu (RUNBOOK "henüz yazılmadı") **✅ KAPANDI** (2026-08-13). **"WP8-B artık BORÇSUZ."** Sınır beyanı: kapanış tek `grep` sayımına dayanıyor. **İkinci rol: WP-P ≠ WP-UX** — WP-P doktrindir ve **WP-UX D6 kabul çıtasıdır**; WP-P yüzey işi YENİDEN AÇILMAZ |
| **KALAN** | `:1821` | açık | 15 bekçi mekanizması + `halt_learning` (ayrı tur). *[2026-08-23 notu: "15" bayat — F8 ölçümü 17 bekçi]* |

**P8 gövdede ayrı madde olarak YOK** — yalnız RED/UYARLANDI satırında "zaten mimaride" diye geçiyor (`:1808`).

**Redesign için sonucu:** WP8-B, WP8-A'nın **D6 doğrulama kapısıdır**. Yeni bir görsel dil, D6'da
P1–P10'un tamamına karşı yeniden sınanır — yani Dub eşlemesi bu on maddeyi tek tek karşılamak
zorundadır, özellikle **P1 (renk yalnız anomalide)**, **P3 (gauge yasağı)** ve **P6 (saf beyaz/siyah yok)**.

## 3.5 Ölçülmüş taban (BASELINE-2026-08-06 · PATTERN-ETUDU-2026-08-06)

**`docs/BASELINE-2026-08-06.md` (678 satır) — redesign'i ilgilendiren rakamlar:**

- Yer-gerçeği (`:7-10`): o gün toplam **11.789 satır** web yüzeyi (`app.js` 7.511 → **bugün 11.109**).
- **25 `T`-kimlikli bulgu**, 4'ü ciddiyet-4 (§D `:428+`).
- Renk-rolü ölçümü (`:341-349`): kromatik değer taşıyan **üç** jeton; `--violet`/`--blue` jeton olarak
  var ama kromatik DEĞİL. **Hüküm: "3 kromatik kanal var, 5 rol dolduruluyor."**
- Rol-sızıntı (`:636-640`): `--green` 14 bağlanma/≥4 rol · `--amber` 21/≥5 · `--red` 24/≥5 ·
  **164 koşulsuz `pos`/`neg`/`warn` emisyonu**.
- Mod kroması: **ayrılmış kanal YOK** (`:401-411`) — D1 turunda açıldı.
- Görsel envanter (`:551-566`): `class="card…"` 81 (app.js) → **bugün 107** · `.srow` 171 → **bugün 194**.
- Silme adayları (`:594-610`): N2 **`--blue` 0 kullanım** · N3 **`--violet` 1 kullanım** ·
  N4 `landing.html` panodan 0 bağ, impeccable bulgularının **%76'sı orada** · N9 `runbook.html`in
  kendi jeton bloğu. *(Bugün ölçüldü: `var(--blue)` app.js'te 0, `var(--violet)` 1 — **hâlâ geçerli**.)*
- 6 beyanlı ÖLÇÜLEMEDİ (`:46-57`): çalışan DOM · app.js'in ürettiği DOM · satır numaraları ·
  sayfa başına çalışma-zamanı kart sayısı · bileşik zeminlerde gerçek kontrast · gerçek alarm sıklığı.

**`docs/PATTERN-ETUDU-2026-08-06.md` (738 satır):** kategori etüdü; **panonun görsel envanterini VERMEZ**
(`:23-25`, "kardeş doküman BASELINE'ın işi"). Redesign'i doğrudan bağlayan tek kısmı **B.0 — 10 elenen
desen sınıfı** (`:300-320`): R1 manuel emir girişi · R2 liderlik tablosu/gamification · R3 sosyal
kopyalama · R4 gerçek-para iması · R5 kanıt kaydını silme · **R6 gauge/donut/pie** ·
**R7 rengin tek anlam kanalı olması** (IBKR emir durumu 11 renkle kodlu — Meridian beş rol + yön
"üçüncü sinyal") · R8 paydasız ölçüm · R9 ajanın kendi düzeltmesini uygulaması · R10 elle izleme listesi.

## 3.6 ⚠ ÖLÇÜLEN SAPMA: `DESIGN.md`'nin gündüz jeton tablosu BAYAT

`DESIGN.md:190-210`'daki "Token table — both grounds" tablosu **P9 turu (2026-08-02) öncesi
değerleri taşıyor.** `meridian/web/index.html:135-147` ve `meridian/web/tokens.json` ise BİRBİRİYLE
UYUMLU. Yani belge kaynaktan ayrışmış:

| Jeton | `DESIGN.md:192-206` (gündüz) | **Gerçek** (`index.html:135-147` = `tokens.json`) | Gece |
|---|---|---|---|
| `--bg` | `#ffffff` | **`#fbf9f8`** | `#1c1a18` (uyumlu) |
| `--bg2` | `#fbfaf8` | **`#f5f4f2`** | `#232120` (uyumlu) |
| `--card` | `#f8f5f2` | **`#f2efed`** | `#262320` (uyumlu) |
| `--card-2` | `#f1ece8` | **`#ece7e3`** | `#2f2b27` (uyumlu) |
| `--raise` | `#ffffff` | **`#fbf9f8`** | `#38342f` (uyumlu) |
| `--slip` | `#f1ece8` | **`#ece7e3`** | `#2f2b27` (uyumlu) |
| `--line` | `#e7e3df` | **`#e2deda`** | `#38342f` (uyumlu) |
| `--line-2` | `#d9d4cf` | **`#d4cfca`** | `#4a453f` (uyumlu) |
| `--accent-tint` | `#f3f3f3` | **`#eeeeee`** | `#302c28` (uyumlu) |
| `--tx3` | *tabloda YOK* | `#686562` | `#95928f` |

Aynı sapma metinde de var: *The Warm Rule* (`DESIGN.md:419`) "daylight hairlines are `#e7e3df`" diyor —
gerçek `#e2deda`. **Bu bir kod hatası değil, belge borcudur:** çivi (`test_tasarim_token_v153.py:189/215`)
CSS ↔ `tokens.json` eşleşmesini denetliyor, **DESIGN.md'yi denetlemiyor.** Redesign'a girmeden önce
kapatılması gerekir; aksi hâlde tasarımcı yanlış tabandan türetir.

---

# [4] DUB-EŞLEME TASLAĞI (ÖNERİ — karar operatörün)

## 4.0 İki sistemin künyesi yan yana

| Eksen | Meridian (bugün) | Dub | Uyum |
|---|---|---|---|
| Kanvas | `#fbf9f8` sıcak kırık-beyaz (+ `#1c1a18` gece) | `#ffffff` saf beyaz | **ÇATIŞMA**: "Backgrounds are never `#000`; text is never `#FFF`" (`DESIGN.md:543`) ve P9 turu saf beyazı bilerek kaldırdı |
| Nötr sıcaklığı | SICAK (`#e2deda`, `#585450`) | SOĞUK (`#e5e5e5`, `#737373`) | **ÇATIŞMA**: *Warm Rule* (`DESIGN.md:418`) — soğuk nötr "farklı, daha soğuk bir ürün" okutur |
| Kenar felsefesi | 1px saç teli, gölge YOK (`--elev:none`) | 1px `#e5e5e5`, "border-first elevation" (1942 kullanım) | **BİREBİR UYUM** — Dub'ın en güçlü tarafı Meridian'ın zaten yasası |
| Gölge | **hiç yok** (*The Flat Rule*) | 4 kademeli gölge (subtle → lg) + 4px ring | **ÇATIŞMA**: Dub'ın gölge kademeleri alınamaz |
| Yarıçap | **tam 3**: 12/10/2px | 5: 9999/16/12/8/6px | **KISMİ**: 12px kart ORTAK; hap (9999px) Meridian'da bilerek YOK (`DESIGN.md:918-926`) |
| Aksan | **YOK** — "no interaction colour"; birincil eylem siyah hap | `#2563eb` elektrik-mavi + `#1e40af` CTA | **ÇATIŞMA**: *Money Rule* (`DESIGN.md:405`) — dekoratif/etkileşim rengi eklemek operatörün taradığı tek sinyali bozar |
| Tipografi | Recursive Sans + Recursive Mono (tek dosya, `MONO 1` ekseni), kendi-barındırma | Satoshi (display) + Inter (gövde) + Geist Mono | **KISMİ**: üç-aile modeli alınabilir ama Geist **emekli edildi** (aşırı-kullanılan yüz listesi, `DESIGN.md:568`) ve CSP dış font host'a izin vermiyor |
| Gövde boyutu | 13px (compact) baskın | 16px kanonik | **ÇATIŞMA**: yoğunluk farkı ~%23; Meridian tek uzmanın uzun vardiyası için tasarlanmış |
| Boşluk tabanı | 4px, 9 basamak | 4px, 16 basamak | **UYUM** |
| Sayfa genişliği | `.shell` **1320px** (`index.html:563`), nav 1560px (`:521`); `--max:1180px` panoda ÖLÜ | 1200px | **KISMİ**: Dub daha dar; Meridian'ın 1320px'i 208px ray + içerik için |
| Kart dolgusu | 24px (`--s6`) | 16px | Kısmi |

## 4.1 Bileşen-bazlı eşleme

| Meridian bileşeni (dosya:satır) | Dub karşılığı (`Downloads/DESIGN.md:satır`) | Doğrudan alınabilir | Koyu kanvasta türetilmeli / alınamaz |
|---|---|---|---|
| `.card` `index.html:1116` | **Dashboard Card** `:159` (white, 1px #e5e5e5, 12px, no shadow) | `--radius-cards:12px` (zaten aynı) · border-first felsefe | Zemin: `#ffffff` → `--card` kalır; kenar `#e5e5e5` → gündüz `#e2deda`, **gece `#38342f`** (soğuk `#e5e5e5`'in sıcak-koyu karşılığı; L farkı korunur) |
| `.gb-kart` `index.html:836` | **Elevated Feature Card** `:164` (16px + 4px ring) | 16px yarıçap ÖNERİ | **4px ring gölgesi ALINAMAZ** (*The Flat Rule*). Karşılık: `--card-2` tonuna çıkmak veya `--line-2` saç teli |
| `.hero` `index.html:1163` (`::before` iç çerçeve) | **Product Mockup Container** `:199` | — | Asimetrik yarıçap + 4px ring alınamaz; mevcut çift saç teli Dub'ın "floating panel"ının gölgesiz karşılığı |
| `.mcard` `index.html:1108` (sol saç teli şerit) | **Muted Alt Card** `:169` (`#fafafa`, 16px, kenarsız) | `#fafafa` → Meridian `--bg2` (`#f5f4f2`) zaten bu rol | Gece `--bg2:#232120` |
| `.tag` + `t-go/t-rv/t-no/t-vi` `index.html:1238` | **Status Badge** `:179` (mint tint + nokta + 9999px) | Tint+ikon deseni ORTAK | **9999px alınamaz** (üç-yarıçap yasası) → `--r-ctl:10px` kalır. Mint `#dcfce7` ALINAMAZ: Dub'da bu "supporting accent", Meridian'da yeşil YALNIZ sev-3 |
| `.pillc` `index.html:631` | **Pill Badge** `:154` | — | Aynı: 9999px değil 10px |
| `.dlbtn` `index.html:1290` | **Outlined Action Button** `:144` (white, #171717, 1px #e5e5e5, 8px) | Yapı birebir | 8px → Meridian 10px (`--r-ctl`). Kenar sıcak nötr |
| `.dlbtn.primary` `index.html:1294` (dolu `--accent` = `#050505`) | **Filled Dark CTA** `:139` (`#0a0a0a`/`#000000`) | **BİREBİR UYUM** — Dub'ın "primary-action-fill:#000000" ile Meridian'ın siyah hapı aynı fikir | Gece: `--accent:#d4d0cb` (ters çevrilmiş dolu) — Dub'ın koyu-dolgu idiomu koyu zeminde AÇIK dolguya döner |
| `.trow` / `.tbl` `index.html:1187,1306` | **Dashboard Table Row** `:174` (1px alt kenar, 14–16px, ferah) | Alt-kenar-yalnız satır BİREBİR | Dub'ın "16px satır yüksekliği + ferah dolgu" **ALINAMAZ**: 117 `.trow` emisyonu ve 114 sabit px kolon yoğunluk için ayarlı |
| `.sitem` `index.html:587` (3px sol şerit) | **Sidebar Nav Item** `:184` (aktif = `#dbeaff` yumuşak kromatik dolgu, 8px) | 8px yarıçap ÖNERİ | **`#dbeaff` ALINAMAZ**: kromatik dolgu ROL 1'i (yapı akromatik) kırar. Dub'ın kendi notu bile "soft chromatic fill rather than a bold left-border" diyor — Meridian bilerek TERSİNİ seçmiş |
| `.gate-in` / `.searchbox` `index.html:493,1367` (`1px solid var(--field)`) | **Input Field** `:189` (**1px `#000000` kenar** — Dub imzası) | **Fikir UYUMLU**: Meridian de girişe AYRI ve daha güçlü bir jeton (`--field`) veriyor, gerekçesi WCAG 1.4.11 | Saf siyah alınamaz; `--field` gündüz `#86817d`(3,14) gece `#7e776e`(3,18) — Dub'ın "inputs feel important" niyeti zaten karşılanmış |
| `.detay-kat` / `.gloss` `index.html:694,1397` | — (Dub'da karşılığı yok) | — | Korunur |
| `.pm-grid` matris `index.html:941` | — (Dub'da veri matrisi yok) | — | Korunur; Dub'ın hiçbir bileşeni bu yoğunluğu taşımıyor |
| `.spine` triyaj şeridi `index.html:903` | — | — | **Meridian imzası** (DESIGN.md:1104) — korunur |
| `.pdrawer` `index.html:992` | — | — | **Meridian imzası** (DESIGN.md:1127) |
| `nav` `index.html:510` | Dub top bar `:244` ("logo left, nav center, two-button cluster right, no sticky") | — | **ALINAMAZ**: Meridian'ın barı sticky + HALT/KRİZ taşıyor; "no sticky" bir denetim konsolunda kabul edilemez |
| Dub **dotted grid background** `:240` | — | — | **ALINAMAZ**: dekoratif doku; "Forbidden: … decorative" (`DESIGN.md:537`) |
| Dub **conic gradient** `:29` | — | — | **ALINAMAZ**: "Forbidden: gradients" (`DESIGN.md:537`) |

## 4.2 Doğrudan alınabilecek Dub token'ları (öneri)

| Dub token | Değer | Meridian'da nereye | Gerekçe |
|---|---|---|---|
| `--radius-cards` | 12px | `--r-card` (zaten 12px) | Değişiklik yok — teyit |
| `--spacing-*` 4px tabanı | 4→112px | `--s1..--s12` (zaten 4px tabanı) | Dub'ın 16 basamağından Meridian'ın 9'u alt küme |
| `--page-max-width` | 1200px | `.shell` 1320px | Alınması ÖNERİLMEZ: 208px ray + yoğun tablolar 1200px'te daralır; `--max` jetonunu canlandırıp 1200'e çekmek ise landing/runbook'u da değiştirir (§2.6/P5) |
| `--element-gap` | 8px | `--s2` | Aynı |
| Border-first elevation felsefesi | — | zaten yasa | Dub'ın en güçlü fikri Meridian'da zaten daha katı |
| `--font-weight-medium:500` (başlıklar medium, bold değil) | 500 | zaten uygulanıyor (`DESIGN.md:588`) | Teyit |

## 4.3 KOYU kanvasta yeniden türetilmesi gereken Dub değerleri (öneri — ölçülmemiş)

**UYARI:** aşağıdaki koyu karşılıklar **ÖNERİDİR ve ÖLÇÜLMEMİŞTİR.** *The Tint-Direction Rule*
(`DESIGN.md:426`) uyarınca hiçbir gece değeri gündüz değerinin ters çevrilmesiyle türetilemez;
her biri kendi bileşik zemininde yeniden ölçülmek zorundadır.

| Dub açık değer | Rolü | Önerilen Meridian gündüz | Önerilen Meridian gece | Neden ters çevirme olmaz |
|---|---|---|---|---|
| `#e5e5e5` (Ash — hairline) | kart/giriş/ayraç kenarı | `--line:#e2deda` (mevcut) | `--line:#38342f` (mevcut) | Soğuk→sıcak dönüşüm; ayrıca gecede saç teli zeminden AÇILARAK ayrışır |
| `#d4d4d4` (Smoke — güçlü kenar) | vurgu kabı, ikincil düğme | `--line-2:#d4cfca` (mevcut) | `--line-2:#4a453f` (mevcut) | aynı |
| `#f5f5f5` (Paper Mist) | alt yüzey | `--bg2:#f5f4f2` (mevcut) | `--bg2:#232120` (mevcut) | Gündüz AŞAĞI, gece YUKARI hareket eder (`DESIGN.md:895`) |
| `#ffffff` (Canvas) | sayfa zemini | `--bg:#fbf9f8` | `--bg:#1c1a18` | Saf beyaz P9 turunda bilerek düşürüldü (halation/parlama) |
| `#171717` (Charcoal — gövde metni) | metin | `--tx:#050505` | `--tx:#d4d0cb` | Meridian gündüzde DAHA koyu; gecede saf beyaz değil sıcak açık |
| `#737373` (Fog — placeholder) | ikincil | `--tx2:#585450` | `--tx2:#b0a9a0` | — |
| `#2563eb` (Electric Blue — aksan) | link, aktif hâl, "voltage" | **ALINMASI ÖNERİLMEZ** — bir kanal açar | — | *Money Rule*: dekoratif/etkileşim rengi eklemek şiddet ve yön kanallarıyla dikkat için yarışır. Alınacaksa: **ROL 6** olarak ilan edilmeli, hue'su şiddet (24/77/154°), mod (310°) ve veri-ölçek (250/84°) bantlarının DIŞINDA olmalı — mavi 250°'ye çok yakın (`--dv-n*` kutbu), yani çatışır |
| `#1e40af` (Deep Sapphire — CTA) | tek birincil eylem | `--accent:#050505` (siyah hap, mevcut) | `--accent:#d4d0cb` | Dub'ın kendi `primary-action-fill` değeri zaten `#000000`; Meridian bu yolu seçmiş |
| `#dcfce7` (Soft Mint) | rozet tinti | **ALINMAZ** | — | Yeşil YALNIZ sev-3; süs tinti rol sızıntısıdır |
| `9999px` (pill) | tag/badge | **ALINMAZ** | — | Üç-yarıçap yasası; `--r-pill` bir kez tanımlanıp kullanılmadığı için silindi |
| `--shadow-*` (6 kademe) | yükseklik | **ALINMAZ** | — | *The Flat Rule*: blur'lu hiçbir gölge, hiçbir temada |
| Inter/Satoshi | tipografi | Recursive Sans (mevcut) | aynı | Satoshi/Inter self-host + tam Türkçe aksan + gerçek tabular + eşlenik mono çıtasından geçmeli (`TASARIM-YONU §5`); Recursive bu çıtayı ölçümle geçmiş durumda. **Geçirilecekse `/impeccable typeset` turu şart** |

## 4.4 Dub'dan alınabilecek ÜÇ FİKİR (token değil, gramer)

1. **Border-first açıklığı ve nefes** — Dub'ın kartları 16px dolgu + ferah satırla "printed
   document clarity" üretiyor. Meridian'ın 24px kart dolgusu zaten daha ferah; asıl kazanç
   **`.trow` yoğunluğunda değil, kart İÇİ hiyerarşisinde**: bugün `.srow` 194 kez basılıyor ve
   hepsi aynı ağırlıkta.
2. **Tek "voltage" anı** — Dub tüm sayfayı monokrom tutup tek aksanı hak eden yere koyuyor.
   Meridian'ın karşılığı ZATEN var (renk = para) ama bugün **11 koşulsuz DEĞER-jetonu emisyonu**
   (bkz. §5-R2) bu disiplini satır içi stillerde deliyor. Dub eşlemesi bir renk değişikliği değil,
   **mevcut kuralın satır-içi stillere de uygulanması** olarak alınabilir.
3. **Yarıçap sözlüğünün katılığı** — Dub "Don't use radii outside the defined vocabulary" diyor;
   Meridian'ın üç-yarıçap yasası daha katı. Bu, redesign'da bir teyit maddesi olarak kullanılabilir.

---

# [5] RİSK LİSTESİ — redesign'in kırma ihtimali en yüksek 10 nokta

Sıralama: **kırılma olasılığı × onarım maliyeti**. "Çivi" sütunu, kırılmanın *sessiz* mi *testte
kırmızı* mı olacağını söyler — sessiz olanlar daha tehlikelidir.

| # | Risk | Kanıt (dosya:satır) | Çivi (kırılma nasıl görünür) | Görsel kayıp | Anlam kaybı |
|---|---|---|---|---|---|
| **R1** | **Izgara mimarisi terk edilemez.** app.js'te 114 satır-içi `grid-template-columns` ve ~304 sabit px kolon var; test **≥100 ızgara ve ≥300 sabit px** olmasını ŞART koşuyor | ölçüm: `grep -oE 'grid-template-columns:[^";]*' app.js` = 114 · gerekçe `app.js:6243-6254` (340px diz noktası, %39→%63) | ⚠ **KIRMIZI** — `tests/test_yerlesim_tasma_v205.py:482`, `:453`, `:350` | Flexbox/`auto-fit`'e geçiş yasak | Sütun hizası "yoğun uzman defteri"nin tek okuma dayanağı (`app.js:6255-6257`) |
| **R2** | **app.js rol katmanını HİÇ kullanmıyor**: 53 DEĞER-jetonu, **0** ROL jetonu; 11'i koşulsuz. Redesign rol jetonlarını yeniden değerlerse bu 53 yer ESKİ anlamda kalır | `app.js:533,1444,2679,2703,2723,3678,3716,3731,3734,3999,4025,4885-4886,8548-8550,8616-8617,8645,8771,8780,8787,9344,9367-9368,9511,9543,9738` · ROADMAP'in kendi kaydı: **WP8-D** `ROADMAP.md:1831-1843` ("33 ham değer-katmanı jetonu") | 🔇 **SESSİZ** — `tests/test_renk_rolleri_v197.py:367` yalnız `index.html` CSS'ini tarıyor; satır-içi stiller kapının DIŞINDA. Üstelik `tests/test_pano_mudahale_satiri_v194.py:151` bazılarını satır içi kalmaya ZORLUYOR | Renk anlamı kayar | **Şiddet kanalına sızıntı** — D1'in kapattığı kusur sınıfının ikinci evi |
| **R3** | **Kart sayısı RATCHET.** 101 ölçülen + 25 kapaklı taban; azaltma testi kırar | `tests/test_kart_sozlesmesi_v198.py:114` (`KART_TABANI`), `:138` (`KAPAK_TABANI`), `:382`, `:391` | ⚠ **KIRMIZI** | Kart konsolidasyonu (Dub'ın "fewer, bigger cards" grameri) bloklu | Taban beyanla düşürülmeden yüzey birleştirilemez |
| **R4** | **Tablo satırlarında ellipsis/nowrap yasak** (`.trow` kapsamlı kurallarda). Dub'ın kompakt tablo satırı uzun adları kırpar; Meridian sarar | `tests/test_yerlesim_tasma_v205.py:335` (regex `(\.trow[^{;]*)\{`), `:419` · kural `index.html:1219` (`.trow > *{min-width:0;overflow-wrap:anywhere}`) | ⚠ **KIRMIZI** — ama yalnız `.trow` ailesinde; global değil (§2.5/Y5) | Kompakt tek-satır tablo grameri alınamaz | Kırpılan ad **günlükte greplenemez** (`app.js:5809-5812`) |
| **R5** | **`.chain` özgüllük tuzağı** ve genel kap-vs-rol sıralaması. Aynı özgüllükte (0,1,0) kap kazanır ve kural EKRANDA ÖLÜR | `index.html:1245-1250` ("ihlal, uyumlu satırla aynı griydi"); `.pm-yield`'da bir kez yaşanmış | 🔇/⚠ karışık — `tests/test_renk_rolleri_v197.py:443` yalnız `.{kap}.{rol}{` kuralının VARLIĞINI arıyor | Renk hiç görünmez | **En sinsi sınıf**: kaynakta kural canlı, ekranda ölü — hiçbir görsel gözden geçirme yakalamaz |
| **R6** | **Hücre dilinin üç kapısı** (`deger` · payda-beyanlı `oran` · ≥20 karakterli `meta`). Yeni kart tasarımı bu üçünü kuramazsa kart katlanmaz ve `_KAT_OZETSIZ`e düşer | `app.js:1952-1958`, `:1975`, `:2025-2033` · `hucreGovde()` `:1964` | ⚠ **KIRMIZI** — `tests/test_kart_sozlesmesi_v198.py:229,238,256,321` (assert :427) | Kapak kaybı | "Ölçtük, sıfır çıktı" ile "ölçemedik" aynı piksele düşerse **pano bilgi değil izlenim taşır** |
| **R7** | **Gölge yasağı + üç-yarıçap.** `--elev:none` her iki temada; Dub'ın 6 gölge kademesi ve 9999px hapı doğrudan çatışıyor | `index.html:281`, `:277`; `DESIGN.md:891-912`, `:916-926` | Gölge ⚠ **KIRMIZI** (`tests/test_tasarim_token_v153.py:388`, assert :420-421). **Yarıçap 🔇 SESSİZ** — üç-yarıçap yasası DESIGN.md'de YAZILI ama **testte çivili DEĞİL** (§2.11) | Dub'ın "floating panel" hissi alınamaz | Gölge bu sistemde "bug okur" |
| **R8** | **Yazı tipi = yerleşim kararı.** Font değişirse `tnum.json`/`measurements.json` metrikleri, 340px diz noktası, bindirme testi ve `font-display:block` gerekçesi birden yeniden ölçülür | `index.html:88-102`, `:104-113` · metrik kaynağı `tests/test_yerlesim_tasma_v205.py:102-106` · yapısal tabular `tests/test_yazitipi_v201.py:331` (`rakam_advance == [600]`) · çıta `TASARIM-YONU §5` | ⚠ **KIRMIZI** (üç ayrı test) | Soğuk önbellekte 3sn görünmez metin | **Takas anında tabular sütun YATAY KAYAR** — okunmakta olan sütunun kayması boş sütundan kötüdür |
| **R9** | **Mod bandı yapısaldır, rozet değil.** `body[data-mod]::before` sayfanın üst kenarında; `olculemedi` KESİK desen. Redesign'da "üstteki ince çizgi"yi temizlemek çok kolay | `index.html:1454-1462` · `app.js:483-494` (`MOD_OLCULEMEDI`) | ⚠ **KIRMIZI** — `tests/test_renk_rolleri_v197.py:323` üç seçiciyi de birebir arıyor | Üst kenar bandı "gereksiz" görünür | **"Kâğıt mı canlı mı" en pahalı kaza sınıfı** (`DESIGN.md:534`) |
| **R10** | **Dürüstlük metni GÖRSEL DEĞİL, YAPISAL.** 291 "ÖLÇÜLEMEDİ", 272 `.hint`, 194 `.srow` — sadeleştirme turunun ilk hedefi bunlar olur; ama **YASA 6 bir alanı UI'dan kaldırmayı yasaklıyor** | ölçüm: `grep -c "ÖLÇÜLEMEDİ\|ölçülemedi" app.js` = 291 · `satirKoru()` `app.js:1588-1601` · `_dolduruldu()` `app.js:3117` | ⚠ **KIRMIZI** — `tests/test_wp2d_pano_beyani_v246.py:327`, `tests/test_acil_dogruluk_v196.py:439`, `tests/test_gorunurluk_v219.py:483,501` | Sayfa "temizlenir" | **Uydurma yasağının taşıyıcısı silinir**; YASA 6 tersine döner |

### R11–R16 · sıralamaya girmeyen ama kayda geçen riskler

| # | Risk | Kanıt | Not |
|---|---|---|---|
| **R11** | **`DESIGN.md`'nin gündüz jeton tablosu BAYAT** (P9 öncesi değerler) — tasarımcı yanlış tabandan türetir | §3.6 tablosu; `DESIGN.md:190-210` vs `index.html:135-147` = `tokens.json` | Çivi CSS↔`tokens.json`'ı denetliyor, **DESIGN.md'yi denetlemiyor**. Redesign'a girmeden önce kapatılmalı |
| **R12** | **Jeton ADLARI sözleşme.** `--violet`, `--blue`, `--slip` tarihsel adlar; app.js DOM'u çalışma anında üretiyor | `index.html:132-134` ("TOKEN ADLARI DEĞİŞMEZ"), `:156-163` | Ad değişirse ikinci tema SESSİZCE yanlış renkle çalışır (`index.html:381-383` bunun bir kez yaşandığını yazıyor) |
| **R13** | **Beş fonksiyon ADA BAĞLI taranıyor** — refactor/parçalama testi kırar | `tests/test_wpux_d3b_v229.py:384` (`esikHal, esikSatiri, firsatKagitCanli, firsatSapmaKoku, firsatEsikPaneli`) · `tests/test_wpux_d3b_f5_v230.py:242` (`firsatAlarmTaksonomi`) · `tests/test_ayna_rozeti_v239.py:100` (`aynaRozeti`) · `tests/test_acil_dogruluk_v196.py:219` (`modJetonu`) | Redesign kodu yeniden düzenleyemez, yalnız **çıktısını** değiştirebilir |
| **R14** | **Altı betik dosyası var olmaya devam etmeli** — app.js'i modüllere ayırmak yasak | `tests/test_guvenlik_basliklari_v203.py:60` (`BETIK_YUZEYLER`) | 11.109 satırlık app.js bölünemez |
| **R15** | **Dört HTML yüzeyi jeton-birliği içinde** — biri değişirse dördü değişir | `tests/test_jeton_birligi_v208.py:165,176,186,204,216` | `workflow.html` EMEKLİ edilse bile (TASARIM-YONU §1) bu teste bağlı |
| **R16** | **Şekil ayrımı BİLGİ taşıyor**: `.spine::before` 8×8 **kare** · `.dot` 6×6 **daire** · `.livedot`/`.ld` `radius:0` **kare** | `index.html:908`, `:531`, `:1176`, `:1489` | 🔇 SESSİZ. Hepsini Dub'ın hap/daire grameriyle tekleştirmek üç göstergeyi tek şekle çökertir |

### Ek riskler (mekanik tuzaklar)

- **`.acct .r b` `white-space:nowrap;flex:none`** — kenar şeridinde değerin yanına eklenen her
  kelime satırı genişletir ve etiketi taşırır; `sermayeKokenSatiri()` bu yüzden ibareyi AYRI
  satıra indiriyor (`app.js:770-773`).
- **`.nav-in` sarma yasağı** — HALT'ın sabit bir evi olmalı (1280×720'de bar iki satıra sarıyor ve
  HALT ikinci satırın ortasına düşüyordu); sıkışan taraf HUD, o zaten kaydırıcı (`index.html:513-517`).
- **`--navh` JS ile ölçülür** (`syncNavHeight()` `app.js:574`); sabit sayı dar ekranda başlığı
  barın altına sokar.
- **`.pm-cell` `min-height:106px`** ve **`.bullet` 212px sabit eksen** — ölçülmüş, seçilmemiş
  değerler (`app.js:3767-3769`).
