"""test_hafiza_genel_bakis_v388.py — HAFIZA "GENEL BAKIŞ" DÜZELTME DİLİMİNİN BEKÇİSİ
(TSK-124, 2026-09-03).

TETİK: operatör görsel turu (TSK-108…112 DONE kapısı, 2026-09-03 12:1xZ). Üç bulgu:
  (a) "takımyıldızı kartı hem ana sayfada var hem Bellekler'de — ana sayfada olmasına gerek yok";
      aynı sınıftan "son belgeler de duplike, bilgi sayfaları da duplike olabilir",
  (b) "mor noktalar çok büyük, orijinalinde farklı renklerle daha küçük",
  (c) "'Ana Sayfa' adı mantıksız, uygulamanın ana sayfasını andırıyor".

NUMARA ÇAKIŞMASI TARANDI (2026-09-03): `ls tests | grep v388` BOŞ döndü (v387 TSK-115'indir).
v388 alındı.

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI: bu dosya TSX/TS'i METİN olarak okur —
v286/v288/v314/v323/v324/v373/v378/v380 ailesinin kurulu cevabı ("depoda `ui/` için test çatısı
yok" bir engel değil, bu ailenin çözdüğü problemdir). Ölçtüğü şey davranış DEĞİL, davranışı
üreten satırın varlığıdır. Zayıflık MUTASYONLA telafi edilir (rapor: üç mutasyon, üçü de ısırdı).

TEK İSTİSNA — DÜĞÜM RENGİ: (b) bulgusunun çivisi metin eşleşmesi DEĞİL, HESAPTIR. Jeton adı →
`tema.css` → Tailwind `theme.css` oklch zinciri çözülür, oklch→sRGB→HSL dönüşümü BURADA yapılır
ve hue, `docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md` §2'nin rol bantlarıyla karşılaştırılır.
Sabit bir hex tablosu yazsaydık çivi kendi kopyasını doğrular, jeton değiştiği gün susardı.

ÖLÇÜM (kök neden, 2026-09-03): "mor noktalar" bir tercih değil ZİNCİRDİ —
`takimyildizi.tsx::paletOku` ısı rampasını `[mavi, mor, turuncu]` duraklarından kuruyordu ve
kayıt türü gelmeyen (kümesiz) düğümler ısı rengiyle boyanıyor. Rampanın ORTA durağı `mor`
(`--color-seri-8` = `--mod-canli` ile AYNI hex, 262°) ve düğümlerin çoğu orta bölgeye düşüyor.
Aynı üç durağın ÜÇÜ de rol bandındaydı: mavi 221° GEZİNME · mor 262° MOD · turuncu ~21° UYARI.
Yarıçap ise `GrafPaneli::boyutFn`de `4 + sqrt(w/wmax)*9` = 4–13 px @1x idi.

REFERANS ÖLÇÜLEMEDİ VE BU YAZILI (uydurma yasağı): "orijinal" = Hindsight control plane
(`constellation.tsx` / `home-view.tsx` @ ebad4782) BU DEPODA YOKTUR. Depoda kayıtlı olan tek
ölçüm `docs/superpowers/plans/2026-09-02-hafiza-cpui-birebir.md` Task 6'dır ve yalnız KURALI
taşır ("nokta yarıçapı bağ sayısından, ısı rengi sqrt(lc/maxLinkCount)"), piksel değeri
taşımaz; `takimyildizi.tsx`teki 4/9 sayıları dış bir SATIR çapasına (`home-view.tsx:160-173`)
dayanıyor ve o çapa buradan doğrulanamaz. Bu yüzden sözleşme brief'in beyanlı yedeğidir:
yarıçap 2–4 px @1x, renk TÜRE göre, tonlar rol bantlarının dışında.
"""
from __future__ import annotations

import colorsys
import math
import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
UI = KOK / "ui"
PANO = UI / "src/pano"
HAFIZA = PANO / "yuzeyler/hafiza"

