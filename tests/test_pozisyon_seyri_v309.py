"""v309 · "AÇIK POZİSYONLARIN SEYRİ" GRAFİĞİ AÇIK POZİSYON DEFTERİYLE TUTMUYOR.

Bu turda BAĞIMSIZ olarak yeniden ölçülen üç kusur (`ui/src/pano/yuzeyler/portfoy/`):

(1) SAYAÇ YALAN SÖYLÜYOR. Dürüstlük kutusu "N pozisyonun M'i çizildi" derken M =
    `cizim.seriler.length`, yani ADAY sayısı. Aday olmak ÇİZİLMEK DEĞİLDİR: girişi
    pencerenin SON seansında olan bir pozisyonun serisi TEK NOKTALIDIR ve recharts o
    seriyi SIFIR PİKSEL çizer (d3 `line()` tek non-null noktada `M x,y Z` üretir; sıfır
    uzunluklu alt-yol + `stroke-linecap: butt` = ekranda hiçbir şey). Sayaç onları
    "çizildi" kovasına yazınca kutu, ekranda olmayan çizgileri sayıyordu.

(2) BROKER-ONLY POZİSYON YAPISAL OLARAK DÜŞÜYOR ve nedeni YANLIŞ ADRESE gönderiyordu.
    Açılış damgası `birlestir()` içinde YALNIZ kitap satırından okunuyor (`k.ts_open`);
    `BrokerPozisyonu` (tipler.ts) symbol/qty/avg_entry/current/upl taşır, TARİH TAŞIMAZ.
    Yani yalnız aynada olan bir pozisyon (bugün NVDA) hiçbir zaman çizilemez ve bu bir
    veri boşluğu değil, aynanın ŞEKLİDİR. Neden cümlesi bunu söylemeliydi.

(3) AYNI EKRANDA İKİ YÜZDE. Tablo "K/Z %" ile grafiğin göstergesi aynı sembolde farklı
    sayı gösterebiliyor ve ekranda hiçbir yerde NEDEN yazmıyordu. ÖLÇÜLEN neden:
    `PozisyonTablosu` `s.kzYuzde`yi basar — `(sonFiyat − giris) / giris`, payı BROKER
    `current` (yoksa /api/market kapanışı). Bu grafik ise `(kapanış / giris − 1)` —
    payı `/api/bars` EOD KAPANIŞI. TABAN (`s.giris`) İKİSİNDE DE AYNI ALANDIR; ayrışma
    PAYDAN gelir. Beyan bu yüzden "kitap tabanı" diye YAZILAMAZ (uydurma olurdu);
    yazılması gereken, iki yüzdenin hangi fiyat kanalından okunduğudur.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. Tek noktalı serinin `dot`u — `seansSayisi < 2` koşuluyla, ÇAĞRI BİÇİMİ regex'le.
B. Üç kovalı sayaç — "çizilen" kovası tek-seanslıkları DIŞARIDA bırakmalı (çıkarma
   ifadesi çivili), ve kutunun BASTIĞI DEĞİŞKEN çivili: kovaların ADI ekranda dururken
   sayının `cizim.seriler.length`e geri dönmesi hem pytest'i hem tsc'yi YEŞİL bırakırdı,
   yani kusur sessizce geri gelirdi. Tek-seanslıklar KENDİ NEDENLERİYLE listelenmeli.
C. Broker-only düşme nedeni — `nerede === "yalniz-broker"` dalı ve YAPISAL cümle,
   açılış-tarihi dalının İÇİNDE (başka bir yerde duran bir dizge kanıt değildir).
D. Taban/pay beyanı — ekranda, ve `girisKaynak`tan VERİYLE beslenerek (sabit cümle değil).
   Tablonun YEDEK fiyat kanalı DOĞRU ADLANDIRILMALI: `birlestir.ts::piyasaFiyati` ÖNCE
   `intraday_close` (seans içi) döner, `close` (EOD) yalnız onun da yedeğidir. Beyanı
   "/api/market kapanışı" diye yazmak, okuyucuya yanlış kanalı adres göstermekti.
E. Tek-seanslık satırının NEDENİ ÖLÇÜLMÜŞ olmalı: "bar serisi bu tarihten sonrasını
   taşımıyor" cümlesi HİÇ ÖLÇÜLMEMİŞTİ — seri o tarihten sonra pekâlâ devam ediyor,
   kapanışları okunamıyor olabilirdi. Yerine ham serinin SON SEANSI ölçülüp basılıyor.
F. Kaynaktaki çıpalar SEMBOL olmalı (`dosya.py:NNN` yasak — depo yasası).

ALT-DİZGE TUZAĞI: bütün çiviler YORUMLARI SİLİNMİŞ kaynak üzerinde koşar. Bu dosyanın
kapattığı kusurların gerekçeleri kaynağın kendi yorumlarında da geçiyor; yorumlu metinde
arama yapmak, silinmiş bir davranışı mezar taşı yüzünden yaşıyor sanmak olurdu.

VARLIK KONTROLÜ KANIT DEĞİLDİR: `"entry" in beyan` çivisi `avg_entry` yüzünden ASLA
ötmezdi, `re.search("EOD", beyan)` ise değişiklikten ÖNCEKİ cümleyle de sağlanıyordu.
Bu yüzden buradaki çiviler ya KAPSANMAYAN bir çıpaya (`kitap entry`) ya da yeni beyanın
ÇAĞRI/CÜMLE BİÇİMİNE (`buradaki pay /api/bars EOD KAPANIŞI`) bağlanır.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
SEYIR_YOLU = REPO / "ui" / "src" / "pano" / "yuzeyler" / "portfoy" / "PozisyonSeyri.tsx"
HAM = SEYIR_YOLU.read_text(encoding="utf-8")


def _blok_yorumsuz(src: str) -> str:
    """`/* ... */` bloklarını AYNI SATIR SAYISINI koruyarak siler.

    Satır sayısı korunuyor ki hata mesajındaki bağlam ham dosyayla hizalı kalsın."""
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.DOTALL)


def _yorumsuz(src: str) -> str:
    """Blok yorumları siler, ardından SATIR BAŞI `//` yorum satırlarını atar.

    NEDEN SATIR-SONU `//` TARANMIYOR: bu dosyada JSX metni tırnaksız kesme işareti
    taşıyor (`{n}'i çizildi`), yani "dizgileri maskele sonra `//` ara" deseni burada
    kaynağı BOZAR — maskeleme kesme işaretini dizgi başlangıcı sanıp satırın yarısını
    yutar. Bunun yerine `test_stripper_hala_gecerli` satır-sonu yorumu OLMADIĞINI
    doğruluyor; bir gün eklenirse o çivi öter ve stripper bilerek sertleştirilir."""
    return "\n".join(ln for ln in _blok_yorumsuz(src).splitlines() if not ln.lstrip().startswith("//"))


KOD = _yorumsuz(HAM)


def _jsx_ogeleri(etiket: str) -> list[str]:
    """`<Etiket ... />` kendinden-kapanan öğelerini çıkarır (yorumsuz kaynaktan).

    NEDEN REGEX DEĞİL TARAYICI: prop değerleri `<` taşıyabiliyor (`s.seansSayisi < 2`),
    yani "`<` görene kadar oku" deseni öğeyi ORTASINDAN keser ve çivi sessizce kör kalır —
    bu dosyanın kapattığı kusurun tam olarak testteki karşılığı olurdu. Süslü parantez
    derinliği sayılıyor: öğe, derinlik sıfırken gelen `/>` ile biter."""
    ogeler: list[str] = []
    for m in re.finditer(rf"<{etiket}\b", KOD):
        i = m.start()
        derinlik = 0
        j = m.end()
        while j < len(KOD):
            c = KOD[j]
            if c == "{":
                derinlik += 1
            elif c == "}":
                derinlik -= 1
            elif derinlik == 0 and KOD.startswith("/>", j):
                ogeler.append(KOD[i : j + 2])
                break
            j += 1
        else:
            raise AssertionError(f"<{etiket}> öğesi kapanmadı (indeks {i})")
    return ogeler


def _line_ogesi(imza: str) -> str:
    esleşen = [o for o in _jsx_ogeleri("Line") if imza in o]
    assert len(esleşen) == 1, f"`{imza}` taşıyan <Line> sayısı {len(esleşen)} (1 bekleniyordu)"
    return esleşen[0]


def _durustluk_kutusu() -> str:
    """Dürüstlük kutusunun JSX'i — `rounded-md border border-dashed` çıpasından sona."""
    i = KOD.find('className="rounded-md border border-dashed p-3"')
    assert i != -1, "dürüstlük kutusu çıpası kayboldu"
    return KOD[i:]


