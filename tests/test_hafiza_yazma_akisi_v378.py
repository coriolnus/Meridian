"""test_hafiza_yazma_akisi_v378.py — PANONUN İLK YAZMA YÜZEYİNİN BEKÇİSİ (2026-09-03).

TSK-111 dilim 1 ile pano ilk kez hafızaya YAZIYOR: işlem satırında iptal · yeniden dene ·
kaydı sil, ana sayfanın düşen-birleştirme penceresinde kurtar→tetikle zinciri. Bu dört
eylemin sözleşmesi ekranda yaşıyor ve sözleşmeyi bozan hiçbir regresyon `tsc`ye GÖRÜNMEZ:
rozetin sessizce geri gelmesi, durum kapılarının üst yüzeyden ayrışması, `retried_count`
yoluna bir `?? 0` sızması, ikinci bir `fetch` kapısının açılması — hiçbiri tip hatası
üretmez. Panonun yazan tek yüzeyini ölçüsüz bırakmak, ölçülmüş bir kapıyı açık bırakmaktır.

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI: bu dosya TSX'i METİN olarak okur — v286/v288/
v314/v323/v324/v373 ailesinin kurulu cevabı ("depoda `ui/` için test çatısı yok" bir engel
değil, bu ailenin çözdüğü problemdir). Ölçtüğü şey davranış DEĞİL, davranışı üreten satırın
varlığıdır. Bu zayıflık mutasyonla telafi edildi: 17 mutasyonun 17'si ısırdı — ve ilk turda
ÜÇÜ sağ kaldı, üçü de çivinin körlüğünü gösterdi (kilit deseni dosyadaki ikizini görüyordu ·
"vazgeç" ithal satırından sayılıyordu · "ham" kelimesi başka yerde de geçiyordu). Üçü de bu
dosyada SIKILAŞTIRILMIŞ hâlleriyle duruyor; gevşetilirlerse o üç mutasyon sessizce geçer.

ÖLÇÜMÜN KAYNAĞI ÜST YÜZEYDİR (Hindsight control plane @ ebad478240d3171bb88201ececda5e8d9883d22d):
durum kapıları `bank-operations-view.tsx` satır tablosundan (cancel/retry/delete), zincir sırası
ve `retried_count` `bank-stats-view.tsx::handleRecover`tan okundu. Aşağıdaki `OLCULEN_KAPILAR`
tablosu o ÖLÇÜMÜN kopyasıdır ve koddan TÜRETİLMEZ — türetseydi çivi kendini doğrulardı.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
HAFIZA = KOK / "ui/src/pano/yuzeyler/hafiza"
YAZMA = HAFIZA / "yazma.tsx"
ISLEMLER = HAFIZA / "Yapilandirma.tsx"
ANASAYFA = HAFIZA / "anasayfakartlari.tsx"
GONDER = KOK / "ui/src/pano/gonder.ts"

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy(p: pathlib.Path) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken YASAKLANAN
    ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır (v286'nın `_soy` dersi)."""
    return _YORUM.sub(" ", p.read_text(encoding="utf-8"))


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve
    çivi "temiz" der. Dosya varlığı ayrı ölçülür ki 'sıfır ihlal' bir okuma yokluğu olmasın."""
    for p in (YAZMA, ISLEMLER, ANASAYFA, GONDER):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 500, f"dosya beklenmedik biçimde küçük: {p}"


# ============================================================================
# (1) UÇ SÖZLEŞMESİ — vekilin yolları ve gövde alanları
# ============================================================================

def test_uc_yollari_vekil_sozlesmesiyle_ayni():
    s = soy(YAZMA)
    assert '"/api/hindsight/islem"' in s
    assert '"/api/hindsight/konsolidasyon/kurtar"' in s
    assert '"/api/hindsight/konsolidasyon/tetikle"' in s
    assert "`${UC_ISLEM}/${eylem}`" in s, "işlem eylemi yol kuyruğuna eklenmiyor"


def test_govde_bank_ve_id_alanlariyla_gider():
    s = soy(YAZMA)
    assert "{ bank, id: kimlik }" in s, "işlem gövdesi vekilin istediği iki alanı taşımıyor"
    assert s.count("{ bank }") >= 2, "kurtarma/tetikleme gövdesi banka alanını taşımıyor"


def test_tetikleme_UST_YUZEY_GIBI_GOVDESIZ_gider():
    """ÖLÇÜLDÜ (`lib/api.ts::triggerConsolidation`): üst yüzeyin istemcisi birleştirmeyi
    tetiklerken YALNIZ yöntem gönderiyor, gövde YOK. Vekil bir gözlem-kapsamı alanını beyaz
    listede tutuyor; onu göndermek üst servisin kendi varsayılanını sessizce değiştirirdi."""
    s = soy(YAZMA)
    assert "observation_scopes" not in s, "tetikleme çağrısına ölçülmemiş bir alan eklenmiş"


# ============================================================================
# (2) ÇİFT GÖNDERİM KİLİDİ — İKİ HAT, İKİ AYRI ŞEY
# ============================================================================

def test_kilit_REF_ile_kurulu_state_FOTOGRAFI_degil():
    """M-3/M1 DERSİ. İki ayrı kusur aynı satırda buluşuyordu:
    (a) kilit bir `useState` fotoğrafını okuyordu — aynı tikte gelen iki tıklama ikisi de
        `false` görürdü, yani 'iki hatlı kilit' iddiası tek hatta inerdi;
    (b) çivinin deseni dosyanın HERHANGİ bir yerindeki `if (ucusta) return;`i görüyordu ve
        pencere-kapanış kapısındaki ikizi, kilit silinse bile çiviyi yeşil tutuyordu.
    Kilit artık bir ref ve KENDİ GÖVDESİNDE aranıyor."""
    s = soy(YAZMA)
    assert "useRef(false)" in s, "kilit bir ref değil — aynı tikteki ikinci istek geçer"
    govde = re.search(r"async function uygula\(\) \{(.*?)\n  \}", s, re.S)
    assert govde, "onay eyleminin gövdesi okunamadı"
    g = govde.group(1)
    assert re.search(r"if \(kilit\.current\) return;\s*kilit\.current = true;", g), \
        "uçuşta erken dönüş yok — ikinci istek geçer"
    assert "kilit.current = false;" in g, "kilit bırakılmıyor — düğme ömür boyu kilitli kalır"


def test_onay_dugmesi_UCUSTA_kilitli():
    assert re.search(r"disabled=\{ucusta \|\| hedef === null\}", soy(YAZMA)), \
        "onay düğmesi uçuşta kilitli değil"


def test_ucusta_pencere_kapanmaz():
    """Yasa 6: sonucu okunmadan istek yok. Pencere uçuşta kapansaydı gerekçe hiç
    okunmadan yok olurdu."""
    s = soy(YAZMA)
    assert "onEscapeKeyDown" in s, "kaçış tuşu uçuşta pencereyi kapatabiliyor"
    assert re.search(r"onOpenChange=\{\(a\) => \{\s*if \(ucusta\) return;", s), \
        "uçuşta pencere kapanabiliyor — sonuç okunmadan kaybolur"


# ============================================================================
# (3) SONUCUN OKUNMASI — uydurma yasağı ekranda
# ============================================================================

def test_basarisizlikta_SUNUCUNUN_gerekcesi_ekranda():
    s = soy(YAZMA)
    assert "{b.neden}" in s, "sunucunun gerekçesi çizilmiyor"
    assert re.search(r"if \(!s\.ok\) \{\s*setSonuc\(s\);\s*return;", s), \
        "başarısızlık sonucu duruma yazılmıyor — pencere gerekçesiz kapanır"


def test_http_olculemediginde_SIFIR_YAZILMAZ():
    s = soy(YAZMA)
    assert "b.http === null ?" in s, "durum kodu ölçülemediğinde ayrı hâl çizilmiyor"
    assert 'neden="durum kodu ölçülemedi"' in s
    assert "http: 0" not in s, "ölçülemeyen durum kodu için sıfır uyduruluyor"


def test_KISMI_BASARI_pencerede_KALIR():
    """I-2: kısmi başarı ("kurtarıldı ama kuyruğa alınmadı") bir bildirime emanet edilemez —
    üst servisin ücretsiz tavanı dolduğunda bu, düğmenin EN OLASI sonucudur. Bildirim tek
    satır özet taşır; iki bacağın kodları ve gerekçesi pencerede durur."""
    s = soy(YAZMA)
    assert re.search(r"if \(s\.eksik !== null\) \{\s*toast\.warning\(s\.ozet\);\s*return;", s), \
        "kısmi başarıda pencere kapanıyor — en nüanslı mesaj dört saniyede kayboluyor"
    assert "toast.warning(s.ozet, {" not in s, "bildirime ayrıntı yüklenmiş — okuyucusu geçici"
    # M20 DERSİ: tek `in` kontrolü, KISMİ blok silinse bile BAŞARISIZLIK bloğundaki
    # kopyayı görüp yeşil kalıyordu. İki blok da ayrı ayrı sayılır.
    assert s.count("sonuc.bacaklar.map") == 2, \
        "bacak künyeleri iki sonuç bloğunun ikisinde birden çizilmiyor"
    assert s.count("<BacakSatiri ") == 2, "bacak satırı bileşeni bir blokta düşürülmüş"


def test_her_bacak_KENDI_kodunu_tasir():
    """M-6: tek `http` alanı KURTARMA bacağınındı, şerh ise TETİKLEME bacağının arızasını
    anlatıyordu — ölü ama yanıltıcı bir alan."""
    s = soy(YAZMA)
    assert "export interface YazmaBacagi" in s
    assert re.search(r"function bacak\(ad: string, z: YazmaZarfi\): YazmaBacagi", s)


def test_basarida_bildirim_ve_TAZELEME():
    s = soy(YAZMA)
    assert "toast.success(s.ozet)" in s
    assert re.search(r"setSonuc\(s\);\s*basarili\(\);", s), \
        "durum değiştiği hâlde okumalar tazelenmiyor"


def test_satir_ve_panel_tazelemeyi_BAGLIYOR():
    y, a = soy(ISLEMLER), soy(ANASAYFA)
    assert "basarili={tazele}" in y, "işlem satırı başarıdan sonra listeyi yeniden okumuyor"
    assert re.search(r"liste\.tazele\(\);\s*tazele\(\);", a), \
        "kurtarma sonrası liste ve sayaçlardan biri bayat kalıyor"


def test_basari_metni_DUGME_ETIKETINDEN_turetilmiyor():
    """M-9: `"Kaydı sil uygulandı"` dürüsttü ama Türkçesi tökezliyordu."""
    s = soy(YAZMA)
    assert "basariMetni" in s and "ozet: ISLEM_KUNYELERI[eylem].basariMetni" in s
    assert "} uygulandı`" not in s, "başarı cümlesi hâlâ düğme etiketinden kuruluyor"


# ============================================================================
# (4) DURUM KAPILARI — ÜST YÜZEYDEN ÖLÇÜLDÜ (kopya, türetim DEĞİL)
# ============================================================================

#: `bank-operations-view.tsx` @ ebad4782 satır tablosu: cancel 660 · retry 679 ·
#: delete 698-700 (detay penceresinde 877 / 893-894 / 910-912 aynısı).
OLCULEN_KAPILAR = {
    "iptal": ["pending"],
    "yeniden-dene": ["failed", "cancelled"],
    "sil": ["failed", "cancelled", "completed"],
}


def _kapilar() -> dict[str, list[str]]:
    s = soy(YAZMA)
    blok = re.search(r"export const ISLEM_KAPILARI[^=]*=\s*\{(.*?)\n\};", s, re.S)
    assert blok, "kapı tablosu okunamadı — desen bayat"
    out: dict[str, list[str]] = {}
    for m in re.finditer(r'"?([a-z-]+)"?:\s*\[([^\]]*)\]', blok.group(1)):
        out[m.group(1)] = re.findall(r'"([a-z_]+)"', m.group(2))
    return out


def test_kapi_matrisi_UST_YUZEYLE_ayrismaz():
    assert _kapilar() == OLCULEN_KAPILAR


def test_processing_hicbir_kapida_YOK():
    """Ölçüm sonucu: koşan bir işe bu üç düğmenin hiçbiri uygulanmıyor."""
    assert all("processing" not in v for v in _kapilar().values())


def test_durum_olculemediyse_HIC_dugme_cizilmez():
    assert re.search(r"if \(durum === null\) return \[\];", soy(YAZMA)), \
        "durum gelmediğinde ölçülmemiş bir durum uygulanabilir sayılıyor"


# ============================================================================
# (5) ROZET — DÖRT EYLEMDEN KALKTI, ÖTEKİLERDE DURUYOR
# ============================================================================

def test_dort_eylemden_rozet_KALKTI():
    y, a = soy(ISLEMLER), soy(ANASAYFA)
    for etiket in ("İptal et", "Yeniden dene", "Kaydı sil"):
        assert f">{etiket}</Faz2Dugme>" not in y, f"{etiket} hâlâ devre dışı rozetli"
    assert "Faz2Dugme" not in a, "ana sayfa panelinde devre dışı düğme kaldı"


#: Yolu HÂLÂ AÇILMAMIŞ yazma düğmelerinin yaşadığı dosyalar. Rozet bir YETENEK BEYANIdır:
#: yolu açılmayan bir düğmeden kalkarsa ekran yalan söyler. `Reflect.tsx` kendi sabitini
#: taşıyor (`REFLECT_ROZET`) — tek sayımla kaçırılırdı (inceleme bulgusu M-8).
#: İM, İTHAL ADI DEĞİL ÇİZİM/BEYAN SATIRIDIR (M22 dersi): `REFLECT_ROZET` sabiti yeniden
#: adlandırıldığında kelime kullanım yerlerinde hâlâ geçiyordu ve çivi yeşil kalıyordu.
ROZETLI_KALAN = {
    "Yapilandirma.tsx": "<Faz2Dugme",
    "Bellekler.tsx": "<Faz2Dugme",
    "Belgeler.tsx": "<Faz2Dugme",
    "BilgiTabani.tsx": "<Faz2Dugme",
    "ZihinModelleri.tsx": "<Faz2Dugme",
    "Reflect.tsx": "const REFLECT_ROZET =",
}


def test_OTEKI_yazma_dugmeleri_ROZETLI_KALIR():
    eksik = [ad for ad, im in ROZETLI_KALAN.items() if im not in soy(HAFIZA / ad)]
    assert not eksik, (
        f"{len(eksik)} yüzey devre dışı rozetini kaybetti: {eksik} — yolu açılmamış bir "
        f"düğmeden rozet kalkarsa ekran var olmayan bir yeteneği beyan eder")


#: Yapılandırma yüzeyindeki devre dışı düğmelerin TAM listesi — ÖLÇÜLDÜ 2026-09-03
#: (TSK-109 sonrası). Her düğme ADIYLA sayılır: yalnız SAYIYA bakan bir çivi, bir düğme
#: silinip başkası eklendiğinde sessizce yeşil kalırdı.
YAPILANDIRMA_ROZETLI_DUGMELER = (
    "Webhook ekle",          # webhook bölümü başlığı (TSK-109)
    "Teslimatlar",           # webhook satırı
    "Düzenle",               # webhook satırı
    "Sil",                   # webhook satırı
    "Savunmayı değiştir",    # bellek savunması
    "Kuralı değiştir",       # bellek savunması
    "Kaydet",                # yapılandırma yazımı
)


def test_yapilandirmada_KALAN_rozetli_dugmeler_SAYILI():
    """Sayı bir çırçır değil KÖRLÜK ALARMIdır: düğmeler tek tek silinirse yukarıdaki `in`
    kontrolü hâlâ geçerdi.

    TABAN EŞİTLİĞE ÇEKİLDİ (TSK-109 incelemesi Ö-2a, 2026-09-03). Eşik `>= 3` idi ve düğme
    sayısı bu turda 4 → 7 oldu; yani "körlük alarmı" diyen çivi DÖRT düğmenin sessizce
    ölmesine izin veriyordu — ve docstring'i "üç düğme" derken dördünü sayıyordu. Eşitlik
    iki yönlü ısırır: düşen düğme de, beyansız eklenen düğme de öter."""
    s = soy(ISLEMLER)
    n = s.count("<Faz2Dugme")
    assert n == len(YAPILANDIRMA_ROZETLI_DUGMELER), (
        f"yapılandırma yüzeyinde {n} rozetli düğme var, beklenen "
        f"{len(YAPILANDIRMA_ROZETLI_DUGMELER)} — liste ile ekran ayrıştı")
    # DESEN BİÇİMDEN BAĞIMSIZ (düzeltme turu 2, Y-10): `f">{ad}</Faz2Dugme>"` tek satırlık JSX
    # varsayıyordu; biçimlendirici satırı bölseydi davranış değişmeden KIRMIZI olurdu — yanlış
    # alarm, yasanın en pahalı arızasıdır (susturulan bekçi olmayandan beterdir).
    eksik = [ad for ad in YAPILANDIRMA_ROZETLI_DUGMELER
             if not re.search(r">\s*" + re.escape(ad) + r"\s*<", s)]
    assert eksik == [], f"beyanlı devre dışı düğme ekrandan düştü: {eksik}"


# ============================================================================
# (6) KURTARMA ZİNCİRİ — SIRA VE SAYAÇ KAPISI ÜST YÜZEYDEN
# ============================================================================

def test_once_kurtar_sonra_tetikle():
    s = soy(YAZMA)
    assert s.index("hafizaYaz(UC_KURTAR") < s.index("hafizaYaz(UC_TETIKLE"), \
        "tetikleme kurtarmadan önce çağrılıyor"


def test_tetikleme_yalniz_SAYI_SIFIRDAN_BUYUKKEN():
    """`retried_count` üç değerlidir ve üçü de AYRI: gelmedi · sıfır · pozitif.
    `?? 0` ya da `?? 1` yazmak, ölçülmemiş bir sayıyı varsaymak olurdu."""
    s = soy(YAZMA)
    assert re.search(r"if \(sayac === null\) \{", s), "sayaç gelmediğinde tetikleme durdurulmuyor"
    assert re.search(r"if \(sayac === 0\) \{", s), "sıfır kayıtta boşuna tetikleme yapılıyor"
    assert s.index("if (sayac === 0)") < s.index("hafizaYaz(UC_TETIKLE"), \
        "sıfır kapısı tetiklemeden sonra geliyor"
    assert "retried_count ?? " not in s, "ölçülmemiş sayaç için varsayılan uyduruluyor"


def test_tetikleme_dustugunde_KISMI_BASARI_cumlesi():
    s = soy(YAZMA)
    assert "Kuyruğa alma başarısız:" in s, "kısmi başarı düz cümleyle söylenmiyor"
    assert "düşme işareti temizlendi" in s, "ne YAPILDIĞI söylenmiyor"


def test_eksik_UC_dali_UYUYAN_EMNIYET_olarak_duruyor():
    """Dört yazma ucunun dördü de vekilde VAR (ölçüldü 2026-09-03). Bu dal yalnız eksik/eski
    bir dağıtımda ateşlenir; silinseydi eksik dağıtım 'üst servis arızası' gibi okunurdu."""
    assert "Bu eylemin sunucu ucu bu sürümde yok" in soy(YAZMA)


# ============================================================================
# (7) ONAY PENCERESİ — BÜTÇE, GERİ ALINABİLİRLİK, ERİŞİLEBİLİRLİK
# ============================================================================

def _kunye_alani(alan: str) -> dict[str, bool]:
    s = soy(YAZMA)
    return {m.group(1): m.group(2) == "true"
            for m in re.finditer(r'kimlik: "([a-z-]+)".*?%s: (true|false)' % alan, s, re.S)}


def test_butce_uyarisi_MODEL_CAGRISI_doguran_eylemlerde():
    b = _kunye_alani("butce")
    assert b == {
        "hafiza-islem-iptal": False,
        "hafiza-islem-yeniden-dene": True,
        "hafiza-islem-sil": False,
        "hafiza-konsolidasyon-kurtar": True,
    }, f"bütçe uyarısı yanlış eylemlerde: {b}"
    assert "429" in soy(YAZMA), "ücretsiz tavan dolduğunda ne olacağı yazılı değil"


def test_SIL_geri_alinamaz_YAZILI():
    g = _kunye_alani("geriAlinabilir")
    assert g.get("hafiza-islem-sil") is False, "silme geri alınabilir gösteriliyor"
    assert "GERİ ALINAMAZ" in soy(YAZMA), "geri alınamazlık uyarısı ekranda yok"


def test_GIRIS_TUSU_onaylamaz():
    """Radix uyarı penceresi açılışta odağı iptal düğmesine düşürüyor (kütüphane kaynağında
    doğrulandı: `onOpenAutoFocus` → `cancelRef.focus()`), ve onay düğmesi gönderim düğmesi
    değil. İptal düğmesi Radix'in kendi bileşeni olmaktan çıkarsa bu garanti düşer."""
    s = soy(YAZMA)
    assert "<AlertDialogCancel " in s, "vazgeçme düğmesi ÇİZİLMİYOR — açılışta odak onaya düşer"
    assert s.count('type="button"') >= 2, "düğmeler gönderim düğmesi olarak kalmış"


