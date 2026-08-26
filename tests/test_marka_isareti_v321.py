"""UYGULAMA İÇİ MARKA İŞARETİ — NOKTA YER TUTUCUYDU, ARTIK LOGO VAR · v321

VAKA (2026-08-26, operatör ekran görüntüsüyle): "logoyu görmüyorum." Haklı. v320 favicon'u
indirdi — ama favicon SEKME ikonudur; uygulamanın İÇİNDEKİ marka işareti ayrı bir şeydir ve
ona hiç dokunulmamıştı. Kenar çubuğu hâlâ turuncu bir nokta gösteriyordu.

VE O NOKTA BİR KAZA DEĞİLDİ — kendi şerhi sebebini yazıyordu:
    "Marka işareti bir ikon DEĞİL bir nokta: Meridian'ın kendi logosu YOK ve lucide
     kataloğundan rastgele bir glif seçmek, hiçbir şey anlatmayan bir süs olurdu."
Yani nokta, BİLİNÇLİ bir yer tutucuydu ve dayandığı önerme ("logosu yok") 2026-08-26'da
YANLIŞLANDI. Bu çivi o geçişi kayda geçirir: yer tutucu, önermesi düştüğü için kalkıyor.

GEOMETRİ İKİ YERDE YAŞIYOR — VE BU ÇİVİNİN ASIL İŞİ O:
    meridian/web/favicon.svg          → sekme ikonu (standalone belge)
    ui/src/pano/kabuk/MarkaIsareti.tsx → uygulama içi (React bileşeni)
İki ayrı render ZORUNLUDUR ve tek dosyaya indirilemez:
  · favicon `currentColor` KULLANAMAZ (ayrı belge, sayfanın rengini görmez) → sabit renk +
    `prefers-color-scheme`.
  · uygulama içi işaret `currentColor` KULLANMALIDIR (kenar çubuğu metniyle aynı renkte
    olmalı, temayla birlikte kayar) → sabit renk YANLIŞ olurdu.
  · `<img src="/favicon.svg">` ile tek kaynağa inmek de olmaz: `<img>` de ayrı belgedir,
    `currentColor`u yine miras almaz ve işaret metinden kopuk bir renkte kalır.
İKİ RENDER, TEK GERÇEK: aşağıdaki çapraz çivi ikisinin GEOMETRİSİNİN birebir aynı kalmasını
zorlar. "İki kaynak, zamanla ayrışan iki yasa" bu deponun baskın hata deseni — burada iki
kaynak KAÇINILMAZ, o yüzden ayrışma çiviyle kapatılır, kaynak sayısıyla değil.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
FAVICON = KOK / "meridian/web/favicon.svg"
BILESEN = KOK / "ui/src/pano/kabuk/MarkaIsareti.tsx"
KENAR = KOK / "ui/src/pano/kabuk/app-sidebar.tsx"

#: v0 geometrisi — operatörün tasarımı (bkz. tests/test_favicon_v320.py).
V0_M_YOLU = "M16,82 L33,17 L50,52 L67,17 L84,82"


def _serhsiz(s: str) -> str:
    """XML/JSX şerhleri sökülmüş kaynak. v320'nin dersi: yasak/beklenen desen şerhte de
    geçebilir ve şerh KODUN yerine geçmemelidir."""
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"\{/\*.*?\*/\}", "", s, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def _bilesen() -> str:
    assert BILESEN.exists(), (
        f"marka işareti bileşeni YOK: {BILESEN.relative_to(KOK)} — uygulama içi işaret "
        "yer tutucu noktada kalır")
    return _serhsiz(BILESEN.read_text(encoding="utf-8"))


# --------------------------------------------------- ÇAPRAZ ÇİVİ: TEK GERÇEK

def test_geometri_FAVICON_ile_BIREBIR():
    """ASIL ÇİVİ: iki render, tek geometri. Biri değişip öteki kalırsa marka ikiye bölünür."""
    b, f = _bilesen(), _serhsiz(FAVICON.read_text(encoding="utf-8"))
    assert V0_M_YOLU in b, f"bileşenin M yolu v0 değil (beklenen: {V0_M_YOLU})"
    assert V0_M_YOLU in f, "favicon'un M yolu v0'dan ayrışmış — v320 çivisi de düşmüş olmalı"

    def _enlem(src: str) -> tuple:
        m = re.search(r"<line\b[^>]*>", src)
        assert m, "enlem çizgisi yok"
        e = m.group(0)
        return tuple(re.search(rf'{a}="([^"]+)"', e).group(1) for a in ("x1", "y1", "x2", "y2"))

    assert _enlem(b) == _enlem(f), (
        f"enlem çizgisi AYRIŞMIŞ — bileşen {_enlem(b)}, favicon {_enlem(f)}. "
        "İki render tek geometriyi paylaşmak zorunda.")


def test_kalinlik_orani_da_AYNI():
    b, f = _bilesen(), _serhsiz(FAVICON.read_text(encoding="utf-8"))
    kal = lambda s: sorted(re.findall(r'stroke-?[Ww]idth="?\{?"?([0-9.]+)', s))
    assert kal(b) == kal(f), f"kalınlıklar ayrışmış — bileşen {kal(b)}, favicon {kal(f)}"


# ------------------------------- UYGULAMA İÇİ: currentColor ZORUNLU (favicon'un TERSİ)

def test_bilesen_currentColor_KULLANIYOR():
    """Favicon'un tam TERSİ kural ve gerekçesi dosyada yazılı: uygulama içi işaret kenar
    çubuğu metniyle aynı renkte olmalı ve temayla birlikte kaymalı."""
    b = _bilesen()
    assert "currentColor" in b, (
        "uygulama içi işaret `currentColor` kullanmıyor — sabit renk temayla kaymaz ve "
        "işaret metinden kopuk bir tonda kalır")
    assert not re.search(r'stroke="#[0-9a-fA-F]{3,6}"', b), (
        "bileşende SABİT renk var — tema değişince işaret yanlış renkte kalır")


def test_bilesen_prefers_color_scheme_TASIMIYOR():
    """Aşırıya kaçma çivisi: favicon'un çözümü buraya KOPYALANMAMALI. Uygulama içinde tema
    zaten CSS değişkenleriyle geliyor; ikinci bir tema mekanizması iki yasa demektir."""
    assert "prefers-color-scheme" not in _bilesen(), (
        "bileşen favicon'un tema mekanizmasını kopyalamış — uygulama içinde tema `currentColor` "
        "üzerinden gelir, ikinci mekanizma ayrışır")


# ----------------------------------------------- KENAR ÇUBUĞU: NOKTA GİTTİ

def test_kenar_cubugu_ISARETI_kullaniyor():
    s = _serhsiz(KENAR.read_text(encoding="utf-8"))
    assert "MarkaIsareti" in s, "kenar çubuğu marka işaretini kullanmıyor"


def test_YER_TUTUCU_nokta_gitti():
    """ASIL GÖRÜNÜR DEĞİŞİKLİK: `size-2 rounded-full bg-primary` noktası kalkmalı."""
    s = _serhsiz(KENAR.read_text(encoding="utf-8"))
    assert not re.search(r'size-2\s+shrink-0\s+rounded-full\s+bg-primary', s), (
        "yer tutucu nokta hâlâ orada — operatör ekranda logoyu göremez")


def test_BAYAT_onerme_serhten_kalkti():
    """'Meridian'ın kendi logosu YOK' cümlesi artık YANLIŞ. Bayat bir gerekçe, yanlış bir
    kararın kaynağıdır: bir sonraki oturum onu okuyup noktayı geri koyabilir."""
    ham = KENAR.read_text(encoding="utf-8")   # ŞERH DAHİL — ölçülen şey tam olarak şerh
    assert "logosu yok" not in ham.lower(), (
        "kenar çubuğunda 'Meridian'ın kendi logosu yok' gerekçesi duruyor — önerme "
        "2026-08-26'da yanlışlandı, şerh güncellenmeli")
