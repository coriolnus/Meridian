"""MARKA İŞARETİ: BEŞ SAYFANIN HİÇBİRİNDE FAVICON YOKTU · v320

VAKA (2026-08-26, operatör logoyu tasarlayıp gönderdi): ölçüldü ki beş HTML yüzeyin HİÇBİRİNDE
`<link rel="icon">` satırı yok ve depoda favicon dosyası da yok. Yani `Meridian — Bugün`,
`Meridian — pano`, tanıtım sayfası, runbook ve iş akışı — beşi de tarayıcı sekmesinde BOŞ
sayfa ikonuyla duruyordu.

SEÇİLEN VARYANT: operatörün gönderdiği üç yönden **C · M Monogramı**, ve **v0** — yani
tasarlandığı hâl. Ölçüm turunda enlem çizgisinin M'nin iç köşesiyle çakışık olduğu (ikisi de
y=52) ve bunun 16px'te "bıyık" gibi okunduğu operatöre gösterildi; operatör v0'ı seçti
(2026-08-26). BU ÇİVİ O KARARI KORUR: geometri BİREBİR çivilenir ki sonraki bir oturum
"iyileştirdim" diye sessizce değiştirmesin. Değişecekse operatör kararıyla ve bu çivi
güncellenerek değişir.

İKİ UYGULAMA KARARI VE GEREKÇELERİ:
  (1) DOSYA + ROTA, beş sayfaya gömülü data URI DEĞİL. Data URI ek istek istemez ama aynı 500
      karakteri BEŞ dosyaya kopyalardı — "iki kaynak, zamanla ayrışan iki yasa" bu deponun
      baskın hata deseni (`_statik`in kendi şerhi). Tek dosya, tek rota, beş `<link>`.
  (2) ROTA AD AD YAZILIR, `StaticFiles` MONTAJI YOK. api.py'deki `StaticFiles` montaj-yasağı hükmü (`_FONT_DOSYALARI` üstü): montaj, WEB dizinine
      düşen her taslağı/yedeği/`.orig`i sessizce yayına açar. `/fonts/{ad}` emsali birebir.

ÇIPALAR SEMBOLİK — ve bu ders bu turda ÖLÇÜLEREK öğrenildi: çivinin ilk sürümü montaj-yasağı
hükmüne api.py'nin O GÜNKÜ satır numarasıyla çıpa attı; favicon rotasını eklemek tam o satırı
KAYDIRDI ve codelaw bekçisi aynı turda `stale_line_anchors` verdi. Yani çivi kendi
düzeltmesini bayatlattı. Satır numarası bir çıpa DEĞİLDİR — ada/sembole çıpalanır.
(Bu paragraf da deseni LİTERAL yazamaz: bekçi `dosya.py` + iki nokta + sayı desenini
nesirde de görür ve haklıdır — bayat bir çıpa, açıklama içinde de bayattır.)

STANDALONE SVG `currentColor` MİRAS ALMAZ — bu bir tasarım değişikliği değil, bağlam
zorunluluğu: favicon sayfanın içinde değil AYRI bir belge olarak yüklenir, yani sayfanın
`color`ını göremez. `currentColor` orada siyaha düşer ve karanlık tarayıcı temasında işaret
görünmez olur. Bu yüzden dosya kendi `prefers-color-scheme` kuralını taşır. Geometri v0'dır;
değişen tek şey rengin NEREDEN geldiğidir.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian/web"
FAVICON = WEB / "favicon.svg"
SAYFALAR = ("index.html", "pano.html", "landing.html", "runbook.html", "workflow.html")

#: v0 geometrisi — operatörün tasarımı, BİREBİR. Değiştirmek bir OPERATÖR kararıdır.
V0_ENLEM = dict(x1="6", y1="52", x2="94", y2="52", genislik="3.5")
V0_M_YOLU = "M16,82 L33,17 L50,52 L67,17 L84,82"
V0_M_GENISLIK = "7"


def _svg() -> str:
    assert FAVICON.exists(), (
        f"favicon dosyası YOK: {FAVICON.relative_to(KOK)} — beş yüzey boş sekme ikonuyla kalır")
    return FAVICON.read_text(encoding="utf-8")


def _svg_serhsiz() -> str:
    """XML şerhleri SÖKÜLMÜŞ kaynak. ZORUNLU, süs değil: `currentColor` yasağı ilk koşuda
    dosyanın KENDİ ŞERHİNDE eşleşti — şerh, o rengin neden KULLANILMADIĞINI anlatıyordu.
    Yani doğru yazılmış bir dosya, yalnızca kararını belgelediği için kırmızı verdi.
    Bir çivi KODU ölçer; şerh kodun tarihçesini taşır ve yasak deseni içerebilir — içermeli de."""
    return re.sub(r"<!--.*?-->", "", _svg(), flags=re.S)


# ------------------------------------------------------------ GEOMETRİ = v0

def test_M_yolu_v0_ile_BIREBIR():
    """ASIL ÇİVİ: monogramın yolu operatörün tasarladığı hâl. Sessiz 'iyileştirme' yok."""
    s = _svg()
    assert V0_M_YOLU in s, (
        f"M yolu v0'dan AYRIŞMIŞ. Beklenen: {V0_M_YOLU}\n"
        "Bu geometri bir operatör kararıdır (2026-08-26): enlem çizgisinin iç köşeyle çakışık "
        "olduğu ve 16px'te bıyık gibi okunduğu GÖSTERİLDİ, operatör yine de v0'ı seçti. "
        "Değiştirmek istiyorsan önce o kararı değiştir, sonra bu çiviyi.")


def test_enlem_cizgisi_v0_ile_BIREBIR():
    s = _svg()
    m = re.search(r"<line\b[^>]*>", s)
    assert m, "enlem çizgisi (`<line>`) yok — monogram tek başına 'M' olur, koordinat gitmez"
    etiket = m.group(0)
    for alan, deger in (("x1", V0_ENLEM["x1"]), ("y1", V0_ENLEM["y1"]),
                        ("x2", V0_ENLEM["x2"]), ("y2", V0_ENLEM["y2"])):
        assert f'{alan}="{deger}"' in etiket, (
            f"enlem çizgisi v0'dan ayrışmış — {alan} beklenen {deger}:\n{etiket}")


def test_cizgi_kalinliklari_v0():
    """3.5 / 7 oranı v0'ın kendisi. Kalınlaştırmak da bir tasarım değişikliğidir."""
    s = _svg()
    assert f'stroke-width="{V0_ENLEM["genislik"]}"' in s, "enlem çizgisi kalınlığı v0 değil (3.5)"
    assert f'stroke-width="{V0_M_GENISLIK}"' in s, "M gövdesi kalınlığı v0 değil (7)"