def test_devre_disi_dugmenin_GEREKCESI_ADIN_ICINDE():
    """I-1 / `parcalar.tsx::Faz2Dugme` M-6 kuralı: devre dışı düğme odak alamaz ve `title`
    ipucu çoğu tarayıcıda bastırılır — gerekçe fareye değil ADA bağlanır."""
    s = soy(YAZMA)
    assert re.search(r'engel !== null \? <span className="sr-only"> — \{engel\}</span>', s), \
        "devre dışı düğmenin gerekçesi yalnız fare ipucunda — klavyeyle okunamaz"


# ============================================================================
# (8) TEK YAZMA KAPISI
# ============================================================================

def test_yazma_TEK_KAPIDAN_gider():
    s = soy(YAZMA)
    assert 'from "../../gonder"' in s and "apiPost" in s
    _yokluk(YAZMA, "fetch(")             # İKİ HATLI (Y-2): soyulmuş + ham


def test_ortak_kapi_HATA_govdesini_tasiyor():
    """M17 DERSİ: ilk çivi yalnız "ham" kelimesini arıyordu ve kelime başka yerde de geçtiği
    için alan silinse bile yeşil kalıyordu. Vekilin 4xx zarfındaki gerekçe `detail` alanında
    DEĞİL; bu alan düşerse reddin nedeni okunamaz hâle gelir."""
    g = soy(GONDER)
    assert "readonly ham: unknown;" in g, "ortak kapı tipinde ham gövde alanı yok"
    assert "ham: cozulen" in g, "ham gövde doldurulmuyor"