ALANLAR = PANO / "alanlar.ts"
KOMUTLAR = PANO / "komutlar.ts"
ANASAYFA = HAFIZA / "AnaSayfa.tsx"
KARTLAR = HAFIZA / "anasayfakartlari.tsx"
TAKIMYILDIZI = HAFIZA / "takimyildizi.tsx"
GORUNUMLER = HAFIZA / "gorunumler.ts"
TEMA = UI / "src/tema.css"
TW_TEMA = UI / "node_modules/tailwindcss/theme.css"
# TSK-136, 2026-09-04 (operatör kararı 10:10Z): eski TSK-117 rezerve-hue seri rampası
# VARSAYILAN tema.css'ten preset'e taşındı. `_jeton_hue` bu yüzden PRESET-FARKINDA: `kaynak`
# verilirse `--seri-N → --color-X` adımı ORADAN okunur (`--color-seri-N → --seri-N` eşlemesi
# HER ZAMAN tema.css'te yaşar — preset o katmana dokunmaz, bkz. fonksiyon şerhi).
PRESET = UI / "src/styles/presets/meridian-palet.css"

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy(p: pathlib.Path) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken YASAKLANAN
    ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır (v286'nın `_soy` dersi)."""
    return _YORUM.sub(" ", p.read_text(encoding="utf-8"))


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve
    çivi "temiz" der. Dosya varlığı ayrı ölçülür ki 'sıfır ihlal' bir okuma yokluğu olmasın."""
    for p in (ALANLAR, KOMUTLAR, ANASAYFA, KARTLAR, TAKIMYILDIZI, GORUNUMLER, TEMA):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 500, f"dosya beklenmedik biçimde küçük: {p}"


def test_YORUM_SOKUCUSU_kendisi_olculuyor():
    """POZİTİF KONTROL (v378 K6 emsali): sökücü çalışmıyorsa aşağıdaki VARLIK ve YOKLUK
    iddialarının hepsi sessizce yalan söyler."""
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    soyulmus = _YORUM.sub(" ", ornek)
    assert soyulmus.count("IZ") == 2, soyulmus
    kod = 'const re = /ab/g;\nif (a < b) { x(); }\nconst t = `${a}/${b}`;\n'
    assert _YORUM.sub(" ", kod) == kod, "sökücü bilinen bir kod bloğunu yiyor"


# ============================================================================
# (D1) AD — "Genel bakış", TEK KAYNAKTAN
# ============================================================================

def test_gorunum_kaydinda_GENEL_BAKIS_yaziyor():
    """Etiketin TEK kaynağı yüzey kaydıdır (`alanlar.ts::YUZEYLER.memory.bolumler`); kenar
    çubuğu, başlık, kırıntı ve ⌘K paleti dördü de oradan okur (`gorunumler.ts::bolumKaydi`)."""
    s = soy(ALANLAR)
    m = re.search(r'\{\s*kimlik:\s*"hafiza-anasayfa",\s*baslik:\s*"([^"]+)"', s)
    assert m, "hafiza-anasayfa kaydı okunamadı — desen bayat"
    assert m.group(1) == "Genel bakış", f"görünen ad hâlâ {m.group(1)!r}"


def test_GORUNUM_KIMLIGI_ve_ESKI_ADRES_degismedi():
    """AD değişti, KİMLİK değişmedi — bu bilinçli: `hafiza-anasayfa` adreste, palet
    anahtarlarında ve `ESKI_GORUNUM_ADRESLERI` tablosunda yaşıyor. Kimliği de çevirmek
    operatörün yer imlerini ve üç emekli adresin evini sessizce kırardı."""
    g = soy(GORUNUMLER)
    assert '"hafiza-anasayfa"' in g
    assert 'VARSAYILAN_GORUNUM: HafizaGorunumu = "hafiza-anasayfa"' in g
    assert '"hafiza-bankalar": "hafiza-anasayfa"' in g, "emekli adresin evi kaydırılmış"


def test_ANA_SAYFA_dizgesi_KODDA_kalmadi():
    """TEK-KAYNAK YASASI: etiketin ikinci bir kopyası (görünüm gövdesi, kenar çubuğu, palet)
    kaydın adıyla sessizce ayrışırdı. Şerhler HARİÇ — bu deponun belge geleneği kaldırılan
    adı ADIYLA alıntılar ve `soy()` tam olarak onun için var."""
    for p in (ALANLAR, KOMUTLAR, ANASAYFA, KARTLAR, GORUNUMLER):
        assert "Ana Sayfa" not in soy(p), f"{p.name}: 'Ana Sayfa' etiketi kodda duruyor"


def test_palet_ANAHTARLARI_genel_bakisi_taniyor():
    """Operatörün aklındaki kelime, başlıktaki kelime değil (`komutlar.ts::BOLUM_EK` sözleşmesi).
    "anasayfa" BİLEREK kalıyor: eski alışkanlık bir aramayı boş döndürmemeli."""
    anahtarlar = _bolum_ek("hafiza-anasayfa")
    for k in ("genel bakis", "ozet", "anasayfa"):
        assert k in anahtarlar, f"palet anahtarı düştü: {k!r}"


def test_takimyildizi_anahtari_CIZEN_goruntume_tasindi():
    """ÇALIŞAN AMA YANLIŞ YERE GİDEN BAĞ, ÇALIŞMAYAN BAĞDAN SİNSİDİR (`komutlar.ts`in kendi
    kuralı): takımyıldızı artık Genel bakış'ta ÇİZİLMİYOR, Bellekler'de çiziliyor."""
    assert "takimyildizi" not in _bolum_ek("hafiza-anasayfa"), \
        "palet 'takimyildizi' arayanı grafı çizmeyen görünüme gönderiyor"
    assert "takimyildizi" in _bolum_ek("hafiza-bellekler"), \
        "anahtar taşınmadı, SİLİNDİ — arama artık hiçbir yere gitmiyor"


def _bolum_ek(kimlik: str) -> list[str]:
    """`BOLUM_EK` tablosundan bir bölümün anahtar listesi. Tablo TEK kaynak; buradan
    türetmek yerine ayrı bir kopya yazsaydık çivi kendi kopyasını doğrulardı."""
    s = soy(KOMUTLAR)
    blok = re.search(r"const BOLUM_EK[^=]*=\s*\{(.*?)\n\};", s, re.S)
    assert blok, "BOLUM_EK tablosu okunamadı — desen bayat"
    satir = re.search(rf'"{re.escape(kimlik)}":\s*\[(.*?)\]', blok.group(1), re.S)
    assert satir, f"{kimlik} satırı BOLUM_EK'te yok"
    return re.findall(r'"([^"]+)"', satir.group(1))


# ============================================================================
# (D2/D4) KOPYA YOK — GENEL BAKIŞ BİR GÖRÜNÜMÜN LİSTESİNİ/GRAFİĞİNİ TEKRARLAMAZ
# ============================================================================

def test_takimyildizi_GENEL_BAKISTAN_kalkti():
    """Aynı bileşen (`GrafPaneli`) aynı uçtan (`/api/hindsight/bellek-graf`) iki ekranda
    çiziliyordu; Bellekler görünümü onun EVİDİR (tam graf, 620 px)."""
    s = soy(ANASAYFA)
    assert "GrafPaneli" not in s, "Genel bakış hâlâ takımyıldızı çiziyor"
    assert 'from "./takimyildizi"' not in s, "takımyıldızı modülü hâlâ içe aktarılıyor"
    assert "bellek-graf" not in s, "graf ucu Genel bakış'tan hâlâ okunuyor"


def test_takimyildizinin_EVI_BELLEKLERDE_duruyor():
    """POZİTİF KONTROL: kaldırma "sil" değil "TAŞI" olmalı. Kart kalkarken bileşen de ölseydi
    operatör grafı hiçbir yerde bulamazdı ve çivi yine yeşil kalırdı."""
    b = soy(HAFIZA / "Bellekler.tsx")
    assert "GrafPaneli" in b and 'from "./takimyildizi"' in b, "tam graf Bellekler'den de düşmüş"


def test_kopya_LISTELER_tek_satir_ozete_indi():
    """D2 kuralı: bir görünümün LİSTESİNİ tekrar eden kart kalkar, yerine tek satır özet +
    bağlantı gelir. Okuma DURUYOR (sayı ve tazelik ölçülmüş kalsın), çizilen liste gidiyor."""
    s = soy(KARTLAR)
    assert "<ul" not in s, "kartlar modülünde hâlâ liste çiziliyor"
    assert "export function BelgeOzeti(" in s, "son belgeler özeti yok"
    assert "export function SayfaOzeti(" in s, "bilgi sayfaları özeti yok"
    for ad in ("SonBelgeler", "BilgiSayfalari"):
        assert f"export function {ad}(" not in s, f"{ad} kart biçimi hâlâ dışa aktarılıyor"


def test_ozet_satirlari_DOGRU_gorunume_gidiyor():
    """Bağlantının varışı görünüm KİMLİĞİNDEN kurulur (`yuzeyYolu`), elle yazılmış bir hash'ten
    değil: elle yazılan adres kimlik değiştiği gün sessizce varsayılana düşerdi."""
    s = soy(ANASAYFA)
    for kimlik in ("hafiza-bellekler", "hafiza-belgeler", "hafiza-bilgi"):
        assert f'yuzeyYolu("memory", "{kimlik}")' in s, f"{kimlik} bağlantısı yok"


def test_GECIS_SATIRLARI_sayilari_MEVCUT_okumadan_turetiyor():
    """YENİ VEKİL UCU YOK (brief yapılmayacaklar): takımyıldızı satırının sayıları sayfanın
    ZATEN yaptığı özet okumasından (`stats`) türer — graf ucunu bir satır için çekmek, kaldırılan
    kopyanın maliyetini geri getirirdi."""
    s = soy(ANASAYFA)
    assert "GecisSatiri" in s, "geçiş satırı bileşeni yok"
    assert "s.total_nodes" in s and "s.total_links" in s, "kayıt/bağ sayısı özet sayaçlarından gelmiyor"


def test_BOS_DURUM_cumleleri_ozette_KORUNDU():
    """UYDURMA YASAĞI: "ölçüldü, boş" ile "okuyamadım" ayrı cümlelerdir ve özet satırı
    kısaldı diye ikisi tek bir sıfıra inemez."""
    s = soy(KARTLAR)
    assert "ölçüldü, boş" in s, "ölçülmüş boşluğun cümlesi özet satırında kayboldu"


def test_DUSURULEN_dugum_sayimi_ozette_de_OKUNUYOR():
    """v378 `test_DUSURULEN_dugum_SAYILIYOR_ve_EKRANDA` sözleşmesi kart küçülünce DÜŞMEZ:
    sessizce atlanan bir düğüm, özet satırındaki sayıyı da işaretsiz küçültürdü."""
    s = soy(KARTLAR)
    assert "okunamayan += 1;" in s and "tarama.okunamayan > 0" in s
    assert "düğüm okunamadı" in s


# ============================================================================
# (D3) DÜĞÜM STİLİ SÖZLEŞMESİ — TEK TABLO, HESAPLANMIŞ HUE
# ============================================================================

def _dugum_stili() -> str:
    s = soy(TAKIMYILDIZI)
    m = re.search(r"export const DUGUM_STILI\s*=\s*\{(.*?)\n\}\s*as const;", s, re.S)
    assert m, "DUGUM_STILI tablosu okunamadı — desen bayat ya da tablo yok"
    return m.group(1)


def test_DUGUM_STILI_yaricap_araligi_2_4():
    """Operatör: "orijinalinde farklı renklerle DAHA KÜÇÜK". Eski aralık 4–13 px @1x idi
    (`4 + sqrt(w/wmax)*9`); yeni sözleşme 2–4 px."""
    blok = _dugum_stili()
    taban = re.search(r"yaricapTabani:\s*([\d.]+)", blok)
    tavan = re.search(r"yaricapTavani:\s*([\d.]+)", blok)
    assert taban and tavan, "yarıçap aralığı tabloda yazılı değil"
    assert float(taban.group(1)) == 2 and float(tavan.group(1)) == 4, \
        f"yarıçap aralığı {taban.group(1)}–{tavan.group(1)}, sözleşme 2–4"


def test_YARICAP_CIZIMDE_de_TABLODAN_okunuyor():
    """TEK-KAYNAK: tablo yazılıp çizim eski sayıyı kullansaydı sözleşme dekoratif olurdu.
    İki çağrı yeri var — boyut işlevi verilmeyen hâl (`hazirla`/çizim) ve `GrafPaneli::boyutFn`."""
    s = soy(TAKIMYILDIZI)
    assert "4 + Math.sqrt(" not in s, "eski 4+sqrt*9 boyut işlevi yerinde duruyor"
    assert s.count("DUGUM_STILI.yaricapTabani") >= 2, "çizim yarıçapı tablodan okumuyor"
    assert "DUGUM_STILI.yaricapTavani" in s


def test_KUME_ve_ISI_renkleri_TABLODAN_turetiliyor():
    """Tür→renk eşlemesi ve ısı rampası AYNI tablodan doğar; iki liste sessizce ayrışırdı."""
    s = soy(TAKIMYILDIZI)
    assert re.search(r"const KUME_JETONU[^=]*=\s*DUGUM_STILI\.tur", s), \
        "küme renkleri hâlâ ikinci bir tabloda"
    assert "DUGUM_STILI.isiDuraklari" in s, "ısı rampası tablodan okumuyor"


#: TASARIM BELGESİ §2 (`docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md`) — rol bantları, HSL
#: derecesinde.
#:
#: "195° AİLESİ" (185–210°) ARTIK BANTTA (düzeltme turu 1, 2026-09-03): ilk yazımda BİLEREK
#: dışarıdaydı, çünkü belge o bandın rolünü "beyan edilecek (S3); beyan edilmezse bant serbest
#: kalır" diye yazıyordu ve beyan edilmemiş bir rolü bant saymak ölçülmemiş bir kuralı zorlamak
#: olurdu. Beyan GELDİ: operatör kararı S3 (2026-09-03 ~10:50Z, ROADMAP TSK-117 notu) bandı
#: BİLGİ rolüne rezerve etti. Şerhin kendi cümlesi tutuldu — "bant beyan edildiği gün bu sözlüğe
#: girer ve çivi o gün öter" — ve gerçekten öttü (`camgobegi` 192,3°).
ROL_BANTLARI = {
    "KRİTİK": (336.0, 6.0),               # sarmalı bant (336°→360°→6°)
    "UYARI+YÖN-EKSİ": (8.0, 30.0),
    "BAŞARI+YÖN-ARTI": (132.0, 155.0),
    "BİLGİ": (185.0, 210.0),              # S3 beyanı 2026-09-03 (195° ailesi)
    "GEZİNME": (210.0, 232.0),
    "MOD": (245.0, 270.0),
}

#: GEÇİCİ BEYANLI İSTİSNALAR — TEK KAYNAK (Rol-1 ruling, TSK-124 düzeltme turu 1).
#:
#: KAPANDI (TSK-117 K-4, 2026-09-04): palet turu seri rampasını (`ui/src/tema.css` `--seri-6..10`)
#: rol bantlarının DIŞINA taşıdı (`tests/test_seri_rampasi_serbest_bant_v399.py`) ve
#: `DUGUM_STILI.tur.world` artık `camgobegi` (eski `--color-seri-9`, BİLGİ bandındaydı) DEĞİL
#: `teal` (`--color-seri-6`, serbest bant) okuyor — istisnanın nedeni ortadan kalktı, satır
#: SİLİNDİ (ölü muafiyet bir sonraki ihlali sessizce örter, dosyanın kendi kuralı).
#:
#: KÜNYE ZORUNLU (aşağıdaki çivi ölçer, sözlük boşken de): süresi olmayan bir istisna sessizce
#: kalıcılaşır. Yeni bir istisna açılırsa gerekçesi bir `TSK-` künyesi taşımak ZORUNDA, yani
#: istisnanın NE ZAMAN kapanacağı yazılı olmalı.
ISTISNALAR: dict[str, str] = {}


def _bantta(hue: float) -> str | None:
    for ad, (alt, ust) in ROL_BANTLARI.items():
        if alt <= ust:
            if alt <= hue <= ust:
                return ad
        elif hue >= alt or hue <= ust:      # sarmalı bant
            return ad
    return None


def _oklch_srgb(l: float, c: float, h: float) -> tuple[float, float, float]:
    """oklch → gama-düzeltilmiş sRGB (0..1, KIRPILMAMIŞ — çağıran ihtiyacına göre kırpar).
    Matris ve gama eğrisi Björn Ottosson'un OKLab tanımı + sRGB aktarım fonksiyonu (CSS Color 4
    §10.2 ile aynı sabitler). TEK KAYNAK (TSK-117 K-4, 2026-09-04): hem hue/doygunluk (`_oklch_hsl`,
    v399'un rol-bandı ölçümü) hem hex (`_tailwind_renk_hex`, huni=seri türetim ölçümü) BURADAN
    türer — iki ayrı dönüşüm formülü sessizce ayrışmasın diye (bedel yasası: bu depoda bir kez
    yaşanmış bir kusur sınıfı, ayrı-kopya-formül)."""
    a = c * math.cos(math.radians(h))
    b = c * math.sin(math.radians(h))
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def gama(x: float) -> float:
        x = min(max(x, 0.0), 1.0)
        return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055

    return tuple(gama(v) for v in lin)  # type: ignore[return-value]


def _oklch_hsl(l: float, c: float, h: float) -> tuple[float, float]:
    """oklch → sRGB → HSL. (hue derecesi, doygunluk). Dönüşüm BURADA yapılır çünkü tasarım
    belgesinin bantları HSL derecesinde ölçüldü (§1.1 `colorsys.rgb_to_hls`), jetonlar ise
    Tailwind'de oklch yazılı — sabit bir hex tablosu yazsaydık çivi kendi kopyasını doğrulardı."""
    r, g, bl = _oklch_srgb(l, c, h)
    ton, _isik, doygunluk = colorsys.rgb_to_hls(r, g, bl)
    return ton * 360.0, doygunluk


def _tailwind_renk_hex(ad: str) -> str:
    """Tailwind CSS değişken adı (`--color-teal-600`) → hex, `node_modules/tailwindcss/theme.css`
    İÇİNDEN ÖLÇÜLEREK (oklch → sRGB → hex, `_oklch_srgb`). SABİT BİR HEX TABLOSU YAZILMADI
    (uydurma yasağı, v399'un kendi ihtiyacı — `test_seri_rampasi_serbest_bant_v399.py`):
    Tailwind paleti bir gün değişirse bu fonksiyon o günkü değeri okur, donmuş bir kopyayı değil.
    v388'de yaşıyor çünkü `_oklch_srgb`/oklch regex deseni zaten burada tanımlıydı (`_jeton_hue`);
    v399 bunu İTHAL EDER, ikinci bir kopyasını yazmaz (TSK-117 K-4, 2026-09-04)."""
    if not TW_TEMA.is_file():                       # kurulum yoksa ÖLÇÜM YOK, sessizlik de yok
        raise AssertionError(
            f"{TW_TEMA} yok — hex ÖLÇÜLEMEDİ. `npm ci` koşulmadan bu çivi bir şey kanıtlamaz.")
    tw = TW_TEMA.read_text(encoding="utf-8")
    d = re.search(rf"{re.escape(ad)}:\s*oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\)", tw)
    assert d, f"{ad} Tailwind theme.css'te bulunamadı"
    r, g, bl = _oklch_srgb(float(d.group(1)) / 100, float(d.group(2)), float(d.group(3)))
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(bl * 255):02x}"