def test_viewBox_kare():
    s = _svg()
    assert 'viewBox="0 0 100 100"' in s, "viewBox kare değil — favicon kutusunda çarpılır"


# ------------------------------- STANDALONE BAĞLAM: currentColor MİRAS ALINMAZ

def test_currentColor_TEK_BASINA_BIRAKILMADI():
    """Favicon AYRI bir belge olarak yüklenir; sayfanın `color`ını GÖREMEZ. `currentColor`
    orada siyaha düşer → karanlık tarayıcı temasında işaret görünmez."""
    s = _svg_serhsiz()
    assert "currentColor" not in s, (
        "favicon `currentColor` kullanıyor — standalone SVG sayfanın rengini MİRAS ALMAZ, "
        "karanlık temada görünmez olur")


def test_karanlik_tema_kurali_VAR():
    """İki zeminde de görünür olmalı; kural dosyanın İÇİNDE olmalı (dışarıdan gelemez)."""
    s = _svg_serhsiz()
    assert "prefers-color-scheme" in s and "dark" in s, (
        "favicon karanlık tema kuralı taşımıyor — tarayıcı koyu temada işaret kaybolur")


def test_HARICI_kaynak_YOK():
    """CSP `img-src 'self' data:`; favicon dış kaynak çekemez ve çekmeye çalışması sessiz
    bir kırılmadır."""
    s = _svg_serhsiz()
    assert not re.search(r'(?:href|src)\s*=\s*["\']https?://', s), (
        "favicon dış kaynağa başvuruyor — CSP altında sessizce düşer")