# ============================================================================
# (9) NİHAİ DAL DÜZELTMESİ (2026-09-03) — inceleme Ö-1/Ö-2/Ö-3/Ö-6 + TSK-109 Ö-2b/Ö-4
# ============================================================================
#
# BU BÖLÜM DOSYANIN KAPSAMINI GENİŞLETİYOR ve bu bilinçli: yukarıdaki sekiz bölüm
# YAZMA AKIŞINI çiviliyor, buradakiler o akışın kenarındaki sözleşmeleri —
# adresten türeyen sekme, tek POST kapısı, üçüncü yazma hâli, klavye erişimi,
# webhook tablosunun birebirliği. Ayrı bir vNNN dosyası açmak bunları aynı
# `soy()` sökücüsünün ve aynı körlük alarmının DIŞINA çıkarırdı.

PANO = KOK / "ui/src/pano"
ROTA = PANO / "rota.tsx"
ALANLAR = PANO / "alanlar.ts"
GORUNUMLER = HAFIZA / "gorunumler.ts"
BILGI = HAFIZA / "BilgiTabani.tsx"
RECALL = HAFIZA / "Recall.tsx"
BELLEKLER = HAFIZA / "Bellekler.tsx"
BELGELER = HAFIZA / "Belgeler.tsx"
ZIHIN = HAFIZA / "ZihinModelleri.tsx"
SOHBET = PANO / "yuzeyler/ajan/SohbetHatti.tsx"
#: `ANASAYFA` bu dosyada KARTLAR modülüdür (`anasayfakartlari.tsx`); süzgeç şeritleri
#: GÖRÜNÜM dosyasında yaşıyor ve ikisi ayrı ölçülür — aynı adı iki şeye vermek bu dalın
#: kendi K-2 bulgusunun tekrarı olurdu.
ANASAYFA_YUZEYI = HAFIZA / "AnaSayfa.tsx"
PARCALAR = HAFIZA / "parcalar.tsx"
KOMUTLAR = PANO / "komutlar.ts"