def _tek_seanslik_li() -> str:
    """Tek-seanslık kovasının listesi — `tekSeanslik.map(` çıpasından `</ul>`e.

    KUTUNUN TAMAMINDA aramak yetmez: aynı dizgeler düşenler listesinde ya da beyanın
    başka bir köşesinde de geçebilir, o zaman çivi tek-seanslık satırını değil komşusunu
    ölçmüş olurdu."""
    kutu = _durustluk_kutusu()
    i = kutu.find("tekSeanslik.map(")
    assert i != -1, "tek-seanslık listesi kayboldu"
    j = kutu.find("</ul>", i)
    assert j != -1, "tek-seanslık listesinin `</ul>` kapanışı bulunamadı"
    return kutu[i:j]


def test_stripper_hala_gecerli():
    """Yorum ayıklayıcının varsayımı: blok yorumları silindikten sonra kalan HER `//`
    satır başındadır. Satır-sonu yorumu eklenirse bu çivi öter — sessizce kör kalan bir
    ayıklayıcı, bütün alt-dizge çivilerini kanıtsız bırakırdı."""
    for no, ln in enumerate(_blok_yorumsuz(HAM).splitlines(), 1):
        if "//" in ln and not ln.lstrip().startswith("//"):
            raise AssertionError(f"{SEYIR_YOLU.name}:{no} satır-sonu `//` yorumu — ayıklayıcı sertleştirilmeli")


