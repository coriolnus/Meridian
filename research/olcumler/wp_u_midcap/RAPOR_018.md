# EDG-2026-018 — PIT MID-CAP ÜST-SINIR · **ADIM-0 FEASIBILITY-GATE RAPORU**

- Kart: `research/cards/EDG-2026-018-pit-midcap-ust-sinir.yaml` · aile `pit_midcap_ust_sinir`
- Sandbox: `research/olcumler/wp_u_midcap/` · üretildi `2026-08-02T15:20:14Z`
- Repo HEAD: `4b84871` · **kirli_agac: EVET** → bu rapor bu SHA'dan birebir yeniden üretilemez;
  SHA o anki kodun değil **atasının** adıdır (`olcum_araclari` damga sözleşmesi, iki dürüstlük kuralı).
- Python 3.12.7 · `olcum_araclari` sürüm `2026-08-02`
- Kart sha256 **ölçüm ÖNCESİ = SONRASI**: EVET
  (`317013c98cfdd08414ee3a0071747860b9ab35fb494b810f1c57237247ef95ae`) — **karta DOKUNULMADI**
- Rol: ölçüm ajanı. **Bu rapor HÜKÜM CÜMLESİ TAŞIMAZ.** Kapı sayıları kartın eşikleriyle
  yan yana konur; hükmü Rol-1 verir.
- Yazım beyanı: `state/` altına HİÇBİR yazım yapılmadı (bar arşivi ve `edgar_facts` SALT-OKUNUR
  açıldı); tek yazım bu klasördür.

> **ÖLÇÜM KOŞULMADI.** Kartın `feasibility_gate` alanı ölçümden ÖNCE koşulmasını zorunlu kılar ve
> "ölçüm BAŞLAMAZ; çıktı yalnız KAPSAMA HARİTASI olur" der. Pozitif kontrol, turnover üst-dilim
> hücresi, 21g blok CI ve maliyet duyarlılığı **koşulmadı**; `sonuc_018.json` **üretilmedi**.
> Bu bir başarısızlık değil, kartın kendi yazdığı yolun izlenmesidir.

---

## 0. Kapı sayıları — kartın eşikleriyle yan yana

Kart eşikleri (`feasibility_gate`, birebir): **kapsanan isim sayısı < 40** VEYA
**ortalama bar-geçmişi < 3 yıl** → ölçüm başlamaz.