EK_DOSYALAR = (ROTA, ALANLAR, GORUNUMLER, BILGI, RECALL, BELLEKLER, BELGELER, ZIHIN, SOHBET,
               ANASAYFA_YUZEYI, PARCALAR, KOMUTLAR)


def test_EK_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI — kardeşinin (`test_olculen_dosyalar_YERINDE`) aynısı, yeni kapsam için.
    Yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve çivi "temiz" der."""
    for p in EK_DOSYALAR:
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 500, f"dosya beklenmedik biçimde küçük: {p}"


# ---- (9a) YORUM SÖKÜCÜSÜNÜN KENDİSİ (K6) -----------------------------------

#: SÖKÜCÜNÜN FAZLA YEDİĞİ DOSYALAR — ÖLÇÜLDÜ 2026-09-03 (regex `_YORUM` çıktısı v312'nin
#: karakter-tarayan `_yorumsuz`uyla kıyaslandı; sayı FAZLADAN yenen karakter). Bu tablo bir
#: KAYIP KAYDIdır: yokluk iddiaları over-stripping'e karşı savunmasızdır ve kaybın NEREYE
#: vurduğu yazılmadan "ölçüldü" denemez (bedel yasası, düzeltme turu 2 Y-2).
SOKUCUNUN_FAZLA_YEDIGI = {
    "ui/src/pano/yuzeyler/kapi/KapiYuzey.tsx": 2973,
    "ui/src/pano/komutlar.ts": 2285,  # TSK-118 (2026-09-03) düzenlemesinden sonra yeniden ölçüldü
    "ui/src/pano/yuzeyler/portfoy/MutabakatMasasi.tsx": 1047,
    "ui/src/pano/yuzeyler/bugun/HukumDagilimi.tsx": 157,
    "ui/src/pano/yuzeyler/portfoy/PozisyonSeyri.tsx": 73,
}

#: HAM METİNDE MEŞRU OLARAK GEÇEN YASAKLAR — (dosya adı, anahtar) → gerekçe. Meridian'ın belge
#: geleneği kararın gerekçesini yazarken YASAKLANAN ŞEYİ ALINTILAR; ham tarama o alıntıları
#: yakalar ve muafiyet BEYANLA olur (v380 `IKIZ_HAM_MUAFLARI` deseninin aynısı).
HAM_MUAFLARI = {
    ("Recall.tsx", "fetch("): "şerh v378'in `fetch(` yasağını ADIYLA alıntılıyor",
    ("yazma.tsx", "emerald"): "şerh kaldırılan `emerald-*` sınıfını ADIYLA alıntılıyor",
    ("Yapilandirma.tsx", "secret"): "şerh süzülen `secret` alanını ADIYLA alıntılıyor",
}


def _yokluk(p, yasak: str, *, desen: bool = False, anahtar: str | None = None) -> None:
    """YOKLUK İDDİASI İKİ HATLI (düzeltme turu 2, Y-2): soyulmuş metinde YOK — VE ham metinde
    de yok, ya da muafiyeti BEYANLI. Tek hat, sökücü bir bloğu yediğinde sessizce yeşil kalırdı.

    `desen=True` → `yasak` bir regex'tir; `anahtar` muafiyet tablosundaki adı verir."""
    ad = p.name
    soyulmus, ham = soy(p), p.read_text(encoding="utf-8")
    bulan = (lambda t: re.search(yasak, t) is not None) if desen else (lambda t: yasak in t)
    assert not bulan(soyulmus), f"{ad}: yasaklı dizge KODDA: {yasak!r}"
    if bulan(ham) and (ad, anahtar or yasak) not in HAM_MUAFLARI:
        raise AssertionError(
            f"{ad}: {yasak!r} HAM metinde var, soyulmuşta yok — ya şerhte alıntılanmış "
            f"(HAM_MUAFLARI'na gerekçesiyle yaz) ya da sökücü kod yedi (çivi KÖR)")


def test_SOKUCU_KAYBI_ADIYLA_kayitli():
    """KAYIP KAYDI CANLI: tablodaki her dosya hâlâ yerinde mi? Yol bayatlarsa kayıp ölçümü de
    bayatlar ve "ölçüldü" cümlesi sessizce yalan olur (körlük alarmı deseni)."""
    eksik = [ad for ad in SOKUCUNUN_FAZLA_YEDIGI if not (KOK / ad).is_file()]
    assert eksik == [], f"sökücü kaybı tablosundaki dosya yolu bayatladı: {eksik}"
    assert all(n > 0 for n in SOKUCUNUN_FAZLA_YEDIGI.values())