# ==============================================================================================
# A · TEK NOKTALI SERİ GÖRÜNÜR
# ==============================================================================================
def test_tek_seanslik_seri_NOKTA_olarak_cizilir():
    """`dot` yalnız `seansSayisi < 2` iken açılır. Koşulsuz `dot` bütün 90 seansı noktalarla
    doldurup grafiği okunmaz yapardı; `dot={false}` ise tek noktalı seriyi GÖRÜNMEZ bırakıp
    sayacı yalancı çıkarıyordu (kusur 1)."""
    oge = _line_ogesi("dataKey={s.anahtar}")
    assert re.search(r"dot=\{\s*s\.seansSayisi\s*<\s*2\s*\?", oge), \
        f"pozisyon serisinin `dot`u tek-seanslık koşuluna bağlı değil:\n{oge}"
    assert re.search(r":\s*false\s*\}", oge), "çok seanslık seride `dot` kapatılmıyor — 90 nokta çizilir"


def test_ortalama_cizgisi_de_tek_noktada_gorunur():
    """Kesikli ortalama aynı geometriye tabi: veri TEK seanslıksa o da sıfır piksel çizer.
    Serilerde düzeltip ortalamada bırakmak, aynı kusuru yarım kapatmak olurdu."""
    oge = _line_ogesi('dataKey="ortalama"')
    assert re.search(r"dot=\{\s*cizim\.veri\.length\s*<\s*2\s*\?", oge), \
        f"ortalama çizgisinin `dot`u tek-noktalı veri koşuluna bağlı değil:\n{oge}"


# ==============================================================================================
# B · SAYAÇ ÜÇ KOVA
# ==============================================================================================
def test_tek_seanslik_kova_serilerden_TURETILIR():
    assert re.search(
        r"tekSeanslik\s*=\s*cizim\.seriler\.filter\(\((\w+)\)\s*=>\s*\1\.seansSayisi\s*<\s*2\)", KOD
    ), "`tekSeanslik` kovası `seansSayisi < 2` ile serilerden türetilmiyor"