| eşik | kart değeri | ölçülen | eşiğin altında mı |
|---|---|---|---|
| kohortun veriyle **kurulabilirliği** (gate'in parçası) | kurulabilir olmalı | **kurulamadı** (eksen A) | — (sayı üretilemez, TANIMSIZ) |
| kapsanan isim sayısı | ≥ 40 | **12** | **EVET** |
| ortalama bar-geçmişi (tüm arşiv) | ≥ 3 yıl | 18,90 yıl | hayır |
| ortalama bar-geçmişi (yalnız üyelik-dönemi barları) | ≥ 3 yıl | 13,30 yıl | hayır |

Bar-geçmişi yıla çevrim sabiti: **252 işlem günü/yıl** (beyanlı).

İki eşik kartta **VEYA** ile bağlıdır: isim eşiği tek başına kapıyı düşürür. Yıl eşiğinin
geçilmesi bir teselli değil, **aynı seçilimin ikinci yüzüdür** — §2'de veriyle gösterilir:
barı olan 12 ismin geçmişi tam da *canlı evrende bulundukları için* uzundur.

---

## 1. EKSEN A — Kartın lafzı: mid-cap kohortu kaynaktan İNMİYOR

Kart `evidence_refs` alanında kohortun kaynağı olarak `research/pit_universe/sp500_uyelik_tarihi.csv`
dosyasını anar. Dosyanın yapısı ölçüldü:

| ölçüm | değer |
|---|---|
| sütunlar | `date`, `tickers` — **başka alan yok** |
| satır | 2.718 (kart notu "2.719 satır" başlık satırını sayıyor) |
| tarih aralığı | 1996-01-02 → 2026-06-30 |
| kadans | **olay-tarihli anlık görüntü** (her işlem günü değil); ardışık satır farkı medyan 2 gün, maks 91 gün |
| günlük üye sayısı | medyan 497 (min 487, maks 507) |
| boyut / piyasa-değeri / endeks-ailesi alanı | **YOK** |
| depodaki diğer PIT evren kaynağı | `nasdaq100_yillik/` → **BOŞ (0 dosya)**; `LICENSE-fja05680` |

**Veri cümlesi:** dosya bir **S&P 500** (tanımı gereği large-cap) üyelik geçmişidir; günlük üye
sayısı 487–507 aralığındadır, yani endeksin kendisidir. S&P MidCap 400 üyeliği bu dosyada temsil
edilmiyor ve depoda başka bir mid-cap PIT evren kaynağı yok. Hiçbir satırda büyüklük alanı
bulunmadığı için kartın `universe: pit_midcap_survivor` kohortu **bu kaynaktan türetilemiyor**.

Bu, kapının bir parçasıdır: brief'in yazdığı gibi *"kohort tanımının veriyle kurulabilirliği
gate'in bir parçasıdır"*. Kohort kurulamadığı için kartın kendi kohortu üzerinde bir kapsama
sayısı **None değil, TANIMSIZDIR** — ölçülemeyen bir büyüklük değil, tanımlanamayan bir kümedir.

---

## 2. EKSEN B — Brief'in yönlendirdiği eksen: ÇIKMIŞ isimler × üyelik-dönemi barları

**Kohort tanımı (kurulan):** S&P 500 üyelik geçmişinde en az bir kez görünmüş **ama son anlık
görüntüde (2026-06-30) olmayan** isimler = *çıkmış isimler*. Üyelik as-of okunur: bir sembol t
gününde üyedir ⟺ `date <= t` olan **son** satırda geçiyorsa (look-ahead yok).

**Bu kohort mid-cap DEĞİLDİR** ve öyle sunulmuyor. Endeksten çıkış küçülmeyle olduğu kadar
birleşme, satın alma ve borsa transferiyle de olur; aşağıdaki 12 ismin **hepsi** üyelik
dönemlerinde large-cap endeks üyesiydi. Ölçülen tek şey **bar kapsamasıdır**.

| ölçüm | değer |
|---|---|
| dosyada hiç görünmüş toplam isim | 1.206 |
| son anlık görüntü (2026-06-30) üye sayısı | 503 |
| **çıkmış isim** | **703** |
| çıkmış **ve** arşivde barı olan | **12** |
| çıkmış ve barı olmayan | 691 |
| bar kapsama oranı | **%1,71** |

### 2a. Barı olan 12 ismin dökümü

| sembol | üyelik ilk | üyelik son | bar n | bar ilk | bar son | üyelik-içi bar n | üyelik-içi yıl | emekli defterinde |
|---|---|---|---|---|---|---|---|---|
| ANSS | 2017-06-19 | 2025-07-18 | 5419 | 2004-01-02 | 2025-07-16 | 2031 | 8,06 | EVET |
| CAG | 1996-01-02 | 2026-06-30 | 5679 | 2004-01-02 | 2026-07-28 | 5659 | 22,46 | hayır |
| DFS | 2007-07-02 | 2025-05-19 | 4504 | 2007-06-25 | 2025-05-15 | 4499 | 17,85 | EVET |
| ENPH | 2021-01-07 | 2025-09-22 | 3602 | 2012-03-30 | 2026-07-28 | 1182 | 4,69 | hayır |
| FI | 2023-06-07 | 2025-11-11 | 5500 | 2004-01-02 | 2025-11-07 | 610 | 2,42 | EVET |
| HES | 1996-01-02 | 2025-07-23 | 5421 | 2004-01-02 | 2025-07-17 | 5421 | 21,51 | EVET |
| IPG | 1996-01-02 | 2025-11-28 | 5513 | 2004-01-02 | 2025-11-25 | 5513 | 21,88 | EVET |
| K | 1996-01-02 | 2025-12-11 | 5522 | 2004-01-02 | 2025-12-09 | 5522 | 21,91 | EVET |
| MTCH | 2021-09-20 | 2026-03-23 | 2686 | 2015-11-19 | 2026-07-28 | 1131 | 4,49 | hayır |
| PARA | 2022-02-17 | 2025-08-08 | 4950 | 2005-12-05 | 2025-08-06 | 870 | 3,45 | EVET |
| VFC | 1996-01-02 | 2024-04-01 | 5679 | 2004-01-02 | 2026-07-28 | 5095 | 20,22 | hayır |
| WBA | 1996-01-02 | 2025-08-28 | 2682 | 2014-12-31 | 2025-08-28 | 2681 | 10,64 | EVET |

Bar-geçmişi dağılımı (yıl): tüm arşiv — ort **18,90**, medyan 21,51, min 10,64, maks 22,54;
yalnız üyelik-dönemi — ort **13,30**, medyan 14,25, min **2,42**, maks 22,46.

### 2b. İKİNCİ SEÇİLİM — bu 12 isim rastgele değil

| ölçüm | değer |
|---|---|
| barı olan 12 ismin çıkış yılı dağılımı | 2024: 1 · 2025: 9 · 2026: 2 — **hepsi 2024 ve sonrası** |
| bunlardan `RETIRED_SYMBOLS` defterinde olan | 8 |
| bunlardan hâlâ CANLI evrende (`REPLAY_UNIVERSE`) olan | 4 (CAG, ENPH, MTCH, VFC) |
| barı olmayan çıkmış isimlerin 2009+ çıkış yılı dağılımı | 2009: 21 · 2010: 16 · … · 2023: 18 · 2024: 19 · 2025: 12 · 2026: 12 |

**Veri cümlesi:** arşivdeki barlar bu 12 ismin *çıkmış olmasından* değil, **çıkmadan önce canlı
evrende bulunmasından** doğuyor. 2009–2023 arasında endeksten çıkan 300'den fazla ismin
**hiçbirinin** barı yok. Yani "çıkmış isim" ekseninin kendisi ikinci bir seçilim taşır: çıkış
tarihi eskidikçe bar bulunma olasılığı sıfıra iner. Uzun ortalama bar-geçmişi (18,90 yıl) bu
seçilimin sonucudur, kapsamanın iyi olduğunun kanıtı değil.

---

## 3. EKSEN C — Boyut ekseni (BETİMLEYİCİ; **PIT DEĞİL**, hüküm bacağı DEĞİL)

**Ne olduğu:** tek bir **güncel kesit** — son bar kapanışı × en son dosyalanmış **anlık** hisse
sayısı (dei `EntityCommonStockSharesOutstanding` önce, us-gaap `CommonStockSharesOutstanding`
sonra; ağırlıklı-ortalama SEVİYE olarak kullanılmaz — EDG-012/016 kuralı). EDG-016'nın as-of
paneli **değildir**, CI taşımaz, K harcamaz. Tek bir soruyu cevaplar: *bar arşivinde mid-cap
bandında isim var mı?*

Bant sözleşmesi (**KART DIŞI**, beyanlı): 2–10 milyar USD, yaygın piyasa konvansiyonu.

| ölçüm | değer |
|---|---|
| ölçülen sembol | 251 / 259 |
| ölçülemeyen | 8 (nedenleriyle ayrıştırıldı — aşağıda) |
| piyasa değeri medyanı | 74,7 mia USD |
| p10 / p25 | 23,3 / 39,0 mia USD |
| **2–10 mia bandında** | **9** (CAG, ENPH, IPG, MTCH, NCLH, PINS, SNAP, SWKS, VFC) |
| 2 mia altında | 1 (SPG — **bayat hisse sayımı artefaktı**, aşağıya bakınız) |

Bant duyarlılığı (kümülatif isim sayısı; parantez içi = bayat hisse sayımı olanlar düşülünce):

| eşik | <2B | <5B | <10B | <15B | <20B | <30B | <50B |
|---|---|---|---|---|---|---|---|
| tüm | 1 | 3 | 10 | 16 | 19 | 42 | 79 |
| bayat işaretliler hariç | 0 | 1 | 8 | 14 | 17 | 40 | 74 |

**Bayatlık bekçisi (400 gün):** 10 sembolde hisse sayımı bayat işaretlendi; satırlar atılmadı,
**işaretlendi** (eksen betimleyici). İki uç vaka veriyle: `SPG` hisse dönem-sonu 2012-12-31
(4.957 gün bayat) → hesaplanan 0,0019 mia USD **kullanılamaz**; `PINS` dönem-sonu 2019-03-31
(2.677 gün bayat) → 3,08 mia USD **güvenilmez**. (EDG-016 turunda da SPG fiziksel bekçiye takılan
sembollerden biriydi — aynı kayıt sorunu.)

Ölçülemeyen 8 sembolün nedenleri **ayrıştırıldı** (UYDURMA YASAĞI — üç ayrı yokluk tek etikete
sıkıştırılmadı):

| neden | semboller |
|---|---|
| yalnız ağırlıklı-ortalama etiketi var (seviye olarak kullanılmaz) | EL, HRL, META, MKC, TSN |
| anlık etiket var ama kullanılabilir değer yok (val ≤ 0) | PARA |
| dosyada bu sembole ait HİÇ satır yok | SPY (ETF), STZ |

**Veri cümlesi:** arşiv 251 large-cap likit isimden oluşuyor; bandın içine düşen 9 ismin çoğu
*mid-cap evreninden gelen* isimler değil, **küçülerek** bu bandın içine inmiş eski large-cap'ler
(5'i eksen B'nin çıkmış isimleri: CAG, ENPH, IPG, MTCH, VFC). Bant 20 mia USD'ye kadar gevşetilse
bile bayatsız isim sayısı 17'de kalıyor — kartın 40 isim eşiğinin altında.

---

## 4. EKSEN D — Delist boşluğu (WP-U kilidine doğrudan girdi)

| ölçüm | değer |
|---|---|
| barı olmayan çıkmış isim | **691** |
| üyelik süresi (takvim günü) | ort 3.140 · medyan 2.393 · p10 609 · p90 6.544 · min 7 · maks 11.129 |
| çıkış yılı aralığı | 1996 – 2026 (31 kova) |
| 2009-08-04 sonrası çıkan **ve** barı olmayan | **338** |

**EDG-016 panel penceresi karşılığı** (panel ilk gözlem günü 2009-08-04):

| ölçüm | değer |
|---|---|
| pencerede endeksten çıkan toplam isim | 350 |
| bunlardan arşivde barı olan | 12 |
| bunlardan arşivde barı **olmayan** | 338 |
| **kayıp oranı** | **%96,57** |

**"Üst-sınır" şerhinin veri dilindeki karşılığı.** Kartın tezi, ölçülecek her mid-cap sayısının
bir üst-sınır olacağını söylüyordu: delist edilmiş isimlerin barları yok, eksik kuyruk sonucu
yukarı çarpıtır. Bu rapor o çarpıtmanın **büyüklüğünü ölçmez** — ölçemez, çünkü eksik barlar
tanımı gereği yok. Ölçtüğü şey **eksik kuyruğun BOYUTUDUR**: EDG-016 panelinin penceresinde
endeksten çıkan isimlerin %96,57'si arşivde hiç bar taşımıyor. EDG-016'nın Ç1 şerhi
("işareti bilinir, büyüklüğü bu veriyle ölçülemez") bu sayıyla **kapsama tarafında**
niceliklendirilmiş olur; etki büyüklüğü hâlâ ölçülmemiştir.

---

## 5. Kill-listesi karşılıkları (TABLO — hüküm YOK)

| # | kartın kill/askı ölçütü (birebir) | ölçülen karşılık | tetiklendi mi |
|---|---|---|---|
| 1 | "feasibility_gate düşer → askıya:veri-kapısı, kapsama haritası teslim (kill DEĞİL — veri kilidi)" | kohort kurulamadı (eksen A); kapsanan isim **12 < 40** (eksen B) | **EVET** |
| 2 | "üst-dilim fazlası CI-0-içi → mid-cap sağkalanda bilgisiz…" | **ölçülmedi** — kapı düştüğü için hücre koşulmadı | ölçülmedi |
| 3 | "maliyet-sonrası net ≤ 0 → mid-cap işlem maliyeti etkiyi yiyor…" | **ölçülmedi** — kapı düştüğü için hücre koşulmadı | ölçülmedi |

Kartın `guards` maddeleri de aynı sebeple **koşulmadı**: pozitif kontrol (mid-cap evrende ham
rvol20 @20 IC yeniden üretimi), PIT üyelik as-of gözlem-günü kontrolü, split/as-of bekçileri.
Üyelik as-of okuma kuralı bu raporda **yalnız kapsama sayımı için** işletildi (§2), sinyal için
değil.

`k_registry` beyanı: kartta iki trial_id kayıtlı (`wp_u_midcap/kapsama_gate`,
`wp_u_midcap/turnover_ust20`). Bu turda **yalnız `kapsama_gate` koşuldu**; `turnover_ust20`
hücresi ölçülmedi — K muhasebesinin nasıl işleyeceği Rol-1'in hükmüdür, bu rapor K'ya dokunmaz.

---

## 6. Kapsam-dışı beyanlar (bu raporun ÖLÇMEDİĞİ şeyler)

1. **Sinyalin mid-cap'te var olup olmadığı ölçülmedi.** Ne pozitif ne negatif kanıt üretildi;
   kartın "güçlü negatif kanıt" dalı da **açılmadı** (o dal ölçülmüş bir CI gerektirir).
2. **Hayatta-kalma çarpıtmasının büyüklüğü ölçülmedi.** Yalnız eksik kuyruğun kapsama boyutu
   (%96,57) ölçüldü. İkisi farklı büyüklüklerdir.
3. **Eksen C PIT değildir.** Tek güncel kesit; geçmişte hangi ismin ne zaman mid-cap bandında
   olduğu ölçülmedi. Bayat hisse sayımı olan 10 sembolde piyasa değeri **güvenilmez** (SPG, PINS
   adıyla işaretli).
4. **Çıkış sebebi ayrıştırılmadı.** 703 çıkışın kaçının birleşme/satın alma, kaçının küçülme
   (endeksten düşme) olduğu bu veriden okunamaz; üyelik dosyası sebep taşımıyor.
5. **Üyelik dosyasının doğruluğu bağımsız doğrulanmadı.** Dosya olduğu gibi alındı
   (sha256 `39a9202c…`); kaynağın kendi hataları bu rapora aynen geçer.
6. **Son anlık görüntü 2026-06-30'dur**, bar arşivi 2026-07-29'a kadar gider. 2026-07 içindeki
   olası üyelik değişiklikleri dosyada yok; "çıkmış" kümesi bu tarihe göre kuruldu.
7. **Delist barlarının EDİNİLEBİLİRLİĞİ ölçülmedi.** 691 ismin barının hangi sağlayıcıdan, hangi
   maliyetle alınabileceği bu turun kapsamı dışıdır; rapor yalnız boşluğun büyüklüğünü verir.

---

## 7. Kapı satırı (ölçüm standardı §"Rapor kapı satırı")

`pozitif kontrol KOŞULMADI · PK4 KOŞULMADI · PK5 KOŞULMADI` — üçü de **feasibility_gate ölçümü
başlatmadığı için** koşulmadı; bu bir HAYIR değil, bir **koşulmama** kaydıdır. Ölçüm koşsaydı üçü
de zorunluydu.

---

## 8. Dosyalar

| dosya | ne |
|---|---|
| `research/olcumler/wp_u_midcap/adim0_kapsama.py` | ADIM-0 betiği (salt-okunur girdiler; tek yazım `kapsama_haritasi.json`) |
| `research/olcumler/wp_u_midcap/kapsama_haritasi.json` | kapsama haritası — 4 eksen + kapı sayıları + kod damgası + girdi sha256'ları |
| `research/olcumler/wp_u_midcap/RAPOR_018.md` | bu rapor |
| `sonuc_018.json` | **ÜRETİLMEDİ** — kapı düştüğü için ölçüm koşulmadı (kartın yazdığı yol) |