def test_YORUM_SOKUCUSU_kendisi_olculuyor():
    """POZİTİF KONTROL (v312 `test_yorum_sokucusu_KENDISI_olculuyor` emsali, nihai inceleme K6).

    Sökücü çalışmıyorsa bu dosyadaki VARLIK çivilerinin hepsi sessizce yalan söyler: bir yasak
    dizge yorumda geçtiği için "kod" sayılır ya da tersi. `test_IKIZ_TARAYICISI_sessizce_bos_DEGIL`
    kardeşi yalnız İMZA regex'ini ölçüyordu, `soy()`u DEĞİL — tarayıcının kendisi kontrolsüzdü.

    SÖKÜCÜNÜN ÖLÇÜLMÜŞ KÖRLÜĞÜ (2026-09-03, bedel yasası): `_YORUM` bir REGEX LİTERALİNİ de
    yiyebilir (`/\\*` ile başlayan bir literal blok yorumu gibi görünür) ve kapanmamış dize
    alarmı YOKTUR — v312'nin karakter-tarayan `_yorumsuz`u bu ikisini karşılıyor ama tüm
    `pano/` ağacına uygulanamıyor (bir dosya JSX metninde düz kesme işareti taşıyor, sökücü
    orada bağırırdı). Kayıp ÖLÇÜLDÜ: beş pano dosyasında regex sökücü karakter-tarayandan
    daha fazlasını yiyor.

    KAYBIN NEREYE VURDUĞU DA ÖLÇÜLDÜ (düzeltme turu 2, Y-2 — ilk turda yalnız "beş dosya"
    yazılmıştı, ADLARI yazılmamıştı): `SOKUCUNUN_FAZLA_YEDIGI` tablosu beşini ADIYLA taşıyor.
    Beşinin hiçbiri bu dosyanın ölçtüğü yüzeylerde DEĞİL (bugün), ama YOKLUK iddiaları
    (`"X" not in s`) yapısal olarak over-stripping'e açıktır: sökücü bir bloğu yerse yasaklı
    dizge "yok" görünür ve çivi yeşil kalır. Bu yüzden her yokluk iddiası HAM metinde de koşar
    (`_yokluk`), beyanlı muafiyetlerle — ağaç genelinde tarayan çivinin (v380
    `test_baska_dosyada_UCUNCU_ikiz_dogmadi`) ikinci hattının aynısı.
    """
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    soyulmus = _YORUM.sub(" ", ornek)
    assert soyulmus.count("IZ") == 2, soyulmus
    assert "/*" not in soyulmus and "*/" not in soyulmus, soyulmus
    # POZİTİF KONTROLÜN İKİNCİ YARISI (düzeltme turu 2, Y-2): sökücü BİLİNEN BİR KOD BLOĞUNU
    # YEMEZ. Yalnız "yorum gitti" demek, HER ŞEYİ yiyen bir sökücüyle de yeşil kalırdı.
    kod = 'const re = /ab/g;\nif (a < b) { x(); }\nconst t = `${a}/${b}`;\n'
    assert _YORUM.sub(" ", kod) == kod, _YORUM.sub(" ", kod)
    # ÜÇÜNCÜ YARI — ÖLÇÜLEN KÖRLÜK, ADIYLA (bedel yasası): sökücü bir DİZENİN İÇİNDEKİ `//`yi
    # de yer. Lookbehind yalnız `:` `'` `"` karakterlerini koruyor; `"a//b"` gibi bir dize
    # (URL, yol) sessizce kırpılır. Bu çivi o körlüğü ÖLÇER — kapatmaz. Kapatan şey `_yokluk`un
    # ikinci hattıdır (ham metin), ve o hat tam olarak bu sınıf için var.
    kor = 'const u = "a//b";\n'
    assert _YORUM.sub(" ", kor) != kor, (
        "sökücünün bilinen körlüğü kapanmış — şerh ve `_yokluk`un gerekçesi bayat")


# ---- (9b) SEKME ADRESTEN TÜRER (Ö-1) ---------------------------------------

def test_sekme_ADRESTEN_turuyor():
    """Ö-1: sekme `useState`teydi ve "… → Meridian dersleri" diyen bağ hep sayfa ağacını
    açıyordu — çalışan ama yanlış yere giden bağ. Görünüm zaten adresten türüyordu; sekme
    aynı kuralın bir kademe altı."""
    s = soy(BILGI)
    assert "bilgiSekmesiCoz(rota.sorgu)" in s, "sekme adresten çözülmüyor"
    assert "onValueChange={sekmeSec}" in s, "sekme değişimi adrese yazılmıyor"
    assert 'useState("sayfalar")' not in s, "sekme hâlâ yerel durumda tutuluyor"


def test_sekme_SORGU_ADI_tek_kaynaktan():
    """Sorgu adı ve sekme listesi TEK yerde (`gorunumler.ts`); adres kuran ve okuyan aynı
    sabitten besleniyor. İki kopya sessizce ayrışır ve bağ "çalışır ama açmaz" hâline döner."""
    g = soy(GORUNUMLER)
    assert 'export const SEKME_SORGU_ADI = "sekme"' in g
    assert "export const HAFIZA_BILGI_SEKMELERI" in g
    assert "export function bilgiSekmesiCoz" in g and "export function sekmeliYol" in g


def test_rota_HASH_ICINDEKI_sorguyu_tasiyor():
    """Ölçüm (brief kalemi): `hashiCoz` bölüm olarak yalnız yolun ÜÇÜNCÜ parçasını okuyor ve
    dördüncüsünü DÜŞÜRÜYORDU, `gorunumCoz` da tek bir bölüm dizgesi alıyor — mevcut mekanizma
    ikinci kademeyi TAŞIMIYOR. Bu yüzden kademe SORGUDA taşınır; `yol` sorguyu TAŞIMAZ
    (kenar çubuğu etkinliği ve kırıntı onu okuyor)."""
    s = soy(ROTA)
    assert "readonly sorgu: Readonly<Record<string, string>>;" in s, "rota sorguyu taşımıyor"
    assert "function sorguCoz(" in s, "sorgu çözücüsü yok"
    assert 'const soru = bos.indexOf("?");' in s, "sorgu yoldan ayrılmıyor"


def test_DERS_baglari_GORUNUME_gidiyor():
    """TSK-118 (2026-09-03, operatör K8) GÜNCELLEMESİ: Ö-1'in üç giriş kapısından ikisi —
    sohbet hattındaki bağ ve `#hafiza` yer imi — artık bir SEKMEYE değil kendi GÖRÜNÜMÜNE
    gidiyor, çünkü "Meridian dersleri" TSK-118'de sekme olmaktan çıktı (`hafiza-dersler`,
    `alanlar.ts::YUZEYLER.memory.bolumler`). Üçüncüsü (⌘K paleti) hâlâ "sekmeye değil
    görünüme iner" ilkesine bağlı — bu ilke TSK-118'de TERSİNE ÇEVRİLMEDİ, dersler artık
    gerçekten bir görünüm olduğu için aynı ilkeyle çelişmeden gerçek kayda kavuştu; gerekçesi
    `komutlar.ts`te yazılı ve bu çivinin son iddiası onu ölçer."""
    assert '#/dashboard/memory/hafiza-dersler' in soy(SOHBET), \
        "sohbet hattındaki ders bağı hâlâ eski (sekmeli) adrese gidiyor"
    a = soy(ALANLAR)
    assert 'hafiza: { yuzey: "memory", bolum: "hafiza-dersler" }' in a, \
        "`#hafiza` yer imi artık görünüme değil eski sekme adresine bağlı"
    assert "sorgu?: Readonly<Record<string, string>>" in a, "takma ad sorgusu tipte yok"
    # PALETİN SEKMEYE DEĞİL GÖRÜNÜME İNMESİ HÂLÂ BEYANLI: sessiz bir eksik ile ölçülmüş bir
    # ilke ayrı şeyler; TSK-118 bu ilkeyi TERSİNE ÇEVİRMEDİ, uyguladı.
    k = KOMUTLAR.read_text(encoding="utf-8")
    assert "PALET SEKMEYE DEĞİL GÖRÜNÜME İNER" in k, \
        "paletin sekmeye inmemesi beyansız — sessiz bir eksik ölçülmüş bir sınır gibi görünür"


# ---- (9c) TEK POST KAPISI RECALL'A DA GEÇERLİ (Ö-2) ------------------------

def test_recall_TEK_KAPIDAN_gider():
    """Ö-2: `Recall.tsx` kendi `fetch`ini açıyor, 401 çevrimini ve `hataEki` çağrısını yeniden
    yazıyordu. İki POST uygulaması sessizce ayrışır (kimlik/başlık/zaman aşımı politikası
    `apiPost`ta değişirse recall onu almaz) ve v378'in kendi kuralı bu dosyaya uygulanmıyordu."""
    s = soy(RECALL)
    assert 'from "../../gonder"' in s and "apiPost(UC_RECALL" in s, "recall ortak kapıdan geçmiyor"
    _yokluk(RECALL, "fetch(")            # İKİ HATLI (Y-2): soyulmuş + ham
    assert "s.kod === 401" in s, "401 oturum hâline çevrilmiyor"
    assert "s.kod === 0" in s, "yanıtın hiç gelmediği hâl `HTTP 0` diye yazılıyor"
    # Y-3: 2xx + ÇÖZÜLEMEYEN GÖVDE. `apiPost` ayrıştırma hatasını işaretli yutar ve
    # `govde: null` döner (`ok` hâlâ true). Geçirilirse `zarf === null` olur ve çağıran onu
    # "henüz sorulmadı" diye çizer: SESSİZ BOŞ EKRAN. Eski `fetch` yazımı burada ATIYORDU —
    # tek kapıya geçerken kaybolan tek şey buydu.
    assert "if (s.govde === null) {" in s, "2xx + çözülemeyen gövde sessiz boş ekran üretiyor"
    assert "yanıt gövdesi çözülemedi" in s, "çözülemeyen gövdenin gerekçesi yazılmıyor"


