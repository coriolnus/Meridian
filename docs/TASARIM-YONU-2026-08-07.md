# TASARIM YÖNÜ — Meridian yeniden-tasarımı (2026-08-07)

**Statü:** operatör onaylı (dört karar, 2026-08-07) · **bağlayıcı** — sonraki her dalga buna dayanır.
**Girdiler:** `docs/BASELINE-2026-08-06.md` (bugün ne var) · `docs/PATTERN-ETUDU-2026-08-06.md`
(kategoride ne olabilir) · `docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md` (ölçülmüş adım sayıları) ·
`DESIGN.md` §Design rules (kapsam mandası, beş renk rolü, üç sapma) · operatörün ana brief'i
(trading-platform brief — kategori değişmez, tasarım dili girdi).

---

## 1. Operatör kararları ve bunlardan türeyen hükümler

| # | Karar | Türeyen hüküm |
|---|---|---|
| 1 | Yan yüzeyler: "mantıklı olanı yap" | Aşağıda üç ayrı hüküm — biri korunur, ikisi emekli |
| 2 | **Bütün modüller yazılır** | C2'nin altı adayı da programa girer (biri dış-kaynak kararına bağlı) |
| 3 | Yazı tipi: **Impeccable önerisiyle git** | Geist emekli; aday seçimi ölçümle (aşağıda çıta) |
| 4 | Yeni bilgi mimarisi **onaylandı** | §3 bağlayıcı |

### Yan yüzeylerin kaderi (Rol-1 hükmü, gerekçeli)

- **`landing.html` KALIR ve onarılır.** Ürünün tek dışa-dönük yüzeyi; panodan bağ almaması bir
  kusur değil, doğası. Ölçülen kusuru bir sızıntı: `:203`/`:252` `color:#fff` sabiti gece
  zemininde **1,53:1** — dönüştürülmemişlik değil, dönüşümün kaçağı. Ayrı brief'le (Persuade
  kipi) ele alınır; ürün-içi Operate kurallarıyla karıştırılmaz.
- **`workflow.html` EMEKLİ.** Statik bir boru-hattı resmi; C1#4'ün **canlı zaman çizelgesi**
  aynı soruyu gerçek veriyle cevaplıyor. Resmi canlı enstrümanla değiştirmek net kazanç.
  İçeriği zaman çizelgesi yüzeyine taşınır, sonra dosya düşer.
- **`runbook.html` EMİLİR.** Bugün dördüncü, dönüştürülmemiş görsel dünya (Roboto, kendi
  jetonları, ölçülen 3,50:1) ve alarmdan teşhise giden yol panoyu terk ediyor (denetim B14).
  Runbook içeriği **olay yüzeylerinin içine** girer; dördüncü dünya ölür, bağlam sıçraması biter.

---

## 2. Renk rolü mimarisi — beş rol, üç kanal yetmiyor

**Ölçülen bugün:** `--green` ≥4 rol · `--amber` ≥5 · `--red` ≥5 · mod-kroması için ayrılmış
kanal **yok** · **164 koşulsuz** `pos`/`neg`/`warn` emisyonu.

| Rol | Ne taşır | Kural |
|---|---|---|
| 1 · Yapı | zemin, panel, ayraç, metin | akromatik; hue yok |
| 2 · Şiddet | alarm/risk seviyesi (P1/P2/P3) | üç hue, **başka hiçbir şey için kullanılamaz** |
| 3 · Yön | K/Z işareti | düşük kroma, CVD-güvenli; **üçüncü sinyal** (işaret ve ok önce gelir) |
| 4 · **Mod** | kâğıt / canlı | **kendi kanalı**; yapısal, köşe rozeti değil; başka hiçbir şey kullanamaz |
| 5 · Veri ölçekleri | kapsama matrisi, sapma | tek-hue sequential + CVD-güvenli diverging (bugün UYUYOR) |