def _jeton_hue(jeton: str, kaynak: pathlib.Path | None = None) -> float | None:
    """Jeton adı → hue. `None` = AKROMATİK (doygunluk ~0) ya da tema jetonu (gri ailesi);
    hue'su olmayan bir renk hiçbir hue bandına giremez ve bu bir kaçamak değil, ölçüm.

    `kaynak` (TSK-136, 2026-09-04): `--seri-N → --color-X` adımı NEREDEN okunur — VARSAYILAN
    `TEMA` (`ui/src/tema.css`), preset-farkında bir ölçüm için `PRESET` verilebilir. `--color-
    seri-N → --seri-N` eşlemesi (aşağıdaki `seri = re.search(...)`) HER ZAMAN `TEMA`'dan okunur
    — preset dosyası o `@theme inline` katmanına hiç dokunmaz, yalnız ham `--seri-N` değerini
    EZER."""
    kaynak = kaynak or TEMA
    tak = soy(TAKIMYILDIZI)
    blok = re.search(r"export const JETONLAR\s*=\s*\{(.*?)\n\}", tak, re.S)
    assert blok, "JETONLAR tablosu okunamadı — desen bayat"
    # `"?` (TSK-132, 2026-09-04): JETONLAR artık İKİ anahtar biçimi karıştırıyor — kısa/tirsiz
    # adlar (`zemin`) çıplak JS tanımlayıcı, tireli rol adları (`dugum-world`) ZORUNLU tırnaklı
    # (TS geçerli tanımlayıcı değilse tırnaklar) — tırnaksız bir desen ikincisini kaçırırdı.
    m = re.search(rf'"?{re.escape(jeton)}"?:\s*"(--[a-z0-9-]+)"', blok.group(1))
    assert m, f"jeton tabloda yok: {jeton}"
    degisken = m.group(1)

    tema = TEMA.read_text(encoding="utf-8")
    seri = re.search(rf"{re.escape(degisken)}:\s*var\((--seri-\d+)\)", tema)
    if seri is None:
        # Tema jetonu (`--foreground`, `--muted-foreground`, `--border`…): shadcn tabanı
        # akromatiktir (oklch C=0). Doğrudan ölçülür, VARSAYILMAZ.
        dogrudan = re.search(rf"\n\s*{re.escape(degisken)}:\s*oklch\(([^)]*)\)", tema)
        assert dogrudan, f"{degisken} tema.css'te oklch olarak bulunamadı"
        parc = dogrudan.group(1).replace("/", " ").split()
        return None if float(parc[1]) < 0.02 else _oklch_hsl(
            float(parc[0]), float(parc[1]), float(parc[2]))[0]

    ham_metin = kaynak.read_text(encoding="utf-8")
    ham = re.search(rf"\n\s*{re.escape(seri.group(1))}:\s*var\((--color-[a-z]+-\d+)\)", ham_metin)
    if ham is None:
        dogrudan = re.search(rf"\n\s*{re.escape(seri.group(1))}:\s*oklch\(([^)]*)\)", ham_metin)
        assert dogrudan, f"{seri.group(1)} {kaynak.name}'te çözülemedi"
        parc = dogrudan.group(1).replace("/", " ").split()
        return None if float(parc[1]) < 0.02 else _oklch_hsl(
            float(parc[0]), float(parc[1]), float(parc[2]))[0]

    if not TW_TEMA.is_file():                       # kurulum yoksa ÖLÇÜM YOK, sessizlik de yok
        raise AssertionError(
            f"{TW_TEMA} yok — jeton hue'su ÖLÇÜLEMEDİ. `npm ci` koşulmadan bu çivi bir şey "
            "kanıtlamaz; sessizce geçmesi 'ölçülmemiş'i 'temiz' diye okumak olurdu.")
    tw = TW_TEMA.read_text(encoding="utf-8")
    d = re.search(rf"{re.escape(ham.group(1))}:\s*oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\)", tw)
    assert d, f"{ham.group(1)} Tailwind theme.css'te bulunamadı"
    hue, doygunluk = _oklch_hsl(float(d.group(1)) / 100, float(d.group(2)), float(d.group(3)))
    return None if doygunluk < 0.02 else hue


