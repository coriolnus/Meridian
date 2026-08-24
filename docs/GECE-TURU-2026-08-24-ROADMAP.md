# GECE TURU 2026-08-24 — tahtaya işlenecek satırlar

> **Bu belge ROADMAP DEĞİLDİR.** `ROADMAP.md`'ye dokunulmadı (tahtayı Rol-1 işler). §6 blokları
> kopyala-yapıştır için hazırdır.
> **Yazan:** gece raportör ajanı. **Okuyucu (YASA 6):** sabah Rol-1 + operatör.
> **Yöntem:** her satır ya (a) icra ajanının iddiası + bağımsız doğrulayıcının hükmü, ya da
> (b) raportörün bu oturumda KENDİ koştuğu ölçüm ile desteklenmiştir. Desteksiz hiçbir kapanış
> "kapandı" yazılmadı.

## 0. GİRDİ BÜTÜNLÜĞÜ — ÖNCE BUNU OKU (uydurma yasağı)

Bu rapora gelen girdi **iki yerden kesikti**. Kesik kısımlar doldurulmadı, boş bırakıldı:

| # | kesik girdi | ham kesit | sonucu |
|---|---|---|---|
| 1 | "zaten-kapalı" listesinin **8. maddesi** | `{"id": "M11 Ö-1 \`broker_status\` pano yan` — `neden` alanı YOK | §4'te kalem **adıyla** listelendi, gerekçesi **None + neden: girdi kesik** |
| 2 | K2 doğrulama çiftinin **son bulgusu** | `…'%34,8 yakalama' başlığı 'bilinen spl` | §2'de o cümle **alıntılanmadı**; yerine raportörün kendi ölçümü kondu |

Ayrıca: girdide **yalnız K1 ve K2** için icra+doğrulama çifti var. **K3 ve K6** açıkça
"koşulmadı" damgalı. **K4 ve K5** yalnız başka kalemlerin gerekçesi içinde ileri-atıf olarak
geçiyor (`"kalan Ö-5…Ö-8 K4 kalemi olarak ayrıldı"`, `"açık kalan tek bacağı WP7-40 (K5)"`) —
bunların **hiçbir icra ya da doğrulama kaydı raportöre ulaşmadı**, durumları **bilinmiyor**.

---

## 1. TEK BAKIŞTA

| sınıf | adet | kalemler |
|---|---:|---|
| **Doğrulanarak KAPANDI** | **1** | K2 · `EDG-2026-056` split oran-imzası |
| **ÇÜRÜTÜLDÜ** (icra "kapandı" dedi, doğrulama düşürdü) | **1** | K1 · `EDG-2026-053` gelir momentumu → **kısmen** |
| **ZATEN KAPALIYDI** (Ö-49 bayat-beyan) | **8** | 7'si kanıtlı · 1'i girdi kesik (§0) |
| **KOŞULMADI** — çakışma/yasak | **2** | K3 · K6 |
| **DURUMU BİLİNMİYOR** — kayıt ulaşmadı | **2** | K4 · K5 |
| **Denenen toplam (icra çifti olan)** | **2** | K1 · K2 |

**Tek cümle:** gece iki ölçüm koştu; **biri sağlam kapandı (056), biri hüküm eşiğine
ULAŞAMADI (053)** — ve tahtanın 8 satırının bayat olduğu kanıtlandı.

**Raportörün bu oturumda kendi koştuğu doğrulamalar (tümü yeşil):**

| ne | komut/ölçüm | sonuç |
|---|---|---|
| 056 kapsam testi | `pytest research/olcumler/edg056_oran_imzasi_2026-08-24/test_tara.py` | `7 passed in 0.11s` |
| 056 sonuç bütünlüğü | `sha256(sonuc.json)` | `c1092218…4e78d9e` (doğrulayıcı ile birebir) |
| 056 motor kablolaması | `grep -rn "ratio_signature\|oran_imza\|oran-imza" meridian/` | **0 eşleşme** (hüküm ile tutarlı) |
| kart hijyeni (M8 U2/U3) | `grep -l "pending-" research/cards/*.yaml` | **8 kart**, 8'i de `registered`/`measuring` |
| kart endeksi | `ops/kart_endeksi_uret.py --kontrol` | `GÜNCEL`, çıkış 0 |
| çapa sağlığı | `codelaw.report()` | `ok=True`, `stale_line_anchors=[]` |
| suite kapsamı | `pyproject.toml:48` | `testpaths = ["tests"]` → `research/` testleri otoriter suite'e girmiyor |

---

## 2. KAPANANLAR

### K2 · `EDG-2026-056` — split oran-imzası dedektörü · **DOĞRULANDI · KAPANDI**

| alan | içerik |
|---|---|
| **ne yapıldı** | Kart ön-kayıtlıydı (`registered`, 2026-08-23 23:37). Tolerans tanımı (`donuk_tanim.json`) ve yer gerçeği (`bilinen_split_donuk.json`) **ölçümden ÖNCE donduruldu**; tarayıcı koştu; hüküm: **imza tek başına yetersiz — körlük BEYANLI kalır**. Dedektör motora **kablolanmadı**. |
| **sayılar** | aday **55** · eşleşen **32** · eşleşmeyen **23** · yakalanmayan **60/92** → YP **%41,8** · yakalama **%34,8** · `gecti=false` (çıta: YP ≤ %20 **VE** yakalama ≥ %80) |
| **kanıt — bağımsız yeniden üretim** | Doğrulayıcı izole ağaçta `tara.py`'yi sıfırdan koştu → üretilen `sonuc.json` repodakiyle **BYTE-AYNI**. Raportör sha256'yı üçüncü kez teyit etti: `c109221821d809b3207fd50d1186adadfbc2371c254374576f89133b84e78d9e`. |
| **kanıt — eşik donukluğu (kart yasası 3)** | `stat` birth==mtime: `donuk_tanim.json` 02:58:55 · `bilinen_split_donuk.json` 02:59:30 · `test_tara.py` 02:59:51 — **üçü de ölçümden önce donmuş, sonra dokunulmamış**. Kartın kendisi birth==mtime==`Aug 23 23:37:38` (raportör teyit etti) → **karta dokunulmadı**. |
| **kanıt — state yazımı yok** | `state/bars_integrity.json` mtime `07-31 10:19:54` (dokunulmamış), `state/quarantine/` `07-21`. Betikler yalnız `research/olcumler/edg056_*/` altına yazıyor. |
| **kanıt — hüküm dayanıklılığı** | Merdivenin **üç basamağı da** düşüyor: F=1,25 → YP %47,1 / yakalama %19,6 · F=1,5 → %41,8 / %34,8 · F=2,0 → %41,5 / %41,3. Yapısal yanlış-pozitifler (3:2 bandı, 8 aday) tamamen silinse bile YP = 15/47 = **%31,9 > %20**. Yakalama tarafı hiçbir yolda %80'e yaklaşmıyor. |
| **doğrulayıcının hükmü** | **`dogrulandi: true` · `gercek_durum: kapandi`.** Hükmü kırmaya çalıştı, kıramadı. |
| **dokunulan dosyalar** | `research/olcumler/edg056_oran_imzasi_2026-08-24/` (yeni: `RAPOR.md`, `sonuc.json`, `tara.py`, `test_tara.py`, `donuk_tanim.json`, `bilinen_split_donuk.json`, `dondur_liste.py`) · `docs/ELEME-WP4-HAVUZ-2026-08-23.md` (**append-only** — eski "ÖNERİ: ÖLÇ" bloğu duruyor, kapanış ayrı blok olarak eklendi; SİLME YOK sağlandı) |

