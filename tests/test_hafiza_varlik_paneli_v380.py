"""test_hafiza_varlik_paneli_v380.py — VARLIK KÜNYESİ PANELİNİN BEKÇİSİ (2026-09-03).

TSK-112 ile pano bir varlığa tıklayınca İKİ okuma açıyor: künye (`/api/hindsight/varlik`) ve o
isme bağlı kayıtların zaman çizelgesi (`/api/hindsight/liste`, `entity_id` süzgeciyle). Bu iki
okumanın sözleşmesi ekranda yaşıyor ve sözleşmeyi bozan hiçbir regresyon `tsc`ye GÖRÜNMEZ:
süzgecin sorgudan düşmesi · panel kapalıyken istek açılması · gerekçenin ekrandan silinmesi ·
çekmece anahtarının kalkması (bayat gövde yeni isme atfedilir) · satır çiziminin yeniden
kopyalanması — hiçbiri tip hatası üretmez.

NUMARA ÇAKIŞMASI TARANDI (2026-09-03): alınmış son numara v379 idi; `ls tests | grep v380` boş
döndü, deponun kalanında da yalnız v379'un kendi tarama notunda geçiyor. v380 BOŞTU.

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI: bu dosya TSX'i METİN olarak okur — v286/v288/v314/
v323/v324/v373/v378 ailesinin kurulu cevabı ("depoda `ui/` için test çatısı yok" bir engel
değil, bu ailenin çözdüğü problemdir). Ölçtüğü şey davranış DEĞİL, davranışı üreten satırın
varlığıdır. Zayıflık mutasyonla telafi edildi: 10 mutasyonun 10'u ısırdı — ve ilk turda BİRİ
sağ kaldı (künye tipindeki alan ölçümü dosyanın TAMAMINDA aranıyordu, oysa aynı ad başka iki
tipte de geçiyor: çivi kendi körlüğünü "temiz" okuyordu). O ölçüm arayüz bloğunun içine
sıkıştırılmış hâliyle duruyor; gevşetilirse mutasyon sessizce geçer.

ÖLÇÜMÜN KAYNAĞI ÜST YÜZEYDİR (Hindsight control plane @ ebad478240d3171bb88201ececda5e8d9883d22d):
tıklama ve panel alanları `entities-view.tsx` (satır 232-237, 287, 344-345, 432-517), çizelgenin
sıralama/kova/kart kuralları `data-view.tsx::TimelineView`. Aşağıdaki beklentiler O ÖLÇÜMÜN
kopyasıdır ve koddan TÜRETİLMEZ — türetseydi çivi kendini doğrulardı.

`veri.ts::hataEki` DE BURADA ÖLÇÜLÜYOR ve bu bilinçli bir genişlemedir (inceleme I-3): o kapı
tablodaki uçların TÜMÜNÜN ortak hata okuyucusu ve ret gövdesindeki üç adın SIRASI geriye dönük uyumun
kendisidir. Turla birlikte ölen bir scratchpad çivisi onu koruyamazdı.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
HAFIZA = PANO / "yuzeyler/hafiza"
VARLIKLAR = HAFIZA / "Varliklar.tsx"
PARCALAR = HAFIZA / "parcalar.tsx"
BELLEKLER = HAFIZA / "Bellekler.tsx"
RECALL = HAFIZA / "Recall.tsx"
UCTIPLERI = HAFIZA / "uctipleri.ts"
VERI = PANO / "veri.ts"

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy(p: pathlib.Path) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken YASAKLANAN
    ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır (v286'nın `_soy` dersi)."""
    return _YORUM.sub(" ", p.read_text(encoding="utf-8"))


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve
    çivi "temiz" der. Dosya varlığı ayrı ölçülür ki 'sıfır ihlal' bir okuma yokluğu olmasın."""
    for p in (VARLIKLAR, PARCALAR, BELLEKLER, RECALL, UCTIPLERI, VERI):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 500, f"dosya beklenmedik biçimde küçük: {p}"


# ============================================================================
# (1) UÇ SÖZLEŞMESİ — vekilin açtığı iki yol gerçekten kullanılıyor
# ============================================================================

def test_kunye_ucu_kullaniliyor():
    s = soy(VARLIKLAR)
    assert 'const UC_VARLIK = "/api/hindsight/varlik"' in s
    assert "${UC_VARLIK}?bank=" in s, "künye isteği banka parametresini taşımıyor"
    assert "id=${encodeURIComponent(kimlik)}" in s, "künye isteği kimliği kaçırmadan geçiriyor"


def test_bagli_kayitlar_entity_id_suzgeciyle_okunuyor():
    s = soy(VARLIKLAR)
    assert 'const UC_LISTE = "/api/hindsight/liste"' in s
    assert "entity_id=${encodeURIComponent(kimlik)}" in s, "kayıt listesi varlık süzgeci olmadan gidiyor"


def test_bagli_kayit_tavani_sunucununkiyle_ayni_ve_yazili():
    """Üst yüzey 500 istiyor; vekil kendi tavanına (200) kırpar. 500 yazmak, ekranın
    istediğinden başkasını aldığını bilmemesi olurdu."""
    s = soy(VARLIKLAR)
    assert "const BAGLI_KAYIT_TAVANI = 200" in s
    assert "limit=${BAGLI_KAYIT_TAVANI}" in s, "tavan yazılı ama sorguya girmiyor"


# ============================================================================
# (2) YASA 6 — panel açılmadan istek yok, kapanınca yol düşer
# ============================================================================

def test_iki_bacak_da_ACIKKEN_okunuyor():
    s = soy(VARLIKLAR)
    assert re.search(r"const kunyeYolu =\s*\n?\s*acik\s*\?", s), "künye yolu açıklık kapısından geçmiyor"
    assert re.search(r"const kayitYolu =\s*\n?\s*acik\s*\?", s), "kayıt yolu açıklık kapısından geçmiyor"


def test_cekmece_yeni_varlikta_yeniden_kuruluyor():
    """Veri katmanı yol değişince eski gövdeyi TEMİZLEMİYOR: anahtar olmadan A'nın künyesi
    B'nin başlığı altında çizilebilir (Belgeler'in ölçülmüş dersi, M-5)."""
    s = soy(VARLIKLAR)
    assert "cekmeceAnahtari" in s, "çekmece anahtarı yok — bayat gövde yeni varlığa atfedilebilir"
    assert "key={cekmeceAnahtari}" in s


def test_anahtar_RENDER_sirasinda_ilerler():
    """Etkide ilerleyen anahtar bir kare bayat gövde çizdiriyordu (inceleme M-1): etki
    boyamadan SONRA koşar."""
    s = soy(VARLIKLAR)
    assert "if (secili !== null && secili !== cekmeceAnahtari) setCekmeceAnahtari(secili);" in s
    assert not re.search(r"useEffect\(\(\) => \{\s*if \(secili !== null\) setCekmeceAnahtari", s), \
        "anahtar hâlâ etkide ilerliyor"


# ============================================================================
# (3) ETKİLEŞİM — iki okuma biçimi, tek panel; klavye ve yardımcı teknoloji
# ============================================================================

def test_dugum_ve_satir_AYNI_paneli_aciyor():
    s = soy(VARLIKLAR)
    assert s.count("varligiSec") >= 3, "seçim tek yerden akmıyor (düğüm + satır + kap)"
    assert "dugumTiklandi={" in s, "takımyıldız düğümü tıklamaya bağlanmamış"


def test_liste_satiri_klavyeyle_secilebilir():
    s = soy(VARLIKLAR)
    assert "<button" in s, "isim hücresi düğme değil — klavyeyle seçilemez"


def test_secili_satir_yardimci_teknolojiye_de_bildiriliyor():
    s = soy(VARLIKLAR)
    assert "aria-current={kimlik !== null && kimlik === secili" in s, "seçim yalnız renkle bildiriliyor"


def test_TIKLANABILIR_DEGIL_beyani_KALKTI():
    ham = VARLIKLAR.read_text(encoding="utf-8")
    assert "TIKLANABİLİR DEĞİL" not in ham, "artık tıklanabilir; eski gerekçe bayat"
    assert "İKİSİNİN DE KARŞILIĞI YOK" not in ham


# ============================================================================
# (4) ÜÇ DURUM · ALAN-YOK ≠ BOŞ · GEREKÇE GÖRÜNÜR
# ============================================================================

def test_kunye_zarf_kapisindan_geciyor():
    s = soy(VARLIKLAR)
    assert 'ne="Varlık künyesi"' in s, "künye zarfı dört hâli ayıran kapıdan geçmiyor"
    assert s.count("<UcKapisi") >= 4, "her bacak kendi uç kapısını taşımıyor"


def test_bagli_kayit_gerekcesi_EKRANDA():
    s = soy(VARLIKLAR)
    assert 'neden="Bağlı kayıtlar okunamadı"' in s, "liste gerekçesi çizilmiyor"
    assert 'neden="Bağlı kayıt listesi bildirilmedi"' in s


def test_damgasiz_kayitlar_SAYILIYOR():
    """Çizelgeye giremeyen kayıt sessizce düşmez — kaç tane olduğu yazılır."""
    s = soy(VARLIKLAR)
    assert "damgasiz" in s
    assert "KirpmaZinciri" in s


def test_ucsayili_zincir_KORUNDU():
    s = soy(VARLIKLAR)
    assert s.count("<KirpmaZinciri") >= 3, "isim + bağ zinciri korunmadı ya da kayıt zinciri eklenmedi"


def test_ucuncu_sayi_SUZULMUS_listede_kendi_ADIYLA_basiliyor():
    """SAYI DOĞRU, ADI YANLIŞTI (inceleme I-1): çekmecedeki zincir `entity_id` ile süzülmüş
    yanıtın toplamını basıyor; sabit "bankada toplam" metni operatöre bankanın tamamını
    gösterdiğini söylerdi."""
    par = soy(PARCALAR)
    assert 'toplamEtiketi = "bankada toplam"' in par, "varsayılan etiket kayboldu (eski çağıranlar)"
    assert "readonly toplamEtiketi?: string;" in par
    assert '{toplamEtiketi}{" "}' in par, "etiket prop'u alınıyor ama ÇİZİLMİYOR"
    var = soy(VARLIKLAR)
    assert 'toplamEtiketi="bu isme bağlı toplam"' in var, "süzülmüş zincir hâlâ banka geneli diye basılıyor"
    assert var.count("toplamEtiketi=") == 1, "banka geneli sayan iki zincir de etiketi devralmış"
    assert "toplamEtiketi" not in soy(HAFIZA / "takimyildizi.tsx"), "graf paneli gereksiz yere etiket geçiyor"


def test_kunye_alanlari_ETIKETLI_HAM_basiliyor():
    s = soy(VARLIKLAR)
    assert "<HamSatirlar" in s, "künyenin ölçülmemiş alanları kayboluyor"
    assert '"canonical_name"' in s, "ham blok yukarıda çizilen alanları atlamıyor"


def test_cekmece_basligi_AD_tasiyor():
    """Erişilebilir ad ham bir kimlikti (inceleme M-4); ad çözülmeden önce genel sözcükte
    kalır — uydurma başlık yazılmaz."""
    s = soy(VARLIKLAR)
    assert '{ad ?? "Varlık künyesi"}' in s
    assert "metin(kunye.veri?.govde?.canonical_name)" in s


def test_kunye_damgalari_TEK_KAPIDAN():
    s = soy(VARLIKLAR)
    assert "goreliDamga(" in s, "künye damgaları göreli okumasız"
    assert "damgaMs(" in s, "çizelge sıralaması korumasız çözümle kuruluyor olabilir"
    assert "Date.parse" not in s, "korumasız damga çözümü geri geldi"


def test_ayrinti_secimi_DENETLENIR():
    """`as Ayrinti` cast'i sözlük ile tipin ayrışmasını sessiz kılıyordu (inceleme M-2)."""
    s = soy(VARLIKLAR)
    assert "satisfies readonly { readonly deger: Ayrinti" in s
    assert "as Ayrinti" not in s, "denetlenmeyen dönüşüm geri geldi"


