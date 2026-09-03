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
#: NEDEN VAR: S3 beyanından sonra rol bantlarının DIŞINDA kalan tek kromatik seri jetonu
#: `pembe`dir. Üç kayıt türünü tek kromatik tona sıkıştırmak, renk kimlik kanalını tümüyle
#: kaybetmek olurdu — bu turda yeni palet jetonu yaratmak ise palet turunun (TSK-117 K-4) işi.
#: Bu yüzden ihlal SİLİNMEDİ, BEYAN EDİLDİ.
#:
#: KÜNYE ZORUNLU (aşağıdaki çivi ölçer): süresi olmayan bir istisna sessizce kalıcılaşır.
#: Gerekçe bir `TSK-` künyesi taşımak zorunda, yani istisnanın NE ZAMAN kapanacağı yazılı.
ISTISNALAR = {
    "camgobegi": "TSK-117 K-4'e kadar (S3 beyanı 2026-09-03)",
}


def _bantta(hue: float) -> str | None:
    for ad, (alt, ust) in ROL_BANTLARI.items():
        if alt <= ust:
            if alt <= hue <= ust:
                return ad
        elif hue >= alt or hue <= ust:      # sarmalı bant
            return ad
    return None


def _oklch_hsl(l: float, c: float, h: float) -> tuple[float, float]:
    """oklch → sRGB → HSL. (hue derecesi, doygunluk). Dönüşüm BURADA yapılır çünkü tasarım
    belgesinin bantları HSL derecesinde ölçüldü (§1.1 `colorsys.rgb_to_hls`), jetonlar ise
    Tailwind'de oklch yazılı — sabit bir hex tablosu yazsaydık çivi kendi kopyasını doğrulardı."""
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

    r, g, bl = (gama(v) for v in lin)
    ton, _isik, doygunluk = colorsys.rgb_to_hls(r, g, bl)
    return ton * 360.0, doygunluk


def _jeton_hue(jeton: str) -> float | None:
    """Jeton adı → hue. `None` = AKROMATİK (doygunluk ~0) ya da tema jetonu (gri ailesi);
    hue'su olmayan bir renk hiçbir hue bandına giremez ve bu bir kaçamak değil, ölçüm."""
    tak = soy(TAKIMYILDIZI)
    blok = re.search(r"export const JETONLAR\s*=\s*\{(.*?)\n\}", tak, re.S)
    assert blok, "JETONLAR tablosu okunamadı — desen bayat"
    m = re.search(rf'{re.escape(jeton)}:\s*"(--[a-z0-9-]+)"', blok.group(1))
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

    ham = re.search(rf"\n\s*{re.escape(seri.group(1))}:\s*var\((--color-[a-z]+-\d+)\)", tema)
    if ham is None:
        dogrudan = re.search(rf"\n\s*{re.escape(seri.group(1))}:\s*oklch\(([^)]*)\)", tema)
        assert dogrudan, f"{seri.group(1)} tema.css'te çözülemedi"
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
    """POZİTİF KONTROL: dönüşüm bozuksa aşağıdaki bant iddiası her rengi "temiz" okur.
    Bilinen iki ölçüm belgeden (§1.2): `--color-seri-6` 221° (GEZİNME) · `--color-seri-8` 262°
    (MOD). İkisi de BANTTA çıkmalı — yani çivi ısırabildiğini önce kendi üstünde gösterir."""
    for jeton, bant in (("mavi", "GEZİNME"), ("mor", "MOD"), ("turuncu", "UYARI+YÖN-EKSİ")):
        h = _jeton_hue(jeton)
        assert h is not None, f"{jeton} akromatik ölçüldü — dönüşüm bozuk"
        assert _bantta(h) == bant, f"{jeton} hue={h:.1f}° → {_bantta(h)}, beklenen {bant}"