def test_cizilen_kovasi_tek_seansliklari_DISARIDA_birakir():
    """Çizilen sayısı `seriler.length` OLAMAZ: aday olmak çizilmek değildir. Çıkarma
    ifadesi ADIYLA BİRLİKTE çivili — hesap doğru olup da kutunun başka bir değişkeni
    basması mümkündü, o yüzden bağ (`cizilenCizgi`) da ölçülüyor."""
    assert re.search(r"const cizilenCizgi\s*=\s*cizim\.seriler\.length\s*-\s*tekSeanslik\.length", KOD), \
        "çizilen kovası `cizilenCizgi` adıyla tek-seanslıkları düşmüyor — sayaç yine ekranda olmayan çizgileri sayar"


def test_durustluk_kutusu_UC_KOVAYI_da_yazar():
    """KOVANIN ADI DEĞİL, BASILAN DEĞİŞKEN çivilenir. "çizildi" kelimesinin kutuda
    bulunması hiçbir şey ölçmez: kutu `{cizim.seriler.length}'i çizildi` bassa da o çivi
    yeşil kalırdı — yani kapatılan kusur (aday sayısını çizilen sanmak) aynen geri
    gelebilirdi ve ne pytest ne tsc bunu görürdü. Üç kovanın ÜÇÜ de kendi değişkeniyle
    eşleştirilmiş biçimde aranıyor."""
    kutu = _durustluk_kutusu()
    assert re.search(r"\{satirlar\.length\}\s+pozisyonun\s+\{cizilenCizgi\}'i çizildi", kutu), \
        "kutu ÇİZİLEN kovasını `cizilenCizgi` ile basmıyor — aday sayısına geri dönmüş olabilir"
    assert re.search(r"\$\{tekSeanslik\.length\}'i tek seanslık", kutu), \
        "tek-seanslık SAYISI kendi kovasının cümlesinde basılmıyor"
    assert re.search(r"\$\{cizim\.dusenler\.length\}'i çizilemedi", kutu), \
        "çizilemeyen SAYISI kendi kovasının cümlesinde basılmıyor"
    assert "çizgi iki nokta ister" in kutu, "tek-seanslık kovasının NE DEMEK olduğu yazılı değil"


def test_tek_seansliklar_KENDI_NEDENLERIYLE_listelenir():
    li = _tek_seanslik_li()
    assert "sıfır piksel" in li, "tek noktanın NEDEN görünmediği (sıfır piksel) yazılı değil"
    assert re.search(r"gunAyYil\(s\.ilkSeans\)", li), "tek-seanslık serinin O SEANSI yazılmıyor"


def test_tek_seanslik_nedeni_OLCULMUS_seri_sonuna_dayanir():
    """UYDURMA YASAĞI, EKRAN METNİNDE DE GEÇERLİ. "bar serisi bu tarihten sonrasını
    taşımıyor" cümlesi hiç ölçülmemişti: seri o tarihten sonra devam ediyor da olabilir
    (`c` alanı sayıya çevrilemeyen barlar noktaya dönüşmeden düşüyor). Cümle ham serinin
    ÖLÇÜLEN son seansına bağlandı; "seri burada bitiyor" iddiası artık yalnız ölçüm onu
    doğruluyorsa (`sonBarTarihi === ilkSeans`) basılıyor."""
    li = _tek_seanslik_li()
    assert "bar serisi bu tarihten sonrasını taşımıyor" not in li, \
        "ölçülmemiş nedensel kuyruk hâlâ ekranda — seri o tarihten sonra devam ediyor olabilir"
    assert re.search(r"s\.sonBarTarihi === s\.ilkSeans", li), \
        "\"seri burada bitiyor\" iddiası ölçüme (ham serinin son seansına) bağlı değil"
    assert re.search(r"gunAyYil\(s\.sonBarTarihi\)", li), \
        "seri devam ediyorsa ham serinin ÖLÇÜLEN son seansı basılmıyor"
    assert re.search(r"\$\{s\.kapanissizBar\}", li), \
        "noktaya çevrilemeyen bar SAYISI basılmıyor — 'neden tek nokta' yine ölçüsüz kalır"