#### K2'nin iki SAYI KUSURU — kapanışı değiştirmez, **düzeltilmeli**

| # | yer | yazan | doğru | kök neden (raportör ölçtü) |
|---|---|---|---|---|
| **KUSUR-1** | `RAPOR.md:45` | "92 olay / **61** sembol" | **60 sembol** | `61`, `bars_integrity.json`'daki `sembol_sayisi` alanıdır — **tüm kırılma sınıflarını** kapsar (98 kırılma). `sinif=="olcek_dikisi"` alt kümesi ise 92 olay / **60** sembol. Raportör saydı: `olcek_dikisi olay=92 sembol=60` · `hayalet_gecmis 5/5` · `bozuk_kesit 1/1`. |
| **KUSUR-2** | `RAPOR.md:128` | "Geriye kalan yanlış-pozitifler … **hepsi** 3:2 (1,5) bandına düşüyor" | **hepsi değil** | Raportör 23 eşleşmeyen adayın oran dağılımını saydı: `3:2`×7 · `1:2`×6 · `2:1`×5 · `2:3`×1 · `3:1`×1 · `1:10`×2 · `1:5`×1. Hayalet kümesi (5, hepsi 2025-05-26) ve sıçra-ve-dön çiftleri (8 satır) düşüldükten sonra **3 aday sınıflandırılmadan kalıyor ve hiçbiri 3:2 bandında değil**: `CMCSA 2006-10-24 (r=0,65769 · 2:3)`, `CMCSA 2013-12-19 (r=1,97991 · 2:1)`, `DLTR 2012-06-26 (r=0,49351 · 1:2)`. "hepsi" kanıtlanmamış bir süpürme iddiasıdır. |

> **Raportörün YANLIŞ ALARM İPTALİ (kayda geçsin):** §5.4'teki "yer gerçeği de ileri yöne
> süzülürse (**r>1 olan 50 olay**)" satırını önce hatalı sandım — `bars_integrity`'de
> `oran = c_t/c_{t-1}` konvansiyonunda r>1 sayısı **42**'dir. Ama donuk yer gerçeği **iki alan**
> taşıyor: `kayitli_oran_c_t_bolu_c_t1` (>1: 42) **ve** kartın konvansiyonu
> `r_kart_c_t1_bolu_c_t` (>1: **50**). Rapor kart konvansiyonunu kullanıyor → **satır DOĞRU**.
> Üçüncü bir kusur YOKTUR. (Kanıt: `bilinen_split_donuk.json`, n=92, iki alan da ölçüldü.)

#### K2'nin iki YÖNTEM UYARISI — kill değil, **Rol-1 tescili gerekir**

| # | uyarı | neden kill değil |
|---|---|---|
| **U-a** | Kart `beyanli_sinirlar(2)` ters-split'i "imza sınıfı dışında" sayıyordu; ölçüm **iki yönü de** aldı. | Seçim ölçümden **önce** `donuk_tanim.json`'da beyan edildi, karşı-olgusu ölçüldü (`RAPOR.md:172-174`), `kill_criteria`'da yasak değil. Ayrıca yer gerçeğinin 92 olayının 42'si ters yönlü — dışlansaydı yer gerçeği de bozulurdu. **Karta AYKIRI olduğu için Rol-1 tescil etmeli.** |
| **U-b** | Hacim toleransı **F=1,5 kartta YOKTU** — ölçüm ajanı icat etti, "kart boşluğu" diye beyan edip ölçümden önce dondurdu. | Kart kill'i yalnız "hacim teyidi **atlanırsa** geçersiz" diyor; atlanmadı. Merdiven üç basamağın da düştüğünü gösterdiği için F seçimi hükmü taşımıyor. **Yine de karta girmemiş bir eşiktir.** |

---

## 3. ÇÜRÜTÜLENLER

> **Bu bölümün tek kalemi var ve gecenin en değerli satırı budur.**

### K1 · `EDG-2026-053` — gelir momentumu (PIT faktör) · icra **"kapandı"** dedi → doğrulama **"kısmen"**

**İddia:** ölçüm koştu, dört hücre ölçüldü, "hiçbir dal eşleşmedi", `80 passed in 8.61s`.
**Hüküm:** `dogrulandi: false` · `gercek_durum: kismen`. **Kalem AÇIK.**

#### 3.1 Ne DOĞRULANDI (ölçüm zanaatı sağlam — bu kısım tartışmasız)