**Sızıntı olarak kapatılacaklar (baseline'dan):** stop fiyatı koşulsuz kırmızı / hedef koşulsuz
yeşil (fiyat seviyesi sonuç değildir) · açık risk koşulsuz amber · "KEŞİF MODU" amber'de
(mod → şiddet sızıntısı) · "ince örneklem" amber'de (veri güveni → şiddet sızıntısı).
Veri güveni ve mod kendi kanallarını alır; şiddet kanalı yalnız şiddet taşır.

---

## 3. Yeni bilgi mimarisi — beş yüzey, işe göre

Sayfa yapısı işten türetildi (widget'tan değil) ve C1'in "veri var ama gösterilmiyor" işleri
doğrudan içine yerleştirildi.

| # | Yüzey | Cevapladığı soru | İçine giren işler |
|---|---|---|---|
| ① | **Bugün** | "Sağlıklı mı, dün gece ne oldu, benden ne bekleniyor?" | sessiz-hat (yeniden) · triyaj şeridi · son döngü · kitap · alarm bütçesi — eylemler **yerinde** çekmeceyle |
| ② | **Karar** | "Ne önerildi, neden geçti/geçmedi, ne oldu?" | adaylar → kapılar → planlar → onay → **emir yaşam-döngüsü** (C1#2) · **reddedilen kararların karnesi** (C1#1) · denetim izi (C1#7) · **"bugün neden hiçbir şey olmadı"** (C1#8) · çıkış-nedeni kırılımı (C1#9) |
| ③ | **Sağlık** | "Veri ve işleyiş güvenilir mi, bir şey bozulduysa ne yapmalıyım?" | besleme/kapsama/mutabakat · bütünlük dedektörleri · alarmlar · **canlı zaman çizelgesi** (C1#4, workflow.html'in halefi) · **olay yüzeyleri** (runbook içeride) |
| ④ | **Öğrenme** | "Ajan öğreniyor mu, neyi düzeltti, neyi bozdu, kaça mal oldu?" | karne · sürümler · **rollback sicili** (C1#5) · **regresyon kırılımı** (C1#6) · **skor olgunlaşması** (C1#10) · gölge/skiller · **gece maliyet karnesi** (C1#3) · ajan telemetrisi (C2-S) |
| ⑤ | **Kilitler** | "Ajanın yetkisi ne, sınırları nerede, nasıl durdururum?" | goal/bounds görünürlüğü · otonomi merdiveni · müdahale · yapılandırma |

**Olay yüzeyleri (Tier-4):** sayfa değil — herhangi bir alarmdan açılan tam çekmece. Her biri
tek yerde: *ne oldu · değerler şimdi ne · runbook adımları · mevcut eylemler.* `runbook.html`
bunların içine emilir.

**Değişmeyenler (ürün yasası, tasarım değil):** tek emir-yolu · dürüstlük yasaları
(ÖLÇÜLEMEDİ≠0, paydasız çubuk yok, uydurma yok) · iki zemin + gündüz varsayılan · dopamin
yasağı · CSP-self · Türkçe.

---

## 4. Modüller — hepsi yazılır (operatör kararı)

| Boy | Modül | Ne üretir | Not |
|---|---|---|---|
| S | Ajan çağrı telemetrisi | çağrı başına süre/deneme/araç — ölçüm anında yazılır, türetilemez | ④'ü besler |
| M | Ham ajan-izi defteri | bugünkü 200-karakter maskeli özetin yerine tam iz (sır-maskeli) | teşhis |
| M | Vaka sabitleme | canlı arıza → dondurulmuş fikstür | regresyon çivisi |
| L | İkinci motor diferansiyeli | LEAN (Apache-2.0) ile emir-düzeyi ayrışma | **QC hesabı gerekmez**; hüküm değişirse kart |
| L | Delist-dahil evren arşivi | yerel %96,6 boşluğu kapatır | **Massive kararına bağlı** (dış maliyet, operatör kalemi); **kart ZORUNLU** |
| — | (etüdün altıncı adayı) | rapordaki tanımıyla | dalga-3'te sıraya girer |

**Kural:** kenar iddiası üreten modül ön-kayıtlı kart ister; saf görünüm/türetme modülü istemez.

---

## 5. Yazı tipi — Geist emekli, aday ölçümle seçilir

Impeccable'ın bulgusu kabul edildi (operatör kararı 3). Seçim tahminle değil, `DESIGN.md`'nin
Geist için kurduğu **aynı ölçüm standardıyla** yapılır (font ikilisi binary-düzeyinde incelenir).

**Geçilmesi zorunlu çıta:** kendi-barındırma (CSP dış font-host'a izin vermez) · açık lisans ·
**tam Türkçe aksan** (ı/İ/ş/ğ/ç/ö/ü — dotless-i çoğu display yüzünde kırık) · **gerçek tabular
rakam** (yapısal ya da `tnum`) · ayırt edilebilir `0/O` ve `1/l/I` · **eşlenik mono** · iki
zeminde 10-11px okunabilirlik, gece zemininde halation yok · değişken ağırlık tercih.

**Yöntem:** `/impeccable typeset` turu — aday havuzu, binary ölçümü, iki zeminde render,
kazananın jetonlara işlenmesi. Rampanın dokuz basamağı ve tabular kuralı korunur.

---

## 6. Dalga sırası ve kapılar

| Dalga | İçerik | Impeccable |
|---|---|---|
| **0** (uçuşta) | Acil doğruluk: mod her durumda görünür · ffill rozeti · `?? 0` triyajı | — |
| **1** | Jetonlar + beş renk rolü + mod kanalı + 164 koşulsuz emisyonun temizliği | `colorize` (kısıtlı prompt), `extract` |
| **2** | Hücre/kart sözleşmesi + yeni IA (§3) + olay yüzeyleri + runbook emilimi | `shape`, `layout`, `distill`, `live` |
| **3** | Fırsat yüzeyleri (C1'in on işi) + modüller (§4) | `shape`, `clarify` |
| **4** | Yazı tipi (§5) + tipografi | `typeset` |
| **5** | Sertleştirme: durum tasarımları, klavye tam turu, performans, viewport | `harden`, `optimize`, `adapt` |
| **6** | Doğrulama: `audit`+`critique` önce/sonra · on ilkenin kanıtı · devir belgesi | `audit`, `critique`, `document`, `doctor` |

**Her dalganın kapısı:** kapsam testleri yeşil → tek otoriter suite → tek `dagit` → canlı
doğrulama. `bolder`/`delight`/`overdrive` bu üründe **koşulmaz** (dopamin ve renk yasaları).

**Bitiş ölçütü:** `audit` sıfır P0/P1 · `critique` AI-slop PASS · üç kanonik görevin ölçülmüş
adım sayısı düşmüş · tam klavye turu faresiz · **ve sistemin ürettiği hiçbir bilgi "üretiliyor
ama görünmüyor" kovasında kalmıyor.**

---

## 7. TAM KUYRUK — hiçbir öneri sıradışı kalmıyor (2026-08-07 denetimi)

Operatör sorusu üzerine sayıldı: etüdün **22 FIRSAT** satırından yalnız C1'in onu yüzeylere
yerleşmişti; **on beşi ve Bölüm B'nin detaylandırılmamış modül adayları sıraya GİRMEMİŞTİ.**
Kapatıldı — tam kuyruk aşağıda, statüsüyle.

### D3-a · C1'in on işi (yerleşti, §3'teki yüzeylerde) ✅ sırada
Reddedilen-karar karnesi · emir yaşam-döngüsü · gece maliyet karnesi · canlı zaman çizelgesi ·
rollback sicili · regresyon kırılımı · denetim izi · "bugün neden hiçbir şey olmadı" ·
çıkış-nedeni kırılımı · skor olgunlaşması.

### D3-b · Kalan on beş FIRSAT (YENİ — sıraya alındı)
| # | İş | Yüzey | Not |
|---|---|---|---|
| F1 | **Kâğıdın nerede yalan söylediğini bilme** | ③ | kâğıt-canlı ayrışması; L1'e geçişin ön-şartı |
| F2 | **Canlı-backtest sapmasının kökünü adlandırma** | ④ | E1/E2 hattımızın tam kalbi |
| F3 | **İptali olmayan aksiyondan önce ön-uçuş** (IBKR WhatIf deseni) | ②/⑤ | onay öncesi sonuç önizlemesi |
| F4 | **Tek kararı adım adım geri sarma** | ② | denetim izinin yürütülebilir hâli |
| F5 | Yinelenen arızaları taksonomiye kümeleme | ③ | alarm gürültüsünün kökü |
| F6 | Arızalı koşuları hedefli filtreyle bulma | ③/④ | kayıtlı sorgular |
| F7 | Ajanın izlediği yolu graf olarak görme | ④ | ham-iz defterinin (C2-2) görünümü |
| F8 | "Neden çalışmıyor" ayrımı (durum sözlüğü) | ③ | arıza-sınıfı ayrımı |
| F9 | Eylemsizliğin nedeni — kilit/kapı düzeyinde | ② | C1#8'in kapı-düzeyi derinleşmesi |
| F10 | Kapasite/doygunluk | ② | slot/ısı doygunluğu |
| F11 | Kesinti anını getiriyle aynı eksende görme | ④ | kesinti ↔ performans bağı |
| F12 | Kesintiye dayanıklılığı önceden ayarlama | ⑤ | eşik/yeniden-deneme yapılandırması |
| F13 | Örneklem derinliğini açarken bedelini beyan etme | ④ | K-cezası şeffaflığı |
| F14 | İki kademeli eşik + NO_DATA hâli | ③ | uyarı/alarm ayrımı + veri-yok |
| F15 | Stratejinin dönem dönem neyi tuttuğu | ④ | tahsis tarihçesi |
| (F16) | Emri kimin koyduğunu ayırma (`clientId`) | — | **bugün tek yol var → uygulanabilir değil**, kayda geçti |

### D3-c · Modüller — beşi + Bölüm B'nin ek adayları
| Modül | Statü |
|---|---|
| C2-1 ajan telemetrisi (S) | 🔄 yazılıyor |
| C2-2 ham iz defteri (M) | 🔄 yazılıyor |
| C2-3 vaka sabitleme (M) | 🔄 yazılıyor |
| C2-4 ikinci motor diferansiyeli — LEAN (L) | 📋 sırada (QC hesabı gerekmez) |
| C2-5 delist-dahil evren arşivi (L) | 📋 sırada — **Massive kararına bağlı** + kart ZORUNLU |
| B-ek: bar-içi dolum varsayımını sınama | 📋 sırada (E2 hattına bitişik) |
| B-ek: bakiyenin işlem-dışı nedenle değişmesi | 📋 sırada |
| B-ek: latency dağılımı / darboğaz | 📋 sırada (C2-1 telemetrisi üstüne) |
| B-ek: üretim izini farklı model/prompt ile yeniden koşturma | 📋 sırada (C2-2 üstüne) |
| B-ek: ajan koşusunu duraklatıp onayla/düzelt/reddet | 📋 **kart-şartlı** — ajan yetkisine dokunur, operatör hükmü ister |

**Kural:** bu kuyruktaki hiçbir kalem "sonra bakarız" diye düşmez; düşecekse gerekçesi yazılır
(F16'da olduğu gibi).