# ============================================================================
# (5) TEK KAYNAK — satır çizimi ve ret-gövdesi okuyucusu
# ============================================================================

def test_kayit_ozeti_TEK_yerde_tanimli():
    p = soy(PARCALAR)
    assert p.count("export function KayitOzeti") == 1
    assert p.count("export function kayitTuru") == 1


def test_iki_gorunum_de_ayni_satiri_kullaniyor():
    assert "<KayitOzeti" in soy(VARLIKLAR), "çizelge satırı kendi kopyasını çiziyor"
    assert "<KayitOzeti" in soy(BELLEKLER), "tablo satırı ortak bileşene geçmedi"


def test_bellekler_kendi_kopyasini_BIRAKTI():
    b = soy(BELLEKLER)
    assert "function kayitTuru" not in b, "tür çözümü iki kopya"
    assert "line-clamp-2" not in b, "metin çizimi hâlâ kopya"


def test_ret_govdesi_okuyucusu_TEK_KAPI():
    """Üç ad (`detail`/`error`/`neden`) tek yerde okunur; ikinci kopya üçüncü adı
    ÖĞRENMEMİŞTİ (inceleme I-2)."""
    v = soy(VERI)
    assert "export function hataEki" in v
    assert "g?.detail ?? g?.error ?? g?.neden" in v, "ret adlarının sırası değişti ya da kayboldu"
    r = soy(RECALL)
    # DESEN GÜNCELLENDİ (nihai inceleme Ö-2, 2026-09-03): `recallGonder` kendi `fetch`ini
    # açıyordu ve `hataEki`yi ham yanıttan çağırıyordu. Artık panonun TEK yazma kapısından
    # (`gonder.ts::apiPost`) geçiyor; ret gövdesi o kapının `ham` alanında taşınıyor.
    assert "hataEki(s.ham)" in r, "gönderim ortak ret okuyucusundan geçmiyor"
    assert "apiPost(UC_RECALL" in r, "gönderim ortak yazma kapısından geçmiyor"
    assert "g.detail" not in r, "ikiz okuyucu hâlâ yerinde"