def test_HUE_HESABI_kendisi_olculuyor():
    """POZİTİF KONTROL — REVİZE (TSK-117 K-4, 2026-09-04): dönüşüm bozuksa aşağıdaki bant
    iddiası her rengi "temiz" okur. ESKİ HEDEF ARTIK GEÇERSİZ: bu kontrol seri jetonlarından
    üçünün (mavi/mor/turuncu) BİLEREK rol bandında olmasını kullanıyordu, ama K-4'ün TAM AMACI
    o üçünü bandın DIŞINA taşımaktı (`tests/test_seri_rampasi_serbest_bant_v399.py`) — ölçülen
    sonuç artık üçü de DIŞARIDA (`test_ISTISNA_DISINDA_kromatik_ton_TEK` bunu ayrıca doğrular).
    Eski hedefi burada tutmak POZİTİF kontrolü NEGATİF bir iddiaya çevirirdi (kendi kendini
    yalanlayan bir çivi).

    Yeni hedef JETONLAR/seri tablosunun DIŞINDA: shadcn tabanının `--destructive` jetonu
    (tema.css `:root`, oklch) — seri rampasından bağımsız, palet turundan ETKİLENMEDİ ve HÂLÂ
    KRİTİK bandında (kırmızı/hata rengi, ölçüldü ~357°). `_oklch_hsl` DOĞRUDAN çağrılır (jeton
    adı üzerinden değil — `_jeton_hue` yalnız `JETONLAR` tablosundaki adları çözer ve
    `--destructive` o tabloda yok); DEĞER SABİT YAZILMADI, tema.css'ten regex'le ÖLÇÜLÜR."""
    tema = TEMA.read_text(encoding="utf-8")
    m = re.search(r"\n\s*--destructive:\s*oklch\(([^)]*)\)", tema)
    assert m, "--destructive tema.css'te oklch olarak bulunamadı — pozitif kontrol hedefi bayat"
    l, c, h = (float(x) for x in m.group(1).replace("/", " ").split())
    hue, doygunluk = _oklch_hsl(l, c, h)
    assert doygunluk >= 0.02, "--destructive akromatik ölçüldü — dönüşüm bozuk"
    assert _bantta(hue) == "KRİTİK", (
        f"--destructive hue={hue:.1f}° → {_bantta(hue)}, beklenen KRİTİK (dönüşüm bozuk mu?)")


