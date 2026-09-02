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


def test_yapilandirmada_KALAN_rozetli_dugmeler_SAYILI():
    """Sayı bir çırçır değil KÖRLÜK ALARMIdır: dosyadaki üç düğme (savunma · kural · kaydet ·
    webhook) tek tek silinirse yukarıdaki `in` kontrolü hâlâ geçerdi."""
    n = soy(ISLEMLER).count("<Faz2Dugme")
    assert n >= 3, f"yapılandırma yüzeyinde yalnız {n} rozetli düğme kaldı — beklenen en az 3"


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
    assert "fetch(" not in s, "ikinci bir yazma kapısı açılmış"


def test_ortak_kapi_HATA_govdesini_tasiyor():
    """M17 DERSİ: ilk çivi yalnız "ham" kelimesini arıyordu ve kelime başka yerde de geçtiği
    için alan silinse bile yeşil kalıyordu. Vekilin 4xx zarfındaki gerekçe `detail` alanında
    DEĞİL; bu alan düşerse reddin nedeni okunamaz hâle gelir."""
    g = soy(GONDER)
    assert "readonly ham: unknown;" in g, "ortak kapı tipinde ham gövde alanı yok"
    assert "ham: cozulen" in g, "ham gövde doldurulmuyor"