def test_seri_sonu_ve_kapanissiz_bar_HAM_SERIDEN_olculur():
    """Ekrandaki sayının arkasında gerçek bir sayım olmalı: `sonBarTarihi` ham barların
    tarihinden, `kapanissizBar` da kapanışı ayrıştırılamayan barlardan sayılır ve ikisi
    de çizim serisine TAŞINIR (taşınmazsa ekran onları okuyamaz)."""
    assert re.search(r"sonBarTarihi\s*=\s*t;", KOD), "`sonBarTarihi` ham bar tarihinden ölçülmüyor"
    assert re.search(r"if \(kapanis === null\) \{[^}]*kapanissizBar \+= 1;", KOD), \
        "kapanışı ayrıştırılamayan bar SAYILMIYOR — sessizce düşüyor"
    assert re.search(r"sonBarTarihi:\s*a\.sonBarTarihi", KOD), "`sonBarTarihi` çizim serisine taşınmıyor"
    assert re.search(r"kapanissizBar:\s*a\.kapanissizBar", KOD), "`kapanissizBar` çizim serisine taşınmıyor"


# ==============================================================================================
# C · BROKER-ONLY YAPISAL NEDEN
# ==============================================================================================
def _acilis_dali() -> str:
    """Açılış tarihi ölçülemedi dalı — koşulundan `continue;`ye kadar."""
    i = KOD.find("acilisGun === null || !TARIH_DESENI.test(acilisGun)")
    assert i != -1, "açılış tarihi dalının koşulu kayboldu"
    j = KOD.find("continue;", i)
    assert j != -1, "açılış dalının `continue;`si bulunamadı"
    return KOD[i:j]


def test_broker_only_neden_YAPISAL_ve_DOGRU_DALDA():
    """NVDA'nın nedeni "bar yok" değildir: aynada açılış damgası YOKTUR. Cümle açılış
    dalının İÇİNDE olmalı — dosyanın başka bir yerinde duran aynı dizge, o dalın hâlâ
    eski/yanlış cümleyi bastığı gerçeğini gizlerdi (alt-dizge tuzağı)."""
    dal = _acilis_dali()
    assert re.search(r'nerede === "yalniz-broker"', dal), \
        "açılış dalı broker-only durumunu AYIRMIYOR — yalnız aynada olan pozisyon kitap diliyle açıklanıyor"
    assert "aynada AÇILIŞ DAMGASI yok" in dal, "broker-only nedeni aynanın eksiğini adıyla söylemiyor"
    assert "GİRİŞTEN İTİBAREN çizilir" in dal, "seyrin girişten çizildiği söylenmiyor"
    assert "YAPISAL" in dal, "eksiğin YAPISAL olduğu (veri boşluğu değil) yazılmıyor"


def test_broker_only_nedeni_BAR_EKSIGI_diye_okunmaz():
    dal = _acilis_dali()
    assert re.search(r"bar eksiği DEĞİL", dal), \
        "neden, okuyucuyu hâlâ bar dosyasına gönderiyor olabilir — ayrım yazılı değil"


# ==============================================================================================
# D · TABAN / PAY BEYANI
# ==============================================================================================
def _beyan() -> str:
    i = KOD.find("Y ekseni GİRİŞE göre yüzde")
    assert i != -1, "ekran beyanının çıpası kayboldu"
    return KOD[i : KOD.find("</p>", i)]


def test_taban_ekranda_BEYAN_EDILIR():
    """Aynı ekranda iki farklı yüzde varsa, hangisinin neyi ölçtüğü YAZILI olmalı; yoksa
    okuyucu farkı kusur sanar (kusur 3).

    KİTAP ALANI `kitap entry` DİYE ARANIR: sade `"entry" in b` çivisi `avg_entry`nin
    içinden geçtiği için beyandan kitap tarafı tamamen silinse bile ÖTMEZDİ."""
    b = _beyan()
    assert re.search(r"broker\s+avg_entry", b), "tabanın broker alanı adıyla beyan edilmiyor"
    assert "kitap entry" in b, "tabanın kitap alanı adıyla beyan edilmiyor"
    assert "K/Z %" in b, "tabloyla karşılaştırma yapılmıyor — fark yine kusur gibi görünür"