def test_DUGUM_RENKLERI_rol_bantlarinda_DEGIL():
    """(b) BULGUSUNUN ÇİVİSİ. Tür renkleri ve ısı rampasının ÜÇ durağı da rol bandı dışında —
    BEYANLI istisnalar hariç. Eski hâl üç ısı durağının ÜÇÜNÜ birden ihlal ediyordu
    (mavi GEZİNME · mor MOD · turuncu UYARI) ve hiçbiri beyanlı değildi.

    TSK-136 (2026-09-04, operatör kararı 10:10Z) HEDEFİ DEĞİŞTİRDİ: K-4'ün rezerve-hue seri
    rampası VARSAYILAN tema.css'ten preset'e taşındı — `takimyildizi.tsx`in JETONLAR/DUGUM_STILI
    tabloları G7 hâliyle KALDI (D3 kararı) ama VARSAYILAN temada `teal`/`pembe` artık blue-600/
    cyan-600'e bağlı (ÖLÇÜLDÜ: rol bandı içi). Bu çivi bu yüzden PRESET seçiliyken ölçer
    (`kaynak=PRESET`) — orada K-4'ün düzeltmesi hâlâ yaşıyor. VARSAYILANIN kendisi
    `test_VARSAYILAN_DUGUM_RENKLERI_rol_bandina_DONDU` ile AYRICA, düz bir değer ölçümü olarak
    (hue-gate DEĞİL) doğrulanır."""
    blok = _dugum_stili()
    jetonlar = set(re.findall(r'"([a-z0-9-]+)"', blok))
    assert jetonlar, "DUGUM_STILI hiçbir jeton adı taşımıyor — tablo boş okunuyor"
    for jeton in sorted(jetonlar):
        h = _jeton_hue(jeton, kaynak=PRESET)
        if h is None:
            continue                                # akromatik: hue yok, banda giremez
        bant = _bantta(h)
        if jeton in ISTISNALAR:
            continue                                # beyanlı: gerekçesi ayrı çivide ölçülüyor
        assert bant is None, f"{jeton} hue={h:.1f}° (preset) rol bandında: {bant}"