def test_ortak_kapi_UCUNCU_ret_adini_da_biliyor():
    """K-4: `veri.ts::hataEki` "TEK KAPI" diye beyanlı ve `detail`/`error`/`neden` üçlüsünü
    okuyor; POST tarafındaki `detaydanMetin` yalnız `detail`i biliyordu — beyan kapsamdan
    genişti. Artık ortak kapıya düşüyor."""
    g = soy(GONDER)
    assert 'import { hataEki } from "./veri";' in g, "ortak ret okuyucusu ithal edilmiyor"
    assert "const ek = hataEki(g);" in g, "`detaydanMetin` ortak kapıya düşmüyor"


# ---- (9d) ÜÇÜNCÜ YAZMA HÂLİ (Ö3) -------------------------------------------

def test_CEVAPSIZ_BASARI_ayri_cumle():
    """Ö3: vekil "`ok:false` yalnız 'cevabını kullanamadım' demektir, UI bunu 'olmadı' diye
    ÇİZEMEZ" diye BEYAN ediyor; UI `b.ok ? "tuttu" : "tutmadı"` çiziyordu ve ayrı dal yalnız
    `http === null` içindi. Ulaşılabilir hâl: upstream 204/boş gövde → `http` 2xx, `ok` false.
    `sil`de sonucu operatörün TEKRAR BASMASIdır — dalın kendi adlandırdığı geri-alınamaz
    çift-gönderim sınıfı."""
    s = soy(YAZMA)
    assert "const cevapsizBasari = !b.ok && kodOlculdu && b.http >= 200 && b.http < 300;" in s, \
        "cevapsız-başarı hâli ayrılmıyor"
    assert "çağrı gitti, cevabı okunamadı" in s, "üçüncü hâlin cümlesi ekranda yok"
    assert "TEKRAR BASMA" in s, "operatöre tekrar basmaması söylenmiyor"


def test_BASARI_RENGI_jetondan():
    """K-5 (Rol-1 hükmü: gece yeni jeton DOĞMAZ): `emerald-*` bu dalda doğan yeni bir palet
    kaynağıydı. 2026-09-03'te başarı rengi geçici olarak seri-9'dan (camgöbeği) okunuyordu;
    TSK-117 K-3 (2026-09-03, commit 01032e8) seri-9'un anlam yükünü kaldırdı: başarı artık
    ANLAM jetonundan (`basari` = sev-3 alias, BAŞARI bandı 132°–155°) okunur, seri jetonları
    yalnız veri serilerinde (v398 çivisi). Bu test o hükmü izler: emerald yok, seri-9 "başarı"
    olarak yok, `basari` utility'si VAR."""
    for p in (YAZMA, ANASAYFA):
        _yokluk(p, "emerald")            # İKİ HATLI (Y-2): soyulmuş + ham
    assert "var(--color-seri-9)" not in soy(ANASAYFA), "başarı rengi hâlâ seri-9'dan (K-3 geri mi alındı?)"
    assert "text-[var(--color-seri-9)]" not in soy(YAZMA), "başarı rengi hâlâ seri-9'dan (K-3 geri mi alındı?)"
    assert "basari" in soy(ANASAYFA) and "basari" in soy(YAZMA), "başarı rengi anlam jetonundan (basari) gelmiyor"


# ---- (9e) KLAVYE ERİŞİMİ — BEŞ YÜZEY (Ö-6) ---------------------------------

#: (dosya, satırın birincil hücresindeki düğmenin imzası). `Varliklar.tsx` deseni:
#: satırın kendisi tıklanabilir ama ODAKLANAMAZ; birincil hücreyi düğme yapmak aynı
#: eylemi sekme tuşuyla da erişilebilir kılar.
KLAVYE_YUZEYLERI = (
    (BELLEKLER, "onClick={() => setAcikKayit(k)}"),
    (BELGELER, "onClick={() => setAcikBelge(b)}"),
    (ZIHIN, "onClick={() => setAcik(m)}"),
    (ISLEMLER, "onClick={() => setAcikDenetim(d)}"),
)


def test_liste_satirlari_KLAVYEYLE_secilebilir():
    """Ö-6: dört tablonun satırları `onClick` + `cursor-pointer` ile tıklanabilir ama
    odaklanamıyordu (ne `tabIndex`, ne `role`, ne `onKeyDown`, ne içlerinde düğme) — yani
    detay çekmecesine tek yol FAREYDİ. v380 aynı sözleşmeyi `Varliklar.tsx` için çiviliyor."""
    eksik = []
    for p, imza in KLAVYE_YUZEYLERI:
        s = soy(p)
        # DÜĞME GÖVDESİNDE ARANIR, dosyanın herhangi bir yerinde değil (v380'in mutasyon
        # dersi: dosya geneli arama kendi körlüğünü "temiz" okuyordu).
        if not re.search(r'<button\b[^>]*?type="button"(?:[^>]|\n)*?' + re.escape(imza), s):
            eksik.append(p.name)
    assert eksik == [], f"satır birincil hücresi klavyeyle erişilebilir değil: {eksik}"


def test_agac_OGE_KAPISI_RENDER_yolunda():
    """Y-4 → K-1 (düzeltme turu 4): kapı ÇAĞRI YERİNDE olmalı, yalnız bileşen gövdesinde değil.

    Tur 2'de kapı `AgacSatiri` gövdesinin ilk satırına kondu. Tur-2 yeniden-incelemesi ölçtü ki
    bu YETMEZ: `key={metin(d.id) ?? …}` bileşen HİÇ ÇAĞRILMADAN önce değerlendirilir — `d`
    `null` ise orada senkron `TypeError` atar ve "bütün ağaç düşer" sınıfı bir satır YUKARI
    taşınmış olurdu. Yani gövde kapısı gerçek çöküş yolunu görmüyordu.

    ÇİVİ KURALI ÖLÇER, KODU TÜRETMEZ: her `<AgacSatiri` çizim yerinin BESLENDİĞİ liste
    `.map`ten ÖNCE `sozluk` ile süzülmüş olmalı. Desen dosyadan okunmaz, burada YAZILIDIR.
    İki kademe birlikte ölçülür: çağrı yeri (birinci hat) + gövde (ikinci hat)."""
    s = soy(BILGI)

    # KÖRLÜK ALARMI: çizim yeri sayısı. Yalnız "bir tane süzülmüş" demek, ikincisinin sessizce
    # süzgeçsiz doğmasına izin verirdi (v380'in mutasyon dersi: sayı bir çırçır değil alarmdır).
    cizim = [m.start() for m in re.finditer(r"<AgacSatiri\b", s)]
    assert len(cizim) == 2, f"ağaç satırı {len(cizim)} yerde çiziliyor — beklenen 2 (kök + özyineleme)"

    for yer in cizim:
        pencere = s[max(0, yer - 400):yer]
        assert ".map(" in pencere, f"çizim yeri bir `.map` içinde değil — desen bayat: …{pencere[-120:]!r}"
        assert re.search(r"\.filter\(\((\w+)\) => sozluk\(\1\) !== null\)\s*\.map\(", pencere), (
            "çizim yerinin listesi `.map`ten ÖNCE `sozluk` ile süzülmüyor — `key={metin(x.id) …}` "
            f"bileşen çağrılmadan değerlendirilir ve `null` düğümde BÜTÜN ağaç düşer: …{pencere[-160:]!r}")

    # İKİNCİ HAT: gövde kapısı da duruyor (üçüncü bir çağrı yeri eklendiği günü karşılar).
    govde = re.search(r"function AgacSatiri\((.*?)\n  return \(", s, re.S)
    assert govde, "AgacSatiri gövdesi okunamadı — desen bayat"
    assert "if (sozluk(dugum) === null) return null;" in govde.group(1), \
        "gövde kapısı (ikinci hat) düştü"