def test_pay_farki_de_BEYAN_EDILIR():
    """Ayrışmanın ÖLÇÜLEN kaynağı paydır: burada EOD kapanış, tabloda broker `current`.

    `EOD` dizgesini ARAMAK KANIT DEĞİL: beyanda zaten "kaynak /api/bars — EOD kapanış"
    cümlesi vardı, yani pay karşılaştırması hiç yazılmasa da o çivi yeşildi. Çivi bu
    yüzden iki payı KARŞILAŞTIRAN cümlenin biçimine bağlandı."""
    b = _beyan()
    assert re.search(r"buradaki pay\s+/api/bars EOD KAPANIŞI", b), \
        "bu grafiğin payı (bars EOD kapanışı) tabloyla KARŞILAŞTIRAN cümlede beyan edilmiyor"
    assert re.search(r"tablodaki pay\s+broker current", b), \
        "tablonun payı (broker `current`) aynı karşılaştırmada beyan edilmiyor"


def test_tablonun_YEDEK_KANALI_DOGRU_adlandirilir():
    """ÖLÇÜLEN GERÇEK (`birlestir.ts::piyasaFiyati`): broker satırı yoksa ÖNCE
    `intraday_close` (seans içi kapanmış dakikalık bar) alınır, `close` (EOD) yalnız
    onun da yedeğidir. Beyanı "/api/market kapanışı" diye yazmak okuyucuyu yanlış
    kanala gönderiyordu — tablo seans içi bir fiyat basarken beyan EOD diyordu."""
    b = _beyan()
    assert re.search(r"ÖNCE seans içi intraday_close", b), \
        "tablonun İLK yedeği (seans içi `intraday_close`) beyanda adıyla geçmiyor"
    assert re.search(r"intraday_close.*?o da yoksa EOD close", b, re.DOTALL), \
        "EOD `close`un YEDEĞİN YEDEĞİ olduğu (sıra) beyanda yazılı değil"
    assert "/api/market kapanışı" not in b, \
        "yedek kanal hâlâ düz 'kapanış' diye adlandırılmış — seans içi fiyatı EOD sanan bir okuma üretir"


def test_taban_beyani_VERIDEN_beslenir_sabit_cumle_degil():
    """Beyan `girisKaynak`tan sayılmalı. Sabit bir cümle, bir gün taban değişirse
    sessizce yalan söylerdi — beyanın kendisi ölçüme bağlı olmalı."""
    assert re.search(r"girisKaynak", KOD), "`girisKaynak` bu yüzeyde hiç okunmuyor"
    assert re.search(r"girisKaynak === \"broker\"", KOD), "taban kaynağı sayılmıyor"
    b = _beyan()
    assert re.search(r"\{[^}]*[Tt]abanBroker[^}]*\}", b) or re.search(r"\{[^}]*girisKaynak[^}]*\}", b), \
        "beyan metni ölçülen taban dağılımını BASMIYOR"


# ==============================================================================================
# F · ÇIPALAR SEMBOL OLMALI
# ==============================================================================================
def test_kaynakta_SATIR_NUMARASI_capasi_yok():
    """Depo yasası: yorumdaki çıpa `dosya.py:NNN` olamaz — satır numarası ilk düzenlemede
    kayar ve okuyucuyu YANLIŞ satıra gönderir; sembol adı kaymaz. Bu çivi HAM kaynağı
    tarar (çıpalar yorumların içinde yaşıyor, yorumsuz metinde aranamaz)."""
    for no, ln in enumerate(HAM.splitlines(), 1):
        m = re.search(r"[\w./-]+\.(?:py|tsx?|css)\s*:\s*\d", ln)
        assert m is None, (
            f"{SEYIR_YOLU.name} {no}. satırda satır-numarası çıpası (`{m.group(0) if m else ''}`) — "
            "çıpa SEMBOL adıyla yazılmalı (`dosya.py::sembol`)"
        )