def test_VARSAYILAN_DUGUM_RENKLERI_rol_bandina_DONDU():
    """DEĞER ÖLÇÜMÜ (hue-gate DEĞİL): VARSAYILAN temada (preset SEÇİLMEDEN) `teal`/`pembe`
    ÖLÇÜLDÜĞÜ ÜZERE rol bandına geri düştü (TSK-136, 2026-09-04) — operatörün BİLİNÇLİ kararının
    doğrudan sonucu, eski (b) bulgusunun sınıfı. `soluk`/`yazi` akromatik, banda giremez."""
    blok = _dugum_stili()
    jetonlar = sorted(set(re.findall(r'"([a-z0-9-]+)"', blok)))
    bantta = {j: _bantta(h) for j in jetonlar if (h := _jeton_hue(j)) is not None}
    bantta = {j: b for j, b in bantta.items() if b is not None}
    # `isi-2`/`isi-3` (TSK-132, 2026-09-04) `isiDuraklari`den — AYNI değişkenleri `dugum-world`/
    # `dugum-experience` ile paylaşıyorlar (ısı rampası ile küme rengi TEK tablodan doğuyor,
    # `test_KUME_ve_ISI_renkleri_TABLODAN_turetiliyor`) — bu yüzden AYNI bantlara düşmeleri
    # BEKLENEN: ısı rampasının orta/sıcak durağı küme rengiyle görsel olarak ÇAKIŞMAMASI gerçeği
    # tam da bu testin ölçtüğü şey (TSK-124 "mor noktalar" ile aynı sınıf).
    assert bantta == {
        "dugum-world": "GEZİNME", "dugum-experience": "BİLGİ",
        "isi-2": "GEZİNME", "isi-3": "BİLGİ",
    }, (
        f"VARSAYILANDA banda-düşen küme değişti: {bantta} — beklenen dugum-world/isi-2→GEZİNME, "
        "dugum-experience/isi-3→BİLGİ (2026-09-04 ölçümü, ad TSK-132'de teal/pembe'den taşındı); "
        "DUGUM_STILI ya da tema.css sessizce değişmiş olabilir")