def test_DUSURULEN_dugum_SAYILIYOR_ve_EKRANDA():
    """Y-4 + B9: "say + atla" (`KovaSeridi` emsali). Sessizce düşen bir düğüm, ekrandaki
    sayıyı İŞARETSİZ küçültürdü — uydurma yasağının kardeşi. İki çözücü de sayar ve iki ekran
    da yazar; sayının OKUYUCUSU olmadan sayım Yasa 6 ihlali olurdu."""
    b, a = soy(BILGI), soy(ANASAYFA)
    assert "okunamayan += 1;" in b and "okunamayan += 1;" in a, "düşürülen düğüm sayılmıyor"
    assert "duz.okunamayan > 0" in b, "bilgi ağacında okunamayan sayısının okuyucusu yok"
    assert "tarama.okunamayan > 0" in a, "ana sayfa kartında okunamayan sayısının okuyucusu yok"
    assert "düğüm okunamadı" in b and "düğüm okunamadı" in a, "sayı ekranda cümleye dönmüyor"


def test_bilgi_agaci_TREEITEM_ve_klavye():
    """Ağaç satırında yapı da bildirilmiyordu: `role` yok, `aria-expanded` yok, odak yok."""
    s = soy(BILGI)
    assert 'role="tree"' in s and 'role="treeitem"' in s, "ağaç yapısı bildirilmiyor"
    assert 'role="group"' in s, "çocuk listesi grup olarak bildirilmiyor"
    assert "aria-expanded={klasor ? acik : undefined}" in s, "açık/kapalı yalnız ikonla söyleniyor"
    assert re.search(r'if \(e\.key !== "Enter" && e\.key !== " "\) return;', s), \
        "Enter/Space ile açılmıyor"


def test_SUZGEC_SERITLERI_aria_pressed_tasiyor():
    """Ö-5: dört şeritte seçim yalnız `variant="secondary"` ile (yani RENKLE) bildiriliyordu;
    kardeşleri (`PencereDugmeleri`, Belgeler tür süzgeci, kip düğmeleri) `aria-pressed`
    taşıyordu. Sayı da ölçülür: tek bir `in` kontrolü üç şeridin düşmesini göremezdi."""
    a, b = soy(ANASAYFA_YUZEYI), soy(BELLEKLER)
    assert a.count("aria-pressed={p === pencere}") == 1, "pencere şeridi durum bildirmiyor"
    assert a.count("aria-pressed={z.deger === zamanAlani}") == 1, "zaman alanı şeridi bildirmiyor"
    assert b.count("aria-pressed={t.deger === tur}") == 1, "tür şeridi durum bildirmiyor"
    assert b.count("aria-pressed={d.deger === durumSuzgeci}") == 1, "durum şeridi bildirmiyor"
    assert a.count('role="group"') >= 2 and b.count('role="group"') >= 2, \
        "şeritler gruplanmamış — ekran okuyucu düğmeleri ilişkisiz okur"


# ---- (9f) ÇIPLAK TİRE VE ADSIZ KOVA (Ö-4 · Ö-7 · K-7) ----------------------

def test_CIPLAK_TIRE_yok():
    """Ö-4: dizin genelindeki TEK çıplak tire `Belgeler.tsx::ParcaSatiri`deydi ve aynı satırın
    komşu hücresi `Olculemedi` ile dürüstçe çiziliyordu — sözleşme kısmen uygulanmış olur."""
    _yokluk(BELGELER, '{sira === null ? "—" : `#${sira}`}')   # İKİ HATLI (Y-2)
    s = soy(BELGELER)
    assert 'neden="sıra gelmedi"' in s, "sıra gelmediğinde gerekçe yazılmıyor"
    # Y-9: dar hücre `overflow-hidden` taşımalı — `Olculemedi kisa` nowrap'tir ve taşardı.
    assert 'className="w-10 shrink-0 overflow-hidden font-mono' in s, \
        "dar sıra hücresi taşmaya açık (overflow-hidden yok)"


def test_ADSIZ_arsiv_kaydina_HUKUM_kurulmuyor():
    """Ö-7: adı ölçülemeyen kayıt "eşleşmedi" sayılıyor ve `bankada yok` rozetiyle
    çiziliyordu — aynı satırda iki zıt iddia ("eşleme anahtarı kurulamadı" + "yok")."""
    s = soy(BELGELER)
    assert "const adsiz = (arsivKayitlari ?? []).filter((k) => dosyaAdi(k.ad) === null);" in s, \
        "adsız kayıtlar ayrı kovaya alınmıyor"
    assert "return ad !== null && !gorulen.has(ad);" in s, "hüküm hâlâ adsız kaydı kapsıyor"
    assert "eşleştirilemeyen" in s, "adsız kovanın cümlesi yok"


def test_DAMGASIZ_kovaya_SENTETIK_kimlik_basilmiyor():
    """K-7: damgası gelmeyen kovaya `kova N` yazılıyordu — kovanın kimliği ÖLÇÜLMEMİŞKEN
    dizideki SIRAYI kovanın adı gibi göstermek."""
    s = soy(PARCALAR)
    assert "`kova ${i + 1}`" not in s, "sentetik kova kimliği geri geldi"
    assert 'neden="damgası gelmeyen kova"' in s, "damgasız kova gerekçesiz çiziliyor"


def test_ROZETIN_KAPSAMI_yazili():
    """Dal-geneli gözlem: rozet bazı görünümlerde var bazılarında yok; kural "boş bir şerit
    'unutuldu' diye okunur" olduğuna göre kapsam YAZILMALIYDI."""
    s = PARCALAR.read_text(encoding="utf-8")   # ŞERH ölçülüyor: soyulmaz
    assert "ROZETİN KAPSAMI DA BURADA YAZILI" in s, "rozetin kapsam cümlesi yok"


# ---- (9g) WEBHOOK TABLOSU (TSK-109 Ö-2b) -----------------------------------

#: ÜST YÜZEYDEN ÖLÇÜLEN SÜTUN BAŞLIKLARI (`webhooks-view.tsx` `tableHeader*` anahtarları,
#: çapa ebad4782): URL · yöntem · olay türleri · durum · oluşturulma. Altıncı sütun
#: düğmelerdir ve o bizim eklememiz değil, üst yüzeyin de kendi sütunu.
WEBHOOK_SUTUNLARI = ("URL", "Yöntem", "Olay türleri", "Durum", "Oluşturulma", "Eylemler")


def _webhook_tablosu() -> str:
    """`WebhookTablosu` bileşeninin GÖVDESİ — dosya geneli DEĞİL.

    KÖRLÜK ALARMI: bileşen bulunamazsa boş metin dönmez, bağırılır (aynı dosyada üç ayrı
    tablo var ve dosya geneli arama yanlış tabloyu okuyabilir — v380'in ölçülmüş mutasyon
    dersi: "çivi kendi körlüğünü temiz diye okuyordu")."""
    s = soy(ISLEMLER)
    m = re.search(r"function WebhookTablosu\(.*?\n\}\n", s, re.S)
    assert m, "WebhookTablosu bileşeni okunamadı — desen bayat"
    return m.group(0)