def test_DUGUM_RENKLERI_rol_bantlarinda_DEGIL():
    """(b) BULGUSUNUN ÇİVİSİ. Tür renkleri ve ısı rampasının ÜÇ durağı da rol bandı dışında —
    BEYANLI istisnalar hariç. Eski hâl üç ısı durağının ÜÇÜNÜ birden ihlal ediyordu
    (mavi GEZİNME · mor MOD · turuncu UYARI) ve hiçbiri beyanlı değildi."""
    blok = _dugum_stili()
    jetonlar = set(re.findall(r'"([a-z]+)"', blok))
    assert jetonlar, "DUGUM_STILI hiçbir jeton adı taşımıyor — tablo boş okunuyor"
    for jeton in sorted(jetonlar):
        h = _jeton_hue(jeton)
        if h is None:
            continue                                # akromatik: hue yok, banda giremez
        bant = _bantta(h)
        if jeton in ISTISNALAR:
            continue                                # beyanlı: gerekçesi ayrı çivide ölçülüyor
        assert bant is None, f"{jeton} hue={h:.1f}° rol bandında: {bant}"


def test_ISTISNALAR_KUNYELI_ve_HALA_GEREKLI():
    """İSTİSNA LİSTESİ KENDİ KENDİNİ DENETLER — iki yönde birden.

    (a) KÜNYE: her gerekçe bir `TSK-` künyesi taşır. Künyesiz bir istisna, süresi olmayan bir
        istisnadır ve sessizce kalıcılaşır — "geçici" kelimesi tek başına bir taahhüt değildir.
    (b) HÂLÂ GEREKLİ Mİ: listedeki jeton BUGÜN gerçekten bir rol bandında olmalı. Palet turu
        (TSK-117 K-4) serbest tonu verip `DUGUM_STILI` güncellendiğinde bu istisna ÖLÜ satır
        olurdu ve ölü bir muafiyet, bir sonraki ihlali sessizce örterdi. Çivi o gün öter ve
        satırın silinmesini ister — muafiyetin kapanışını da mekaniğe bağlayan yarı budur.
    """
    assert ISTISNALAR, "istisna listesi boş — o hâlde ana çividen `ISTISNALAR` dalı da ölü"
    for jeton, gerekce in ISTISNALAR.items():
        assert re.search(r"TSK-\d+", gerekce), \
            f"{jeton} istisnasının gerekçesi künyesiz: {gerekce!r} — kapanış tarihi yazılı değil"
        h = _jeton_hue(jeton)
        assert h is not None and _bantta(h) is not None, (
            f"{jeton} artık hiçbir rol bandında değil (hue={h}) — istisna ÖLÜ, "
            "satır silinmeli yoksa bir sonraki ihlali sessizce örter")


def test_ISTISNA_DISINDA_kromatik_ton_TEK():
    """S3'ÜN ÖLÇÜLEN BEDELİ, ADIYLA (bedel yasası): beyandan sonra rol bantlarının dışında
    kalan kromatik seri jetonu SAYISI. Bugün bir tane (`pembe`) ve istisnanın gerekçesi tam
    olarak bu. Sayı arttığı gün (palet turu) istisna gereksizleşir ve kardeş çivi öter."""
    serbest = [j for j in ("mavi", "turuncu", "mor", "camgobegi", "pembe")
               if (h := _jeton_hue(j)) is not None and _bantta(h) is None]
    assert serbest == ["pembe"], (
        f"serbest kromatik jeton kümesi değişti: {serbest} — `DUGUM_STILI` ve istisna "
        "listesi bu ölçümle birlikte gözden geçirilmeli")


def test_MOR_dugum_rengi_olmaktan_CIKTI():
    """Operatörün gördüğü tam kusur: `mor` (`--color-seri-8` = `--mod-canli` hex'i) hem küme
    hem ısı rampasının ORTA durağıydı, yani düğümlerin çoğunun rengiydi."""
    blok = _dugum_stili()
    assert '"mor"' not in blok, "mor hâlâ düğüm renk tablosunda"