| kontrol | sonuç |
|---|---|
| Dört nokta tahmini, `panel.csv`'den **bağımsız** yeniden hesap | **4/4 birebir**: yoy@20g n=9861 ort=0,002215 · yoy@60g n=9789 ort=0,003745 · ivme@20g n=8180 ort=0,002308 · ivme@60g n=8163 ort=0,004473 |
| Ay-içi üst dilim payı | medyan 0,3021 (min 0,2979 maks 0,3077) → "üst %30" doğru |
| Elle doğrulama (AAPL 2024-08-30) | arşivden teyit: `85,777e9/81,797e9−1 = 0,048657` · ivme farkı `0,09171` |
| Şasi bütünlüğü | `sha256(ortak.py)=8b274c56…` · `sha256(pk.py)=25c1221e…` — EDG-050 ile **birebir** |
| Pozitif kontrol | çivi 0,0642 · PK4/PK5 tüm alt maddeler `True` |
| Karta dokunulmadı | `birth==mtime==Aug 23 22:12:06` (raportör teyit etti); status hâlâ `registered` |
| Gerçek PIT ihlali var mı? | Doğrulayıcının **bağımsız** denetimi: `filed>t` 0 satır · `end>t` 0 satır · seçilen `qidx` ≠ PIT-görünür max `qidx` 0 satır · `temel_ceyrek.csv`'den sıfırdan yeniden hesapta yoy uyuşmazlığı 0 → **sızıntı YOK** |

#### 3.2 ÖLDÜRÜCÜ BULGU — blok birimi sessizce **gün → ay** oldu ve **hükmü bu belirliyor**

Kart "**21g** blok-bootstrap CI" diyor; şablonun kendi sabiti `ortak.py:48`'de
"*blok-bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ (şablon)*" olarak yorumlanmış. EDG-050'de bir birim
**bir işlem günü** idi. Bu ölçümde birim **ay-sonu gözlem tarihi** olarak yeniden okundu →
blok ≈ **21 AY (≈1,75 yıl)**, `nd=202` ay üzerinde yalnızca `n_blok = ceil(202/21) = 10 blok`.

Ölçümün kendi eseri bunu **yazıyla** kabul ediyor (`faz6_ci_kararlilik.json`, raportör okudu):

> `"Bu panelde bir 'gözlem tarihi' = bir ay-sonu; blok 21 ≈ 21 ay takvim karşılığı."`

**Raportörün kendi çektiği tam blok-duyarlılık tablosu** (`faz6_ci_kararlilik.json`, tohum 20260812):

| dilim @ ufuk | blok=1 | blok=3 | blok=6 | blok=12 | **blok=21 (karar)** |
|---|---|---|---|---|---|
| `yoy_ust_30pct` @20g | `[−0,000629, +0,004923]` 0-içi | `[−0,000311, +0,004636]` 0-içi | `[−0,000265, +0,004013]` 0-içi | `[+0,000069, +0,003781]` **0-DIŞI** | `[+0,000330, +0,003454]` **0-DIŞI** |
| `yoy_ust_30pct` @60g | 0-içi | 0-içi | 0-içi | 0-içi | 0-içi |
| `ivme_ust_30pct` @20g | `[+0,000096, +0,004550]` **0-DIŞI** | 0-içi | 0-içi | 0-içi | 0-içi |
| `ivme_ust_30pct` @60g | `[+0,000086, +0,008653]` **0-DIŞI** | 0-içi | 0-içi | 0-içi | 0-içi |

**Bunun anlamı — kartın karar kuralı tersine dönüyor:**

- **blok=21** (seçilen): tek 0-dışı hücre `yoy@20g`. `@60g`'de hiçbir şey yok → kartın
  DAL-1 ateşleme şartı **eşleşmiyor** → "hiçbir dal eşleşmedi".
- **blok=1**: `ivme_ust_30pct @60g` CI `[+0,000086, +0,008653]` → **0-DIŞI POZİTİF**, ve
  `net_10bps = +0,003473 > 0`. Kartın DAL-1 şartı — *"herhangi bir dilim @60g anlamlı POZİTİF
  VE 10bps sonrası net>0 → temel-momentum sinyali VAR — ARSENAL adayı"* — **TAM EŞLEŞİYOR**.

> **Yani: blok=1'de kart ATEŞLER, blok=21'de "hiçbir dal eşleşmedi".** Hangi dalın ateşlediğini
> **kart donduktan SONRA seçilen bir birim yorumu** belirliyor. Doğrulayıcı bunu kendi
> bootstrap'iyle bağımsız üretti (aynı cebir, seed 20260812).

#### 3.3 KIRILGANLIK BEYANI TEK YÖNLÜ — YASA 4 sınıfı

`sonuc.json`'daki `duyarlilik_serhi` yalnızca şunu diyor: *"@20g'deki 0-dışılığın blok 1/3/6'da
kaybolması Rol-1'in görmesi gereken bir kırılganlıktır."* İddia metni de yalnız
*"yoy @20g 0-dışılığı blok seçimine duyarlı, blok 6/3/1'de NEGATİF"* diyor.

**Duyarlılık SADECE bulguyu ZAYIFLATAN yönde anlatılmış.** Aynı tablodaki *"blok=1'de ATEŞLEME
dalı AÇILIYOR"* gerçeği **hiçbir yerde cümleye dökülmemiş** — sayı JSON'da gömülü duruyor.
Rol-1'e giden özet, **kartın ateşleyip ateşlemediğini blok seçiminin belirlediğini SÖYLEMİYOR.**

#### 3.4 Tek "0-dışı" hücre istatistiksel olarak tanımlı değil

`yoy@20g lo=+0,000330` — kartın DAL-2 (BİLGİSİZ) eşleşmesini engelleyen **tek** hücre:

| sınama | sonuç |
|---|---|
| (a) Bağımsız ay-düzeyi çıkarım (bootstrap'in kendi yeniden-örnekleme birimi) | gözlem-ağırlıklı ort 0,002215 · se 0,001405 · **t=1,58** · %95 CI `[−0,000539, +0,004968]` → **0-İÇİ** |
| (a2) Eşit-ağırlıklı ay serisi, Newey-West L=0/1/3/6 | **t = 1,34 / 1,35 / 1,52 / 1,55** → hepsi **0-İÇİ** |
| (b) Blok genişliği | blok1 w=0,005552 → blok21 w=0,003124 — **monoton DARALIYOR**. Pozitif seri bağımlılık varsa hareketli-blok CI'sı **GENİŞLEMELİ**, yarıya inmemeli. (Raportör tabloyu bağımsız çekti, daralma teyitli.) |
| (c) Permütasyon sınaması (ay sırası karıştırılmış, aynı veri/tohum/blok=21, 30 tekrar) | alt sınır medyan **−0,000373** · min −0,002056 · maks **+0,000391** · `lo>0` oranı yalnız **0,27**. Gerçek sıradaki +0,000330 bu gürültü dağılımının **İÇİNDE**. |

`n_blok=10` ile CI genişliği başlı başına yüksek varyanslı bir rastgele değişkendir; "0-dışı"
okuma **sıralama gürültüsünden ayırt edilemiyor**.

#### 3.5 PIT "yıkıcı sınaması" TOTOLOJİK — kanıt değeri sıfır

`olcum.py::pit_yikici_sinama` önce
`kes = [k for k in kayitlar if k['filed'] <= r['t']]` ile süzüyor, sonra `_asof_saf(kes, r['t'])`
çağırıyor. Ama `_asof_saf`'ın **ilk satırı zaten** `gor = [r for r in kayitlar if r['filed'] <= t]`.
Panel de aynı `_asof_saf` ile kurulmuş.

> `f(x)` ile `f(filtre(x))` karşılaştırılıyor; filtre **idempotent** olduğu için
> `ihlal_yoy` / `ihlal_ivme` **matematiksel olarak 0 çıkmak zorunda**.

Aynı şekilde `kesik_girdide_leak` (`any(k['filed']>t for k in kes)`) ve
`dogrudan_filed_buyuk_t` yapı gereği 0. Kanıt#4 (*"sinanan_satir=32934 … gecti=True"*) **hiçbir
bilgi taşımıyor — sınama ASLA kırmızı veremezdi.**
*(Şerh: gerçek bir PIT ihlali de bulunamadı — §3.1. Yani sonuç doğru, ama iddia edilen KANIT geçersiz.)*

#### 3.6 Kart sonrası eklenen, etkisi ölçülmemiş örneklem filtresi

`BAYAT_CEYREK_GUN = 200` guard'ı kartın `features_asof` / `kill_criteria` listesinde **YOK**.
Ölçüm ajanı ekledi ve **2.388 gözlemi** (panel öncesi ~%7) düşürdü. "Karar eşiği DEĞİL, veri
hijyeni" diye beyan edilmiş — ama **guard'sız duyarlılık koşusu YOK**. "Eşik sonradan değişmez"
disiplini açısından **ikinci serbest parametre**.

#### 3.7 `frame` hizasında beyan edilenden geniş maruziyet (beyan eksik, hüküm-değiştirici değil)

`cq` anahtarı `q.dropna(subset=['frame']).groupby(['symbol','start','end']).frame.first()` ile —
yani **ilk-ifşa filtresinden ÖNCEKİ** tam kümeden alınıyor. Ölçüldü: 12.597 frame-kaynaklı
dönemin **10.041'inde (%80)** frame, o dönemin **ilk ifşasından SONRA** dosyalanmış bir satırdan
geliyor. Türetilen-alternatifle uyum 0,999127 (11 uyumsuz) olduğu için **etki sınırlı** — ama
`sonuc.json` "`frame_kaynakli_donem: 12597`" derken bu 10.041'lik geç-dosyalama maruziyetini
**hiç saymıyor**.

#### 3.8 Testin bu kalemi BAĞLAMADIĞI — kapanışı hiçbir kapı korumuyor

```
grep -rln 'EDG-2026-053\|edg053' tests/ meridian/ docs/ scripts/   →  BOŞ
```
(Raportör bu grep'i **kendi koştu**, sonuç boş.) İddiadaki `80 passed in 8.61s` **kapsamsız
beyan edilmiş ve birebir yeniden üretilememiş**: doğrulayıcının koştuğu
`tests/test_kart_hijyeni_v279.py test_kart_hukum_damgasi_v251.py test_kart_kimlik_v219.py
test_kart_sozlesmesi_v198.py` → `61 passed in 9,56s`; beş dosyalı superset → `79 passed in 12,41s`.
Bu suite'ler kaldırılsa da, gevşetilse de kalem **aynen "kapandı" görünürdü** — kapanış
tamamen JSON eserlerine dayanıyor.

#### 3.9 Bu kaleme YAZILAMAYAN kırmızı (kayda geçsin)

Doğrulama anında `codelaw.report()` → `ok=False`, `stale_line_anchors=[{'kaynak':'conftest.py:59',
'capa':'api.py:1553','neden':'yorum'}]`. Çapa `meridian/api.py`'ye bakıyor (o sırada **uçuştaki
başka bir ajanın** dosyası). EDG-053 yalnız `research/olcumler/edg053_.../` altına yazdı,
`meridian/` altına hiç dokunmadı. **Bu kırmızı 053'e yazılamaz.**
**Raportör notu:** rapor yazım anında `codelaw.report()` → **`ok=True`, `stale_line_anchors=[]`**.
Kırmızı geçiciydi ve kapandı.

#### 3.10 Hüküm verilmeden önce gerekenler (doğrulayıcının listesi, aynen)

1. **Blok biriminin adlandırılması** — 21 işlem günü mü, 21 ay mı? (Rol-1 mimari hükmü.)
2. **Her iki okuma için dört hücrenin de karar tablosuna yazılması.**
3. **`BAYAT_CEYREK_GUN=200` guard'ının duyarlılık koşusu.**
4. **Totolojik PIT sınamasının gerçek bir yıkıcı sınamayla değiştirilmesi.**

| dokunulan dosyalar | `research/olcumler/edg053_gelir_momentumu_2026-08-24/` (`olcum.py`, `ortak.py`, `panel.csv`, `faz1…faz6*.json`, loglar). **`research/cards/EDG-2026-053-*.yaml` DOKUNULMADI** (birth==mtime, status `registered`). `meridian/` altına **hiç yazılmadı**. |
|---|---|

---

## 4. ZATEN KAPALIYDI (Ö-49 bayat-beyan sınıfı)

Tahtada **açık** görünen ama gerçekte **kapalı** olan 8 satır. Bunlar iş değil, **tahta bakımı**.

| # | tahtadaki satır | gerçek durum | kanıt |
|---|---|---|---|
| **B1** | M8 U2/U3 kart hijyeni (WP5) | **KAPALI.** ELEME-WP5'in "41/65 kart pending-*" sayımı **bayat**. | **Raportör saydı:** `research/cards/` altında **68 kart** (+ README = 69 dosya). `pending-` deseni taşıyan **8 kart**: `EDG-019` `EDG-042` `EDG-052` `EDG-053` `EDG-054` `EDG-055` `EDG-056` `EXE-003` — **sekizi de `registered` ya da `measuring`**, yani **ölçülmemiş kart = DOĞRU hâl**. (46 kart "pending" kelimesini metin içinde taşıyor — SİLME YOK yasası gereği üstü çizili tarihçe notları.) README endeksi elle bakımdan çıkmış: `ops/kart_endeksi_uret.py --kontrol` → `GÜNCEL`, çıkış **0**. Çivi: `tests/test_kart_hijyeni_v279.py`. §7'de zaten kayıtlı. |
| **B2** | M11 kova-6 alan merceği taraması (WP5) | **KAPALI.** Tarama 2026-08-24'te koştu. | `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md` **mevcut** (37.840 bayt, `Aug 24 03:06`). 26 plan alanı + 14 `entry_law` alt-alanı; kalibrasyon 3/3. Türeyen DAMGALA önerilerinden Ö-3/Ö-4 de indi; Ö-5…Ö-8 K4 kalemi olarak ayrıldı. §7'de zaten kayıtlı. |
| **B3** | F8 kanonik durum sözlüğü uygulaması (WP8) — *"Sıradaki: kanonik sözlük uygulaması"* | **KAPALI + kısmen YASAK DOSYA.** | `meridian/durum_sozlugu.py` **MEVCUT** (10.971 bayt, `Aug 24 00:06`), üç yüzeye kablolu: `watchdog.py:202/515/1347/1782/3053` · `api.py:3087-3089/3166` · `hermes_runtime.py:643-647`; çift-alan geçiş rejimi + eşanlamlı-okuma sayaçlarıyla. Kalan A1-A8 Rol-1/operatör **soruları**; pano bacağı `meridian/web/app.js` + `meridian/api.py` (**yasak liste**). |
| **B4** | EXE-2026-009 pencere kaydırma uygulaması (WP1) — §5'te "operatör-bekliyor" | **KAPALI.** Karar 2026-08-23 K2'de verilmişti; kod indi. | **Raportör okudu:** `barclock.py:144 ENTRY_WINDOW_ET_MIN = 9*60+45` · `:147 _PENCERE_REJIMLERI = {9*60+30:"1330", 9*60+45:"1345"}` · `:150 def pencere_rejimi()`. Damga: `loop.py:700/1470/2571`. Okuyucu: `research/olcumler/edg042_kosum_2026-08-22/pencere_altbant.py` + `pencere_cek.py`. Kapı: `intraday_cycle.py:90/172`. |
| **B5** | WP7-31a `hermes.py:3987` `cevap_veren_model` + 31b `active_model` uydurma koruması | **KAPALI.** | **Raportör okudu:** `hermes.py:2185 def cevap_veren_model()`, künye `:3748` ve `:4269` üstünden; `:4178`'de tüketen-okuma sözleşmesi yazılı. `active_model()` gövdesi `_model_id`'ye delege edilerek uydurma koruması **tek kaynağa** bağlanmış. Ailenin açık kalan tek bacağı **WP7-40 (K5)** — bkz. §5. |
| **B6** | M11 Ö-3/Ö-4 `entry_law` ölü alanları + çürük "okuyucusu E2" beyanı | **KAPALI.** | **Raportör okudu:** `broker.py:255` `ÖLÜ-ALAN DAMGASI[M11]` bloğu (`olay` · `offset_kaynak` · `ref_kaynak` · `limit_bps`), çürük beyan adıyla düzeltilmiş, kaldırmama gerekçesi a-d maddeli (`:69`, `:223`). Çivi: `tests/test_pano_durustluk_v280.py:303-347` — alan üretime bağlanırsa damga bayatlar ve **test kırmızıya döner**. |
| **B7** | 26 değer-eşitliği — ortamlar-arası 3 çift (P0-b / P2 reçetesi, WP6) | **KAPALI (2/3) + 1 YASAK DOSYA.** | **P0-b indi:** `dagit.sh:16` ve `:438-462` → canlıya `state/dagitim.json` (`deployed_sha` + damga + `kirli_gec_kullanildi`); çivi `tests/test_dagit_f9_beyan_v266.py`. **P2 indi:** `yerel_donmus_defter` damgası; çivi `tests/test_wp6_kucuk_kalemler_v268.py:111-162`. **#11** `guard.py` okuyucusuz alanı v268/`375abd5`'te mezar taşıyla kapandı. **Kalan tek kırmızı:** `landing.html` + `workflow.html` sabit sayıları → `meridian/web/**` **yasak listede**, bu turda dokunulmadı. |
| **B8** | M11 Ö-1 `broker_status` pano yan… | **DEĞERLENDİRİLEMEDİ** | **`neden` alanı girdide KESİK** (bkz. §0). Kalem adıyla kaydedildi, durumu **None + neden: girdi kesik**. Rol-1 bu satırı elle doğrulamalı. **Not:** §7'nin 2026-08-24 M11 girişi "broker_status pano yanlış-güveni (veto edilen plan 'gönderilecek' görünüyor)" satırını **tehlikeli bulgu** olarak zaten tahtaya işlemiş — yani kalem **muhtemelen açık bir bulgu**, "zaten kapalı" değil. **Bu çelişki Rol-1'de çözülmeli.** |

---

## 5. KOŞULMAYANLAR — sessiz kesme YOK

| id | neden | çakışan/engelleyen yol |
|---|---|---|
| **K3** | **Dosya çakışması** — başka ajan uçuşta | `/Users/erdemozturk/AI-Trading/research/edgar_facts/earnings_8k_tarihleri.csv` |
| **K6** | **Dosya çakışması** — başka ajan uçuşta | `/Users/erdemozturk/AI-Trading/meridian/hermes.py` · `/Users/erdemozturk/AI-Trading/tests/test_zincir_kunye_v246.py` |
| **K4** | **DURUM BİLİNMİYOR** — icra/doğrulama kaydı raportöre ulaşmadı | Yalnız ileri-atıf var: M11 kova-6 gerekçesinde *"kalan Ö-5…Ö-8 **K4 kalemi** olarak ayrıldı"*. Koşuldu mu koşulmadı mı **söylenemez**. |
| **K5** | **DURUM BİLİNMİYOR** — icra/doğrulama kaydı raportöre ulaşmadı | Yalnız ileri-atıf var: WP7-31 gerekçesinde *"Ailenin açık kalan tek bacağı **WP7-40 (K5)**"*. Koşuldu mu koşulmadı mı **söylenemez**. |

**Ayrıca bu turda bilerek dokunulmayan yüzeyler** (yasak liste, başka ajanlar uçuşta):
`meridian/web/**` · `meridian/api.py` · `meridian/marketview.py` · `tests/test_pano_*` ·
`tests/test_jeton_*` · `tests/test_tasarim_*` · `tests/test_renk_*` · `tests/test_tipografi_*` ·
`tests/test_yazitipi_*` · `tests/test_seri_ucu_v281.py` · `tests/test_wp2d_pano_beyani_v246.py` ·
`ROADMAP.md` · `research/olcumler/yazi_tipi_2026-08-24/**` ·
`research/olcumler/dub_donusumu_2026-08-24/**` · `docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md` ·
`docs/AYIKLAMA-DUB-ANALYTICS-2026-08-24.md`.
Bunun **doğrudan sonucu:** B7'nin kalan kırmızısı (`landing.html`/`workflow.html` sabit sayıları)
ve B3'ün pano bacağı bu gece **kapatılamadı**.

---

## 6. TAHTAYA İŞLENECEK SATIRLAR (Rol-1 kopyalayıp yapıştıracak)

> **Uyarı:** aşağıdaki bloklar `ROADMAP.md`'ye **uygulanmadı**. Uygulamadan önce §4-B8'deki
> çelişkiyi çözün.

### 6.1 → `## §7 KARAR GÜNLÜĞÜ` — **EN ÜSTE**, bu sırayla (tek satır + tarih)

```markdown
- **2026-08-24 GECE KARŞIT-DOĞRULAMA TURU (2 icra çifti · 1 kapandı · 1 düştü):** her icra iddiası bağımsız doğrulayıcıyla karşılandı — `EDG-2026-056` **doğrulanarak KAPANDI** (izole ağaçta yeniden üretim BYTE-AYNI, sha `c1092218…`; hüküm kırılmaya çalışıldı, kırılmadı), `EDG-2026-053` **"kapandı" iddiası DÜŞTÜ → kısmen** (aşağıda). Ayrıca tahtanın **8 satırı bayat** çıktı (M8-U2/U3 · M11 kova-6 · F8 · EXE-009 · WP7-31a/b · M11 Ö-3/Ö-4 · 26-değer-eşitliği P0-b/P2 · [8.'si girdi kesik]) — hiçbiri iş değil, tahta bakımı. **K3/K6 dosya çakışmasından koşulmadı; K4/K5'in kaydı hiç ulaşmadı.** Ayrıntı: `docs/GECE-TURU-2026-08-24-ROADMAP.md`.
- **2026-08-24 `EDG-2026-053` (GELİR MOMENTUMU) KOŞULDU — HÜKÜM YOK, KART AÇIK KALIR (blok birimi Rol-1'e düşer):** ölçüm zanaatı sağlam (dört nokta tahmini panelden bağımsız birebir yeniden üretildi; şasi sha'ları 050 ile aynı; PK geçti; karta dokunulmadı; gerçek PIT ihlali de bulunamadı) **AMA karar kuralı mekanik olarak çözülmedi**: kart "21g blok-bootstrap" derken şablon birimi **işlem günü**ydü (EDG-050), bu ölçümde **ay-sonu** okundu → blok ≈ 21 ay, `n_blok=10`. **Birim tersine dönünce hüküm de dönüyor:** blok=21'de "hiçbir dal eşleşmedi", blok=1'de `ivme_ust_30pct @60g` CI `[+0,000086; +0,008653]` 0-DIŞI ve net10bps=+0,003473>0 → **DAL-1 ATEŞLEME şartı TAM eşleşiyor**. Kırılganlık şerhi yalnız **zayıflatan** yönü yazmış (YASA 4 sınıfı tek-yönlü sunum). Tek 0-dışı hücre (`yoy@20g lo=+0,000330`) ay-düzeyi çıkarımda 0-İÇİ (t=1,58; NW t=1,34…1,55), blok genişliği ters yönde daralıyor (0,005552→0,003124) ve permütasyon sınamasında `lo>0` oranı 0,27 → **sıralama gürültüsünden ayırt edilemiyor**. PIT "yıkıcı sınaması" **totolojik** (`f(x)` vs `f(idempotent_filtre(x))` → ihlal 0 çıkmak zorunda, kanıt değeri sıfır). Kart sonrası eklenen `BAYAT_CEYREK_GUN=200` guard'ı 2.388 gözlem düşürdü, **duyarlılık koşusu yok** (ikinci serbest parametre). Depoda `edg053`'e değen **hiçbir test yok** — kapanışı hiçbir kapı korumuyor. **AÇILIŞ ŞARTI: (1) blok biriminin adlandırılması, (2) her iki okumanın karar tablosuna yazılması, (3) 200g guard duyarlılığı, (4) gerçek yıkıcı PIT sınaması.**
- **2026-08-24 `EDG-2026-056` (SPLIT ORAN-İMZASI) ÖLÇÜLDÜ — HÜKÜM: YETERSİZ, dedektör KABLOLANMAZ:** aday 55 · eşleşen 32 · yakalanmayan 60/92 → **YP %41,8 · yakalama %34,8**, çıta (YP≤%20 VE yakalama≥%80) **DÜŞTÜ** → *"imza tek başına yetersiz — körlük BEYANLI kalır"*; `grep ratio_signature|oran_imza meridian/` = **0** (motor temiz). Eşik donukluğu `stat birth==mtime` ile kanıtlı (tolerans 02:58:55, yer gerçeği 02:59:30, test 02:59:51 — hepsi ölçümden ÖNCE), karta ve `state/`e dokunulmadı, ELEME-WP4 belgesi **append-only** güncellendi. Hüküm üç yoldan zorlandı, kırılmadı: merdivenin üç basamağı da düşüyor (F=1,25/1,5/2,0) ve yapısal YP'ler (3:2 bandı, 8 aday) tamamen silinse bile YP=%31,9>%20. **İKİ SAYI KUSURU DÜZELTİLECEK:** `RAPOR.md:45` "92 olay / **61** sembol" → doğrusu **60** (61, `bars_integrity`'nin tüm-sınıf `sembol_sayisi`'dır); `RAPOR.md:128` *"hepsi 3:2 bandına düşüyor"* → **yanlış**, hayalet(5)+sıçra-dön(8)+3:2(7) düşünce **3 aday sınıflandırılmadan kalıyor** (CMCSA 2006-10-24 · CMCSA 2013-12-19 · DLTR 2012-06-26) ve hiçbiri o bantta değil. **İKİ TESCİL BEKLİYOR:** ters-split yönünün dahil edilmesi (karta AYKIRI ama ölçümden önce beyanlı + karşı-olgulu) ve hacim toleransı **F=1,5**'in icadı (kartta yoktu, "kart boşluğu" diye donduruldu) — ikisi de hükmü taşımıyor, Rol-1 tescili gerekir.
```

### 6.2 → `## §2 TAHTA` — satır düzeltmeleri

**(a) `H1 — TASARIM VAR, ölçüm/uygulama bekliyor` tablosuna EKLENECEK satır:**

```markdown
| `EDG-2026-053` blok-birimi hükmü | WP4 | `research/cards/EDG-2026-053-gelir-momentumu.yaml` (`registered`) · `research/olcumler/edg053_gelir_momentumu_2026-08-24/` | **AÇIK — ölçüm koştu, HÜKÜM YOK.** Karar kuralı blok biriminin (21 işlem günü ↔ 21 ay) adlandırılmasına bağlı; blok=1'de kart ATEŞLİYOR, blok=21'de eşleşmiyor. 4 açılış şartı: birim adı · çift-okuma karar tablosu · `BAYAT_CEYREK_GUN=200` duyarlılığı · gerçek yıkıcı PIT sınaması. Kanıt: `docs/GECE-TURU-2026-08-24-ROADMAP.md` §3 |
```

**(b) `H6 ✅` sınıfına GEÇECEK satır:**

```markdown
| `EDG-2026-056` split oran-imzası | WP4 | `research/olcumler/edg056_oran_imzasi_2026-08-24/` · `docs/ELEME-WP4-HAVUZ-2026-08-23.md` (A4 kapanışı) | **H6 ✅** — hüküm: YETERSİZ (YP %41,8 / yakalama %34,8, çıta düştü), dedektör kablolanmadı, körlük BEYANLI kalır. Kanıtı §7'de. **Kalan iş: karta hüküm damgası (status hâlâ `registered`) + 2 sayı kusuru + 2 tescil** |
```

**(c) BAYAT olduğu KANITLANAN satırlara düşülecek not** *(SİLME YOK — satırlar yerinde kalır, not eklenir)*:

```markdown
**[2026-08-24 gece karşıt-doğrulama: aşağıdaki 7 satır BAYAT — kalemler kapalı, tahta açık gösteriyordu. Kanıt tek tek `docs/GECE-TURU-2026-08-24-ROADMAP.md` §4'te.]**
· `M8 U2/U3 kart hijyeni` → 68 kartın yalnız 8'i `pending-` taşıyor ve 8'i de ölçülmemiş kart (`registered`/`measuring`) = DOĞRU hâl; `ops/kart_endeksi_uret.py --kontrol` → `GÜNCEL` (çıkış 0); çivi `tests/test_kart_hijyeni_v279.py`. Kalan tek gerçek karar **U6** (kart-K ↔ DSR `n_trials` bağı) ve o Rol-1'in.
· `M11 kova-6 alan merceği taraması` → `docs/TARAMA-KOVA6-ALAN-MERCEGI-2026-08-24.md` mevcut (26 plan alanı + 14 `entry_law` alt-alanı, kalibrasyon 3/3); Ö-3/Ö-4 indi, Ö-5…Ö-8 K4'e ayrıldı.
· `F8 kanonik durum sözlüğü uygulaması` → `meridian/durum_sozlugu.py` mevcut ve üç yüzeye kablolu (`watchdog.py:202/515/1347/1782/3053` · `api.py:3087-3089/3166` · `hermes_runtime.py:643-647`); "Sıradaki: kanonik sözlük uygulaması" satırı BAYAT. Kalan: A1-A8 soruları (Rol-1/operatör) + pano bacağı (`web/**` + `api.py`, yasak liste).
· `EXE-2026-009 pencere kaydırma` → kod indi: `barclock.py:144/147/150`, damga `loop.py:700/1470/2571`, kapı `intraday_cycle.py:90/172`, okuyucu `edg042_kosum_2026-08-22/pencere_altbant.py`. **§5'teki "operatör-bekliyor" BAYAT** — karar 2026-08-23 K2'de verildi.
· `WP7-31a/31b hermes künye + active_model uydurma koruması` → `hermes.py:2185 cevap_veren_model()`, künye `:3748`/`:4269`, tüketen-okuma sözleşmesi `:4178`; `active_model()` `_model_id`'ye delege. Ailenin açık tek bacağı **WP7-40**.
· `M11 Ö-3/Ö-4 entry_law ölü alanları` → `broker.py:255` ÖLÜ-ALAN DAMGASI[M11] bloğu indi (`olay`/`offset_kaynak`/`ref_kaynak`/`limit_bps`), çürük "okuyucusu E2" beyanı adıyla düzeltildi; çivi `tests/test_pano_durustluk_v280.py:303-347`.
· `26 değer-eşitliği — ortamlar-arası 3 çift` → **P0-b indi** (`dagit.sh:16/438-462` → canlıya `state/dagitim.json`; çivi `tests/test_dagit_f9_beyan_v266.py`), **P2 indi** (`yerel_donmus_defter` damgası; çivi `tests/test_wp6_kucuk_kalemler_v268.py:111-162`), **#11** `guard.py` v268/`375abd5`'te mezar taşıyla kapandı. **KALAN TEK KIRMIZI:** `landing.html` + `workflow.html` sabit sayıları — `meridian/web/**` yasak listede, gece turunda AÇILAMADI.
```

**(d) YENİ satır — koşulamayanların kuyruğu** *(H1 ya da BLOKE, Rol-1 seçer)*:

```markdown
| gece turu kalıntısı (K3 · K6) | — | `docs/GECE-TURU-2026-08-24-ROADMAP.md` §5 | **BLOKE (dosya çakışması, iş değil sıra sorunu).** K3 → `research/edgar_facts/earnings_8k_tarihleri.csv`; K6 → `meridian/hermes.py` + `tests/test_zincir_kunye_v246.py`. Uçuştaki ajanlar inince tek turda koşulur. **K4/K5'in hiçbir icra/doğrulama kaydı ulaşmadı — durumları BİLİNMİYOR, Rol-1 sınıflandırmalı.** |
```

---

## 7. SABAH OPERATÖRE — karar bekleyen ne çıktı

> Kolon "kim": **Rol-1** = mimari/hüküm işi, operatör imzası gerekmez. **OPERATÖR** = imza gerekir.

| # | karar | kim | neden şimdi | maliyet |
|---|---|---:|---|---|
| **1** | **`EDG-2026-053`'ün blok birimi nedir — 21 işlem günü mü, 21 ay mı?** | **Rol-1** | **Gecenin tek gerçek çatalı.** Cevap kartın ateşleyip ateşlemediğini belirliyor: blok=1'de `ivme@60g` CI `[+0,000086; +0,008653]` → DAL-1 ATEŞLEME; blok=21'de "hiçbir dal eşleşmedi". Karar verilmeden 053 ne kapanabilir ne açılabilir. | Yalnız hüküm — K harcamaz |
| **2** | **053 yeniden koşulacak mı?** (200g guard duyarlılığı + gerçek yıkıcı PIT sınaması + çift-okuma karar tablosu) | **Rol-1** → K bütçesi **OPERATÖR** | Mevcut PIT kanıtı totolojik (kanıt değeri sıfır) ve 2.388 gözlem düşüren guard'ın etkisi ölçülmemiş. Şu hâliyle 053 **ARSENAL'a aday gösterilemez**. | **K harcar** — grid çarpımı Rol-1'de |
| **3** | **`EDG-2026-056` kartına hüküm damgası** (status hâlâ `registered`) | **Rol-1** | Ölçüm ajanı karta dokunmaz (CLAUDE.md md.3); hükmü Rol-1 işler. Damgalanmazsa kalem kart endeksinde ölçülmemiş görünmeye devam eder. | Dakikalar |
| **4** | **056'nın iki tescili:** (a) ters-split yönünün dahil edilmesi — **karta AYKIRI** ama ölçümden önce beyanlı + karşı-olgulu; (b) hacim toleransı **F=1,5** — kartta yoktu, "kart boşluğu" diye donduruldu | **Rol-1** | İkisi de hükmü **taşımıyor** (merdiven üç basamakta da düşüyor). Ama "eşik sonradan değişmez" disiplini açısından yazılı tescil gerekir, yoksa emsal olur. | Dakikalar |
| **5** | **056'nın iki sayı kusuru düzeltilecek mi?** `RAPOR.md:45` (61→**60** sembol) · `RAPOR.md:128` ("hepsi 3:2" → **3 aday sınıflandırılmamış**) | **Rol-1** | Hükmü değiştirmez ama "kanıtla-iddia-etme" ilkesinin doğrudan kapsamında. **SİLME YOK** gereği üstü çizilip düzeltme eklenmeli. Not: 3 aday sınıflandırılırsa yer gerçeğinin eksikliği **büyüyebilir** — hükmü aynı yöne iter. | Dakikalar |
| **6** | **§4-B8 ÇELİŞKİSİ:** M11 Ö-1 `broker_status` pano yanlış-güveni — "zaten kapalı" mı, **açık tehlikeli bulgu** mu? | **Rol-1** | Girdi kesik geldi (§0), gerekçe **yok**. Ama §7'nin 2026-08-24 M11 girişi bunu *"veto edilen plan 'gönderilecek' görünüyor"* diye **tehlikeli bulgu** olarak kaydetmiş. İkisi aynı anda doğru olamaz — ve bu bir **canlı pano yanlış-güveni** kalemi. | Elle doğrulama |
| **7** | **U6:** kart-K ↔ DSR `n_trials` bağı | **Rol-1** | M8 U2/U3'ten geriye kalan **tek gerçek karar**; kart hijyeninin kendisi kapandı. | Mimari hüküm |
| **8** | **F8'in A1-A8 soruları** | Rol-1 / **OPERATÖR** | Kanonik sözlük **uygulaması** indi; kalan yalnız bu sorular + pano bacağı. Pano bacağı `meridian/web/app.js` + `meridian/api.py`'de → **başka ajan uçuşta, bu gece açılamadı**. | Karar |
| **9** | **B7'nin kalan kırmızısı:** `landing.html` + `workflow.html` sabit sayıları | Rol-1 | Değer-eşitliğinin 3 çiftinden 2'si (P0-b, P2) ve #11 kapandı; bu tek kalem `meridian/web/**` yasak listesi yüzünden **iki turdur açılamıyor**. Uçuş bitince ilk sıraya alınmalı. | Küçük |
| **10** | **K3/K6 yeniden kuyruğa · K4/K5 sınıflandırılsın** | Rol-1 | K3/K6 iş değil **sıra** sorunu (dosya çakışması). K4/K5'in hiçbir kaydı ulaşmadı — koşuldu mu bilinmiyor, uydurulmadı. | Sıralama |

---

### Kapanış notu — bu turda dokunulan/dokunulmayan

| | |
|---|---|
| **Bu raporun yazdığı tek dosya** | `docs/GECE-TURU-2026-08-24-ROADMAP.md` |
| **DOKUNULMADI** | `ROADMAP.md` · `state/**` (yalnız okundu) · `research/cards/**` · `meridian/**` · yasak listenin tamamı |
| **Koşulan testler** | yalnız kapsam: `research/olcumler/edg056_oran_imzasi_2026-08-24/test_tara.py` (`7 passed`). **Tam suite KOŞULMADI** (tek-otoriter, Rol-1'de). |
| **Git** | **hiçbir git komutu koşulmadı** (ajan yasağı). |