def test_ISTISNALAR_KUNYELI_ve_HALA_GEREKLI():
    """İSTİSNA LİSTESİ KENDİ KENDİNİ DENETLER — TERS YÖN (TSK-117 K-4, 2026-09-04).

    ESKİ HÜKÜM (K-4'TEN ÖNCE): liste BOŞ OLMAMALI — künyesiz/ölü istisna aranırdı.
    YENİ HÜKÜM (K-4 KAPANDIKTAN SONRA): liste BUGÜN BOŞ OLMALI. Palet turu serbest hue verdi ve
    `DUGUM_STILI` o değerlere taşındı (`tests/test_seri_rampasi_serbest_bant_v399.py`); istisnanın
    tek nedeni (S3 beyanından sonra `camgobegi`nin BİLGİ bandında kalması) ortadan kalktı. Boş
    olmayan bir liste bu noktadan sonra ÖLÜ MUAFİYET demektir — bir sonraki gerçek ihlali sessizce
    örter (dosyanın kendi kuralı, aşağıdaki döngüde hâlâ zorlanıyor).

    (a) KÜNYE (kalıcı kural, sözlük boşken de yaşar): her gerekçe bir `TSK-` künyesi taşır.
        Künyesiz bir istisna, süresi olmayan bir istisnadır ve sessizce kalıcılaşır.
    """
    assert ISTISNALAR == {}, (
        "istisna listesi BOŞ OLMALIYDI — palet turu (TSK-117 K-4) serbest hue verdi, "
        f"kalan kayıt(lar) ölü muafiyet: {ISTISNALAR!r}")
    for jeton, gerekce in ISTISNALAR.items():
        assert re.search(r"TSK-\d+", gerekce), \
            f"{jeton} istisnasının gerekçesi künyesiz: {gerekce!r} — kapanış tarihi yazılı değil"


def test_ISTISNA_DISINDA_kromatik_ton_TEK():
    """S3'ÜN ÖLÇÜLEN BEDELİ, ADIYLA (bedel yasası) — GÜNCELLENDİ (TSK-117 K-4, 2026-09-04; jeton
    adları düzeltme turu 1'de TEKRAR değişti, TSK-117 G7 r1, 2026-09-04; TSK-132, 2026-09-04'te
    hue adları ROL adına taşındı — `teal`→`dugum-world`, `turuncu`→`bag-entity`, `mor`→
    `bag-causal`, `pembe`→`dugum-experience`, `sari`→`bag-semantic`, DEĞERLER AYNEN):
    S3 kararından hemen sonra (palet turu K-4'ten ÖNCE) rol bantlarının dışında kalan kromatik
    seri jetonu SAYISI birdi (eski `pembe`, o gün seri-10=`--color-pink-600`). K-4 seri rampasını
    TAMAMEN serbest bantlara taşıdı (`--seri-6..10` artık teal/lime/fuchsia/pink/yellow) — bu
    testin adı ("TEK") artık ÖLÇÜLEN durumu anlatmıyor ama fonksiyon adı KİMLİKTİR (bu depoda
    numaralı/adlı test dosyaları yeniden adlandırılmaz, künye kayar); ÖLÇÜLEN sayı BEŞTİR.

    JETON ADLARI (düzeltme turu 1, TSK-117 G7 r1): `mavi`/`camgobegi` `JETONLAR`dan SİLİNDİ (ad
    çürük çapaydı — `mavi` artık teal'e, `camgobegi` artık pink'e bağlıydı — VE bir düğüm/bağ
    RENK ÇAKIŞMASININ kaynağıydı, bkz. `test_DUGUM_ve_BAG_RENKLERI_CAKISMIYOR`). Kalan beş
    kromatik seri-jeton, TSK-132'den beri seri numarasıyla değil ROLÜYLE adlı: `dugum-world`(6)
    `bag-entity`(7) `bag-causal`(8) `dugum-experience`(9) `bag-semantic`(10).

    TSK-136 (2026-09-04): `kaynak=PRESET` — K-4'ün serbest-bant rampası VARSAYILANDA değil,
    'Meridian Palet' preset'inde yaşıyor. VARSAYILANIN ölçümü
    `test_VARSAYILAN_ISTISNA_DISINDA_kromatik_ton_DUSTU`de."""
    serbest = [j for j in ("dugum-world", "bag-entity", "bag-causal", "dugum-experience", "bag-semantic")
               if (h := _jeton_hue(j, kaynak=PRESET)) is not None and _bantta(h) is None]
    assert serbest == ["dugum-world", "bag-entity", "bag-causal", "dugum-experience", "bag-semantic"], (
        f"serbest kromatik jeton kümesi değişti: {serbest} — `DUGUM_STILI` ve istisna "
        "listesi bu ölçümle birlikte gözden geçirilmeli")


def test_VARSAYILAN_ISTISNA_DISINDA_kromatik_ton_DUSTU():
    """DEĞER ÖLÇÜMÜ (hue-gate DEĞİL): VARSAYILAN temada (preset YOK) serbest kalan kromatik
    seri-jeton sayısı 5'ten 1'e DÜŞTÜ — `_jeton_hue` DAİMA `:root` (gündüz) değerini okur ve
    `dugum-world`(blue-600≈221° GEZİNME), `bag-entity`(orange-600≈18° UYARI+YÖN-EKSİ),
    `bag-causal`(violet-600≈265° MOD), `dugum-experience`(cyan-600≈192° BİLGİ) hepsi bantta;
    yalnız `bag-semantic`(yellow-600) serbest (TSK-136, 2026-09-04 — eski (b) bulgusunun sınıfı,
    operatörün BİLİNÇLİ kararı; adlar TSK-132'de role taşındı, DEĞERLER değişmedi)."""
    serbest = [j for j in ("dugum-world", "bag-entity", "bag-causal", "dugum-experience", "bag-semantic")
               if (h := _jeton_hue(j)) is not None and _bantta(h) is None]
    assert serbest == ["bag-semantic"], (
        f"VARSAYILANDA serbest kromatik jeton kümesi değişti: {serbest} — beklenen "
        "['bag-semantic'] (2026-09-04 ölçümü)")


def test_MOR_dugum_rengi_olmaktan_CIKTI():
    """Operatörün gördüğü tam kusur: eski `mor` (`--color-seri-8` = `--mod-canli` hex'i) hem
    küme hem ısı rampasının ORTA durağıydı, yani düğümlerin çoğunun rengiydi.

    İSİM-ÖZGÜ İDDİA ROL CÜMLESİNE TAŞINDI (TSK-132, 2026-09-04): `JETONLAR` artık hue adı
    taşımıyor (`mor`/`turuncu`/`pembe`/`teal`/`sari` silindi, DEĞERLER aynı) — bu yüzden iddia
    ARTIK "mor" sözcüğünü değil, hiçbir düğüm kümesinin eski hue vokabülerini TAŞIMADIĞINI ölçer."""
    blok = _dugum_stili()
    for eski_hue in ("mor", "turuncu", "pembe", "teal", "sari"):
        assert f'"{eski_hue}"' not in blok, f"{eski_hue} hâlâ düğüm renk tablosunda (rol adına geçilmedi)"