def test_webhook_tablosu_BES_SUTUNU_birebir_cizer():
    # ÖLÇÜM BİLEŞEN GÖVDESİNDE (düzeltme turu 2, Y-7): aynı dosyada ÜÇ tablo var ve `Durum`
    # işlem tablosunda da geçiyor (bugün `className` ile ayrışıyor, yani TESADÜFEN tekil).
    # Komşu tablodan bir `className` düşerse dosya geneli arama KÖR olurdu.
    s = _webhook_tablosu()
    eksik = [b for b in WEBHOOK_SUTUNLARI if f"<TableHead>{b}</TableHead>" not in s
             and f'<TableHead className="w-[15rem]">{b}</TableHead>' not in s]
    assert eksik == [], f"webhook tablosunda ölçülen sütun yok: {eksik}"


def test_webhook_okumasi_BILESENIN_ICINDE():
    """YASA 6 + bedel: okuma `Webhooklar` bileşeninin İÇİNDE yaşıyor, yani sekme monte
    olmadan çağrı açılmıyor. Kabuğun otuz saniyelik toplu okumasına taşınmak, açılmayan bir
    sekme için her yarım dakikada bir upstream çağrısı demek olurdu."""
    s = soy(ISLEMLER)
    govde = re.search(r"function Webhooklar\(\{ bank \}[^\n]*\{(.*?)\n\}", s, re.S)
    assert govde, "Webhooklar bileşeninin gövdesi okunamadı — desen bayat"
    assert "useApi<" in govde.group(1), "webhook okuması bileşenin dışına taşınmış"


def test_webhook_YENILE_dugmesi_tazeleye_bagli():
    """TSK-109 incelemesi Ö-4: CP'nin yenile düğmesi ölçülmüş ama ne taşınmış ne beyan
    edilmişti; `useApi` periyotsuz, yani liste bir kez okunup bayatlıyordu."""
    s = soy(ISLEMLER)
    assert 'aria-label="Webhook listesini yenile"' in s, "yenile düğmesi yok"
    assert "webhooklar.tazele()" in s, "yenile düğmesi tazelemeye bağlı değil"
    assert "son okuma" in s, "bayatlığın işareti (son okuma damgası) çizilmiyor"
    # DAMGA MUTLAK OLMALI (düzeltme turu 2, Y-5): göreli hâl bir `simdi` durumu istiyordu ve
    # o durum yalnız montajda/Yenile'de güncelleniyordu — ama bu uç BİLEREK yoklanmıyor, yani
    # sekme kırk dakika açık kalsa da etiket "az önce" derdi. Ekranda ölçüm gibi duran ama
    # ÖLÇMEYEN bir cümle; kalemin gerekçesi (bayatlık işareti) tam olarak bunun tersiydi.
    assert "damga(webhooklar.zaman?.toISOString())" in s, "son okuma damgası mutlak değil"
    assert "goreliDamga(webhooklar.zaman" not in s, "göreli damga geri geldi (bayatlamaz)"


def test_webhook_SIR_ALANI_ekranda_HIC_gecmiyor():
    """Sır vekilde süzülüyor; ekran tarafında `secret` kelimesinin kod içinde geçmemesi bu
    sözleşmenin ikinci hattı. `secret_tanimli` HARİÇTİR — o alan sırrın kendisi değil."""
    _yokluk(ISLEMLER, r"\bsecret(?!_tanimli)\w*", desen=True, anahtar="secret")   # İKİ HATLI


def test_webhook_ETKIN_alani_UC_DEGERLI():
    """`Boolean(x)` yazmak gelmemiş alanı "kapalı" diye okuturdu: kapalı bir webhook ile hiç
    bilinmeyen bir webhook aynı ekranda aynı görünürdü."""
    s = soy(ISLEMLER)
    assert 'const etkin = typeof webhook.enabled === "boolean" ? webhook.enabled : null;' in s, \
        "`enabled` üç değerli okunmuyor"
    assert "Boolean(webhook.enabled)" not in s, "üç hâl iki hâle indirilmiş"
    assert "<OkRozet" in s, "durum rozeti çizilmiyor"


def test_webhook_YONTEM_varsayilani_UYDURULMUYOR():
    """CP `http_config?.method || "POST"` yazıyor; şemadaki `default` sunucunun O KAYIT için
    ne tuttuğunu SÖYLEMEZ. Uydurma dalında "POST" literal'i olmamalı."""
    s = soy(ISLEMLER)
    dal = re.search(r"const yontem = ([^\n]+)", s)
    assert dal, "yöntem okuması bulunamadı — desen bayat"
    assert '"POST"' not in dal.group(1), "gelmemiş yöntem şemadaki varsayılanla dolduruluyor"
    assert 'neden="Yöntem gelmedi"' in s, "yöntem gelmediğinde gerekçe yazılmıyor"


def test_webhook_BOS_LISTE_dali_DARALTILDI():
    """K-4: `listeye` sözleşmesi gereği boş dizi ÜÇ upstream hâlinden gelebilir; üçüne birden
    "tüm olaylar" demek üçünün EN İDDİALI cümlesini basmaktı."""
    s = soy(ISLEMLER)
    assert "Array.isArray(webhook.event_types) && webhook.event_types.length === 0" in s, \
        "boş liste dalı üç hâli tek cümleye indiriyor"
    assert 'teknik="`event_types` alanı yok' in s, "alan adı `Cipler`e delege edilmemiş"


def test_webhook_SAYAC_cumlesi_CIKARIM_etiketli():
    """K-3: "sayfalama da yok …, yani liste tamdır" bir ÇIKARIMI ölçüm gibi yazıyordu. Sorgu
    parametresinin şemada olmaması, sunucunun kendi tavanının olmadığını KANITLAMAZ."""
    s = soy(ISLEMLER)
    assert "yani liste tamdır" not in s, "çıkarım hâlâ ölçüm gibi yazılı"
    assert "kırpıldığına dair bir işaret" in s and "ÇIKARIMDIR" in s, \
        "sayaç cümlesi çıkarım olarak etiketlenmemiş"


def test_BOS_HALDE_rozet_TEKRAR_ETMIYOR():
    """K-5: başlıktaki `Faz2Grup` rozeti + boş hâl cümlesindeki `{FAZ2_ROZET}` = aynı vaat
    iki kez. Şerhin kendi kuralı "rozet grubun başında BİR KEZ"."""
    # ÖLÇÜM BİLEŞENİN İÇİNDE (v380'in mutasyon dersi): aynı desen (`ogeler.length === 0`)
    # bu dosyada BAŞKA bir tabloda da geçiyor ve dosya geneli arama yanlış dalı okurdu.
    s = _webhook_tablosu()
    bos = re.search(r"if \(ogeler\.length === 0\) \{(.*?)\n  \}", s, re.S)
    assert bos, "boş hâl dalı okunamadı — desen bayat"
    assert "FAZ2_ROZET" not in bos.group(1), "boş hâl rozeti ikinci kez okutuyor"
    assert "yukarıdaki rozet" in bos.group(1), "boş hâl rozetin yerini söylemiyor"


# ---- (9h) BELLEKLER ÇEKMECE ANAHTARI (Ö-3) ---------------------------------

def test_bellekler_cekmecesi_ANAHTARLI():
    """Ö-3: dört fetch'li çekmeceden ÜÇÜ `key={cekmeceAnahtari}` taşıyordu, dördüncüsü
    taşımıyordu — ve dördüncüsü içerik atfının en pahalı olduğu yer (kaydın TAM METNİ yanlış
    kimliğe atfediliyordu). Kök neden TSK-110'da; ara hâlde üçü var/biri yok en kötüsüydü."""
    eksik = [p.name for p in (BELLEKLER, BELGELER, ZIHIN, HAFIZA / "Varliklar.tsx")
             if "<SheetContent key={cekmeceAnahtari}" not in soy(p)]
    assert eksik == [], f"çekmece anahtarı olmayan yüzey: {eksik}"
    assert "if (acikKayit !== null && acikKayit !== cekmeceAnahtari) setCekmeceAnahtari(acikKayit);" \
        in soy(BELLEKLER), "anahtar render sırasında ilerlemiyor (bayat kare çizilir)"