#: OKUMA TARAFININ RET OKUYUCUSUNUN İMZASI: `detail` ile `error` ALTERNATİF olarak okunuyor.
#: DAR TUTULDU VE GEREKÇESİ ÖLÇÜLDÜ (ilk yazım geniş taradı ve İKİ YANLIŞ ALARM üretti):
#: `gonder.ts` ile `kabuk/krizUclari.ts` yalnız `detail` okuyor ve o YAZMA kapısının kendi
#: okuyucusudur (FastAPI'nin dizi biçimli doğrulama hatasını da çözer) — bu turun konusu
#: değil. Yanlış alarm, yasanın en pahalı arızasıdır: susturulan bekçi olmayandan beterdir.
_IKIZ_IMZASI = re.compile(r"detail\s*\?\?\s*[A-Za-z_$.?]*\berror\b")


#: HAM METİNDE eşleşip SOYULMUŞ metinde kaybolan dosyalar — BEYANLI muafiyet listesi.
#: Bugün BOŞ (ölçüldü 2026-09-03). Bir dosya buraya girdiğinde gerekçesi de yazılır:
#: "şerhinde yasaklanan deseni ALINTILIYOR" (Meridian'ın belge geleneği) ya da "sökücü
#: burada kod yiyor" (aşağıdaki körlük).
IKIZ_HAM_MUAFLARI: tuple[str, ...] = ()