# ============================================================================
# (D5) DÜĞÜM × BAĞ RENK ÇAKIŞMASI — YENİ SINIF (düzeltme turu 1, TSK-117 G7 r1, 2026-09-04)
# ============================================================================
#
# TETİK: incelemenin bulgusu — TSK-124 "mor noktalar" (D3) bir DÜĞÜM kümesinin ısı rampasıyla
# çakışmasıydı; bu YENİ sınıf bir DÜĞÜM kümesi ile bir BAĞ TÜRÜNÜN çakışması. K-4'ün ilk hâlinde
# `BAG_TURU_JETONU.semantic` (`mavi`→`--color-seri-6`) `DUGUM_STILI.tur.world`ün (`teal`→AYNI
# değişken) rengiyle, `.temporal` (`camgobegi`→`--color-seri-9`) `.experience`in (`pembe`→AYNI
# değişken) rengiyle birebir aynıydı — takımyıldızında bir DÜNYA-BİLGİSİ düğümü ile bir ANLAMSAL
# bağ ekranda AYNI RENK, ayırt edilemez.

def _kume_jetonu() -> dict[str, str]:
    """`DUGUM_STILI.tur` alt tablosu → {kayıt türü: jeton adı}. `_dugum_stili()` DUGUM_STILI'nin
    TÜM gövdesini döner (`yaricapTabani`, `isiDuraklari` dahil) — bu yardımcı yalnız `tur: {...}`
    alt-nesnesini keser."""
    blok = _dugum_stili()
    m = re.search(r"tur:\s*\{(.*?)\n\s*\},", blok, re.S)
    assert m, "DUGUM_STILI.tur alt tablosu okunamadı — desen bayat"
    return dict(re.findall(r'(\w+):\s*"([a-z0-9-]+)"', m.group(1)))


def _bag_turu_jetonu() -> dict[str, str]:
    """`BAG_TURU_JETONU` tablosu → {bağ türü: jeton adı}."""
    s = soy(TAKIMYILDIZI)
    m = re.search(r"export const BAG_TURU_JETONU[^=]*=\s*\{(.*?)\n\};", s, re.S)
    assert m, "BAG_TURU_JETONU tablosu okunamadı — desen bayat"
    return dict(re.findall(r'(\w+):\s*"([a-z0-9-]+)"', m.group(1)))


def _jeton_degisken(ad: str) -> str:
    """Jeton adı → HAM CSS değişkeni (`--color-seri-6`, `--border`…), hue'ya İNMEDEN. Çakışma
    ölçümü (aşağıdaki çivi) hue EŞİTLİĞİNE değil DEĞİŞKEN eşitliğine bakar — iki sebeple: (1) iki
    farklı jeton adı aynı değişkene bağlıysa renk zaten AYNIDIR, hue hesabına gerek yok; (2) hue
    eşitliği YANLIŞ POZİTİF üretirdi — `_jeton_hue` iki FARKLI akromatik jetonda da (`soluk`=
    `--muted-foreground`, `yazi`=`--foreground`) `None` döner, hue'yla karşılaştırsaydık bu ikisi
    'çakışıyor' sayılırdı; DEĞİŞKEN adı bu körlüğe düşmez."""
    tak = soy(TAKIMYILDIZI)
    blok = re.search(r"export const JETONLAR\s*=\s*\{(.*?)\n\}", tak, re.S)
    assert blok, "JETONLAR tablosu okunamadı — desen bayat"
    m = re.search(rf'"?{re.escape(ad)}"?:\s*"(--[a-z0-9-]+)"', blok.group(1))
    assert m, f"jeton tabloda yok: {ad}"
    return m.group(1)


def test_DUGUM_ve_BAG_RENKLERI_CAKISMIYOR():
    """YENİ ÇAKIŞMA SINIFI (düzeltme turu 1, TSK-117 G7 r1, 2026-09-04) — TSK-124 "mor noktalar"
    (D3) ile AYNI aile ama farklı eksen: orada bir DÜĞÜM kümesi kendi ısı rampasıyla çakışıyordu,
    burada bir DÜĞÜM kümesi bir BAĞ TÜRÜYLE çakışıyordu (ölçüldü, düzeltme öncesi: `semantic`/
    `world` ve `temporal`/`experience` ikişer ikişer AYNI `--color-seri-N`). Bu çivi
    `KUME_JETONU` (`DUGUM_STILI.tur`) ∪ `BAG_TURU_JETONU` birleşiminin çözdüğü SEKİZ CSS
    değişkeninin (hue değil, `_jeton_degisken`) TEKİL olduğunu ölçer; gelecekte biri diğerinin
    rengine taşınırsa bu çivi öter. MUTASYONLA sınandı (rapor: `semantic`i `world`ün jetonuna
    geri çevirmek çiviyi ötürdü, geri alındı)."""
    kume = _kume_jetonu()
    bag = _bag_turu_jetonu()
    assert kume and bag, "DUGUM_STILI.tur ya da BAG_TURU_JETONU boş okundu — desen bayat"
    etiketli = [(f"dugum.{k}", v) for k, v in kume.items()] + [(f"bag.{k}", v) for k, v in bag.items()]
    gruplu: dict[str, list[str]] = {}
    for etiket, jeton in etiketli:
        degisken = _jeton_degisken(jeton)
        gruplu.setdefault(degisken, []).append(f"{etiket}({jeton})")
    cakisan = {d: e for d, e in gruplu.items() if len(e) > 1}
    assert not cakisan, f"düğüm ve bağ renkleri aynı CSS değişkeninde çakışıyor: {cakisan}"