# ----------------------------------------------------- SUNUM: ROTA VAR MI

def test_rota_AD_AD_yazili():
    """`StaticFiles` montajı YOK (api.py'deki `StaticFiles` montaj-yasağı hükmü (`_FONT_DOSYALARI` üstü)) — dosyanın diskte olması bir VAAT'tir,
    sunulan şey ROTAdır. `/fonts/{ad}` emsalinde yaşanmıştı: dosya vardı, rota yoktu, 404."""
    src = (KOK / "meridian/api.py").read_text(encoding="utf-8")
    assert re.search(r'@app\.get\(\s*["\']/favicon\.svg["\']', src), (
        "`/favicon.svg` rotası YOK — dosya diskte olsa bile 404 döner (v202 vakasının aynısı)")


def _rota_govdesi() -> str:
    """`/favicon.svg` ROTASININ gövdesi — DEKORATÖRDEN itibaren.

    ÇIPA NEDEN DEKORATÖR, düz `src.index("/favicon.svg")` DEĞİL: o dize rotayı AÇIKLAYAN
    şerhte de geçiyor ve ilk eşleşme oraya düşüyor; pencere gövdeye hiç ulaşmıyordu. Yani
    doğru yazılmış bir rota, yalnızca belgelendiği için ölçülemiyordu. Bu turda aynı alt-dize
    tuzağına dört kez düşüldü — çıpa ADA/BİÇİME bağlanır, metne değil."""
    src = (KOK / "meridian/api.py").read_text(encoding="utf-8")
    m = re.search(r'@app\.get\(\s*["\']/favicon\.svg["\']\s*\)', src)
    assert m, "`/favicon.svg` rota dekoratörü bulunamadı"
    return src[m.start(): m.start() + 900]


def test_rota_DOGRU_mime_veriyor():
    """`image/svg+xml` olmadan tarayıcı SVG'yi ikon olarak kabul etmeyebilir."""
    govde = _rota_govdesi()
    assert "image/svg+xml" in govde, (
        "favicon rotası `image/svg+xml` mime vermiyor — tarayıcı ikonu yok sayabilir")


def test_rota_ORTAK_statik_govdesini_kullaniyor():
    """`_statik` içerik-ETag + no-cache + 304 yasasını taşır. Kendi elle yanıtını yazan bir
    rota, o yasanın DOKUZUNCU kopyası olurdu (`_statik`in kendi gerekçesi)."""
    govde = _rota_govdesi()
    assert "_statik(" in govde, (
        "favicon rotası `_statik` ortak gövdesini kullanmıyor — önbellek yasası ayrışır")


# ------------------------------------------------ BEŞ YÜZEYİN BEŞİ DE BAĞLI

def test_BES_sayfanin_BESI_de_ikonu_bildiriyor():
    """ASIL BOŞLUK: beşinin de `<link rel="icon">` satırı olmalı. Biri unutulursa o sekme
    boş ikonda kalır ve fark edilmez — sekme ikonu kimsenin bakmadığı yerdir."""
    eksik = []
    for ad in SAYFALAR:
        p = WEB / ad
        assert p.exists(), f"sayfa yok: {ad}"
        s = p.read_text(encoding="utf-8")
        if not re.search(r'<link[^>]+rel="icon"[^>]*>', s):
            eksik.append(ad)
    assert not eksik, f"favicon bildirmeyen sayfa(lar): {eksik}"


def test_HEPSI_AYNI_yolu_gosteriyor():
    """Tek kaynak çivisi: beş sayfa AYNI dosyayı göstermeli. Biri kopya bir data URI'ye
    kayarsa 'iki kaynak, zamanla ayrışan iki yasa' başlar."""
    yollar = set()
    for ad in SAYFALAR:
        s = (WEB / ad).read_text(encoding="utf-8")
        m = re.search(r'<link[^>]+rel="icon"[^>]*>', s)
        if m:
            h = re.search(r'href="([^"]+)"', m.group(0))
            yollar.add(h.group(1) if h else "(href YOK)")
    assert yollar == {"/favicon.svg"}, (
        f"sayfalar farklı favicon yolları gösteriyor: {sorted(yollar)}")