def test_baska_dosyada_UCUNCU_ikiz_dogmadi():
    """Aynı gerçeğin üçüncü kopyası sessizce doğarsa bu çivi öter.

    YANLIŞ NEGATİF KAPATILDI (nihai inceleme K6, 2026-09-03): tarama `soy()`un çıktısında
    yapılıyor ve `soy()` bir REGEX SÖKÜCÜSÜdür — ölçüldü ki beş `pano/` dosyasında v312'nin
    karakter-tarayan `_yorumsuz`undan DAHA FAZLASINI yiyor (en büyüğü ~3.000 karakter).
    Yani gerçek bir ikiz, sökücünün yediği bir bloğun içinde kalıp SESSİZCE görünmez
    olabilirdi ve çivi "kopya yok" derdi.

    ÇARE: HAM metin de taranır. Ham'da eşleşip soyulmuşta kaybolan her dosya BEYANLI
    muafiyet ister — yani "yorumda alıntılanmış" hükmünü insan verir, sökücü değil.
    (v312'nin karakter-tarayan sökücüsü buraya taşınamadı: bir `pano/` dosyası JSX
    metninde düz kesme işareti taşıyor ve o sökücü orada BAĞIRIR — ağaç genelinde
    kullanılamaz. Bedel ölçüldü ve bu ikinci hatla ödendi.)"""
    kopyalar = []
    hamda_kaybolan = []
    for p in sorted(PANO.rglob("*.ts")) + sorted(PANO.rglob("*.tsx")):
        if p == VERI:
            continue
        ad = p.relative_to(KOK).as_posix()
        soyulmus_eslesme = _IKIZ_IMZASI.search(soy(p)) is not None
        ham_eslesme = _IKIZ_IMZASI.search(p.read_text(encoding="utf-8")) is not None
        if soyulmus_eslesme:
            kopyalar.append(ad)
        elif ham_eslesme and ad not in IKIZ_HAM_MUAFLARI:
            hamda_kaybolan.append(ad)
    assert kopyalar == [], f"ret gövdesi okuyucusunun yeni kopyası: {kopyalar}"
    assert hamda_kaybolan == [], (
        f"desen HAM metinde var, soyulmuşta yok: {hamda_kaybolan} — ya yorumda alıntılanmış "
        f"(muafiyet listesine gerekçesiyle yaz) ya da sökücü kod yedi (çivi kör)")


def test_IKIZ_TARAYICISI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (v314 disiplini): sentetik bir ikiz verilir ve tarayıcının onu
    YAKALAMASI beklenir — yoksa "kopya yok" cümlesi, taramanın boş dönmesiyle aynı görünürdü."""
    assert _IKIZ_IMZASI.search("const d = g.detail ?? g.error ?? g.neden;")
    assert _IKIZ_IMZASI.search("const d = govde.detail ?? govde.error;")
    assert not _IKIZ_IMZASI.search('const d = (g as { detail?: unknown }).detail;')


def test_YORUM_SOKUCUSU_kendisi_olculuyor():
    """POZİTİF KONTROL, AMA TARAYICININ DEĞİL SÖKÜCÜNÜN (nihai inceleme K6, v312
    `test_yorum_sokucusu_KENDISI_olculuyor` emsali).

    Kardeşi (`..._sessizce_bos_DEGIL`) yalnız `_IKIZ_IMZASI` regex'ini ölçüyordu; `soy()`
    çalışmasaydı yukarıdaki bütün VARLIK çivileri sessizce yalan söylerdi (yorumdaki dize
    "kod" sayılır). Sentetik örnekte aynı iz ÜÇ yorumda ve İKİ dizede geçiyor; sökümden
    sonra tam iki tanesi kalmalı."""
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    soyulmus = _YORUM.sub(" ", ornek)
    assert soyulmus.count("IZ") == 2, soyulmus
    assert "/*" not in soyulmus and "*/" not in soyulmus, soyulmus
    # İKİNCİ YARI (düzeltme turu 2, Y-2): sökücü BİLİNEN BİR KOD BLOĞUNU YEMEZ — yalnız
    # "yorum gitti" demek, HER ŞEYİ yiyen bir sökücüyle de yeşil kalırdı.
    kod = 'const re = /ab/g;\nif (a < b) { x(); }\nconst t = `${a}/${b}`;\n'
    assert _YORUM.sub(" ", kod) == kod, _YORUM.sub(" ", kod)
    # ÜÇÜNCÜ YARI — ÖLÇÜLEN KÖRLÜK ADIYLA (bedel yasası). İki sınıf ölçüldü 2026-09-03:
    # (a) bir DİZENİN içindeki `//` de yeniyor (lookbehind yalnız `:` `'` `"` koruyor);
    # (b) BEŞ `pano/` dosyasında sökücü v312'nin karakter-tarayanından FAZLASINI yiyor —
    #     `KapiYuzey.tsx` 2.973 · `komutlar.ts` 2.286 · `MutabakatMasasi.tsx` 1.047 ·
    #     `HukumDagilimi.tsx` 157 · `PozisyonSeyri.tsx` 73 karakter (tablo v378'de:
    #     `SOKUCUNUN_FAZLA_YEDIGI`, tek kaynak — burada ADIYLA anılıyor, kopyalanmıyor).
    # Aşağıdaki ağaç-geneli tarama bu yüzden HAM metni de okur.
    kor = 'const u = "a//b";\n'
    assert _YORUM.sub(" ", kor) != kor, (
        "sökücünün bilinen körlüğü kapanmış — ham-metin ikinci hattının gerekçesi bayat")


# ============================================================================
# (6) TİPTE ÖLÇÜLEN ALANLAR
# ============================================================================

def test_kunye_tipi_olculen_alanlarla_tanimli():
    """ÖLÇÜM BLOĞUN İÇİNDE YAPILIR (mutasyon dersi): dosyanın tamamında arayan ilk yazım
    yeşildi, çünkü `observations` başka iki tipte de geçiyor — çivi kendi körlüğünü
    "temiz" diye okuyordu."""
    t = UCTIPLERI.read_text(encoding="utf-8")
    bas = t.find("export interface VarlikKunyesi")
    assert bas != -1, "künye tipi yok"
    govde = t[bas : t.index("\n}", bas)]
    for alan in ("canonical_name", "mention_count", "first_seen", "last_seen", "metadata", "observations"):
        assert f"readonly {alan}?" in govde, f"künye tipinde ölçülen alan yok: {alan}"
