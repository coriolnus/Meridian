"""v197 — BEŞ RENK ROLÜ, BEŞ AYRI KANAL (D1, 2026-08-07).

ÖLÇÜLEN KUSUR SINIFININ ADI: ROL SIZINTISI — bir hue'nun aynı anda birden çok anlam
taşıması. 2026-08-06 denetimi sayıyı verdi (docs/BASELINE-2026-08-06.md §C):

    --green ≥4 rol · --amber ≥5 rol · --red ≥5 rol · mod kroması için AYRILMIŞ KANAL YOK

Sebep mimariydi, dikkatsizlik değil: jetonlar bir HUE adıyla (`--green`) bağlanıyordu, bir
İŞ adıyla değil. Hue adıyla bağlanan bir kural hangi rolü taşıdığını söylemez — ve
söylemeyen bir kural, ikinci bir anlamı ödünç almayı ÜCRETSİZ kılar. Ölçülen bedel:

  · stop fiyatı koşulsuz kırmızı, hedef fiyatı koşulsuz yeşil — ikisi de bir SONUÇ değil
    bir FİYAT SEVİYESİ, ve her silahlı plan satırı bu iki yanlış rengi taşıyordu;
  · açık risk koşulsuz kehribar — bir BÜYÜKLÜK, alarm bütçesinin diliyle yazılmış;
  · "KEŞİF MODU" kehribarda — bir çalışma kipi, alarm seviyesi kanalında;
  · "ince örneklem" kehribarda — bir veri-güveni ölçüsü, yine aynı kanalda.

Bu dosya sızıntının GERİ GELMESİNİ engeller. Testler KAYNAĞA bakar (repo deseni:
test_pano_turu_v139, test_pano_durum_kartlari_v191): kusur kaynakta yaşıyor ve bir jetonun
tanımlı olması onun DOĞRU YERDE kullanıldığı anlamına gelmez.

BÖLÜMLER
  §1  iki zeminde jeton AD KÜMESİ eşit
  §2  bileşen kuralları DEĞER jetonuna (--green/--amber/--red) dokunmaz
  §3  rol ayrıklığı — bir kural iki rolün jetonunu birden taşımaz
  §4  mod kanalı ayrılmış ve şiddetten bağımsız (hue ölçümü)
  §5  yön kroması şiddetin ALTINDA (OKLCh ölçümü, iki zeminde)
  §6  koşulsuz emisyon tavanı (ölçüm betiğiyle)
  §7  kontrast çivileri — WCAG 2.2 AA, iki zeminde
  §8  kapatılan sızıntıların tek tek çivisi
"""

from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent
INDEX = (SRC / "meridian" / "web" / "index.html").read_text()
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
OLCUM = SRC / "research" / "olcumler" / "renk_rolleri_2026-08-07"

# ---------------------------------------------------------------------------
# Ortak: jeton tabloları ve kural gövdeleri
# ---------------------------------------------------------------------------
ROL_ONEK = ("--sev-", "--yon-", "--mod-", "--olcek-")


def _blok(secici: str) -> str:
    """`:root{…}` ya da `:root[data-theme="gece"]{…}` gövdesini döndür."""
    i = INDEX.index(secici + "{")
    d, j = 0, i + len(secici)
    while j < len(INDEX):
        if INDEX[j] == "{":
            d += 1
        elif INDEX[j] == "}":
            d -= 1
            if d == 0:
                return INDEX[i:j]
        j += 1
    raise AssertionError(f"{secici} bloğu kapanmıyor")


def _jetonlar(govde: str) -> dict[str, str]:
    # yorumları at — jeton adı GEÇEN bir yorum, tanımlı jeton değildir
    temiz = re.sub(r"/\*.*?\*/", " ", govde, flags=re.S)
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", temiz)}


def _renk_tasir(deger: str, tablo: dict[str, str]) -> bool:
    """Jeton bir RENK mi taşıyor (hex/rgb/transparent/renk jetonuna var())?"""
    v = deger.strip()
    for _ in range(8):
        if re.match(r"#[0-9a-fA-F]{3,8}$|rgba?\(|^transparent$", v):
            return True
        m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)
        if not m or m.group(1) not in tablo:
            return False
        v = tablo[m.group(1)].strip()
    return False


GUNDUZ = _jetonlar(_blok(":root"))
GECE = _jetonlar(_blok(':root[data-theme="gece"]'))


def _kurallar() -> list[tuple[str, str]]:
    """(seçici, gövde) — YALNIZ bileşen kuralları; iki jeton bloğu ve yorumlar hariç."""
    stil = INDEX[INDEX.index("<style>"): INDEX.rindex("</style>")]
    stil = re.sub(r"/\*.*?\*/", " ", stil, flags=re.S)
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", stil):
        sec = m.group(1).strip().splitlines()[-1].strip()
        if sec.startswith(":root") or not sec:
            continue
        out.append((sec, m.group(2)))
    return out


KURALLAR = _kurallar()

# ---------------------------------------------------------------------------
# OKLCh — kroma ve hue ölçümü (rol mimarisinin sayısal kısıtları buradan gelir)
# ---------------------------------------------------------------------------


def _hx(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb) -> float:
    r, g, b = (_lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b) -> float:
    la = _lum(_hx(a) if isinstance(a, str) else a)
    lb = _lum(_hx(b) if isinstance(b, str) else b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def bilesik(ust, alfa: float, alt):
    u = _hx(ust) if isinstance(ust, str) else ust
    a = _hx(alt) if isinstance(alt, str) else alt
    return tuple(u[i] * alfa + a[i] * (1 - alfa) for i in range(3))


def oklch(h) -> tuple[float, float, float]:
    r, g, b = (_lin(v) for v in (_hx(h) if isinstance(h, str) else h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (max(v, 0.0) ** (1 / 3) for v in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def _coz(ad: str, tablo: dict[str, str]) -> str:
    """`var(--x)` zincirini ham değere kadar aç."""
    v = tablo[ad].strip()
    for _ in range(8):
        m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)
        if not m:
            return v
        v = tablo[m.group(1)].strip()
    raise AssertionError(f"{ad}: var() zinciri kapanmıyor")


# ---------------------------------------------------------------------------
# §1 — İKİ ZEMİNDE AD KÜMESİ EŞİT
# ---------------------------------------------------------------------------
def test_iki_zeminde_ad_kumesi_esit():
    """Bir zeminde olup diğerinde olmayan jeton BUG'dır — ve sessiz bir bugdur.

    Eksik jeton ikinci temada MİRAS ALINIR: kural çalışır, ama yanlış zeminin rengiyle.
    Bu depoda bu kusur sınıfı bir kez yaşandı (üst bar gece temasında beyaz kaldı, HALT
    kırmızısı üstünde 1,27:1 ölçtü) — o yüzden eşitlik jeton adıyla çivilenir, gözle değil.
    """
    # KARŞILAŞTIRMA RENK TAŞIYAN JETONLARLA SINIRLI ve bu bilerek: geometri, tipografi,
    # boşluk ve süre iki zeminde BİREBİR aynıdır (bağlayıcı karar — gece bloğunun kendi
    # yorumu "bir jetonun burada bir KONUM ya da ÖLÇÜ değeri varsa, o bir hatadır" diyor).
    # Onları gece bloğunda TEKRAR ETMEK, aynı sayının iki kaynağını yaratmak olurdu.
    g = {k: v for k, v in GUNDUZ.items() if _renk_tasir(v, GUNDUZ)}
    n = {k: v for k, v in GECE.items() if _renk_tasir(v, GECE)}
    eksik_gece = sorted(set(g) - set(GECE))
    eksik_gunduz = sorted(set(n) - set(GUNDUZ))
    assert not eksik_gece, f"gece zemininde TANIMSIZ jeton: {eksik_gece}"
    assert not eksik_gunduz, f"gündüz zemininde TANIMSIZ jeton: {eksik_gunduz}"


def test_bes_rolun_hepsi_iki_zeminde_tanimli():
    """Rol katmanının kendisi eksiksiz: her rolün jeton ailesi iki zeminde de var."""
    beklenen = {
        "--sev-1", "--sev-2", "--sev-3", "--sev-1-t", "--sev-2-t", "--sev-3-t",
        "--sev-1-h", "--sev-2-h", "--sev-3-h", "--sev-2-h2", "--sev-3-damga",
        "--yon-arti", "--yon-eksi", "--yon-arti-t", "--yon-eksi-t",
        "--yon-arti-h", "--yon-eksi-h", "--yon-arti-zemin", "--yon-eksi-zemin",
        "--mod-kagit", "--mod-canli", "--mod-kesif",
        "--mod-kagit-t", "--mod-canli-t", "--mod-kesif-t",
        "--mod-kagit-h", "--mod-canli-h", "--mod-kesif-h",
        "--olcek-guven", "--olcek-guven-t", "--olcek-guven-h",
    }
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        assert beklenen <= set(tablo), f"{ad}: eksik rol jetonu {sorted(beklenen - set(tablo))}"


# ---------------------------------------------------------------------------
# §2 — BİLEŞEN KURALLARI DEĞER JETONUNA DOKUNMAZ
# ---------------------------------------------------------------------------
DEGER_JETONU = re.compile(r"var\(\s*--(green|amber|red)(-t|-h|-h2|-stamp)?\s*\)")


def test_bilesen_kurallari_ham_hue_okumaz():
    """İki katmanlı jeton sistemi: DEĞER katmanı (--green) → ROL katmanı (--sev-3) → kural.

    Bir kuralın içinde `var(--red)` görmek, o kuralın hangi rolü taşıdığını söylemediği
    anlamına gelir. Denetimin ölçtüğü çürüme tam buradan geldi: aynı hue beş ayrı işe
    koşuldu ve hiçbir yerde bu bir HATA gibi görünmedi.
    """
    ihlal = [(s, DEGER_JETONU.findall(g)) for s, g in KURALLAR if DEGER_JETONU.search(g)]
    assert not ihlal, f"bileşen kuralı ham hue jetonu okuyor: {ihlal}"


def test_ham_renk_literali_bilesene_sizmaz():
    """Kuralın içine yazılan bir hex/rgb, tema değişimine TEPKİ VERMEZ.

    Bu depoda ölçülmüş sonucu: gece temasında beyaz kalan üst bar. Renk taşıyan hiçbir
    değer kuralın içinde yazılmaz; jetondan gelir.
    """
    lit = re.compile(r"(#[0-9a-fA-F]{3,8}\b|\brgba?\([0-9.,\s]+\))")
    ihlal = [(s, lit.findall(g)) for s, g in KURALLAR if lit.search(g)]
    assert not ihlal, f"kural gövdesinde ham renk literali: {ihlal}"
    # app.js DOM'u çalışma anında üretir — orada da literal olmamalı
    js_lit = [m.group(0) for m in lit.finditer(re.sub(r"//[^\n]*", "", APPJS))]
    assert not js_lit, f"app.js'te ham renk literali: {js_lit[:5]}"


# ---------------------------------------------------------------------------
# §3 — ROL AYRIKLIĞI
# ---------------------------------------------------------------------------
def _roller(govde: str) -> set[str]:
    r = set()
    for m in re.finditer(r"var\(\s*(--[a-z0-9-]+)", govde):
        ad = m.group(1)
        for onek in ROL_ONEK:
            if ad.startswith(onek):
                r.add(onek)
    return r


def test_bir_kural_iki_rolu_birden_tasimaz():
    """Rol ayrıklığının işlemsel tanımı: tek bir kural iki rolün jetonunu KARIŞTIRAMAZ.

    Karıştıran bir kural, iki anlamı tek görsel olaya bindirir — ve okuyucu hangisinin
    konuştuğunu ayıramaz. Şiddet jetonu şiddet-dışı bir bağlamda görünürse bu test düşer.
    """
    ihlal = [(s, sorted(_roller(g))) for s, g in KURALLAR if len(_roller(g)) > 1]
    assert not ihlal, f"tek kuralda birden çok rol: {ihlal}"


def test_mod_jetonu_yalniz_mod_baglaminda():
    """Mod kroması "reserved permanently… used for nothing else" (Design rules §4)."""
    izin = ("data-mod", "explore", ".mod-")
    ihlal = [s for s, g in KURALLAR
             if "var(--mod-" in g and not any(k in s for k in izin)]
    assert not ihlal, f"mod jetonu mod-dışı seçicide: {ihlal}"


def test_guven_jetonu_yalniz_veri_guveni_baglaminda():
    """"ince örneklem" bir güven ölçüsüdür; şiddet ya da yön kanalını ödünç ALMAZ."""
    izin = ("thin", ".guven", "pm-thin")
    ihlal = [s for s, g in KURALLAR
             if "var(--olcek-guven" in g and not any(k in s for k in izin)]
    assert not ihlal, f"veri-güveni jetonu kendi bağlamı dışında: {ihlal}"


def test_yapi_seciciler_kromatik_degil():
    """ROL 1: yapı akromatiktir. Gezinme rayı ve oturum çıkışı hue TAŞIMAZ.

    Ölçülen sızıntı (baseline T14): oturum çıkışının hover'ı HALT/FLATTEN ile AYNI kırmızı
    jetonu kullanıyordu — geri alınabilir bir eylem, geri alınamayanların dilinde.
    """
    for sec, govde in KURALLAR:
        if ".sitem" in sec or ".side " in sec:
            assert not _roller(govde), f"gezinme rayı kromatik: {sec} → {govde.strip()}"


# ---------------------------------------------------------------------------
# §4 — MOD KANALI AYRILMIŞ VE ŞİDDETTEN BAĞIMSIZ
# ---------------------------------------------------------------------------
MOD_BANDI = (285.0, 335.0)


def test_mod_hue_bandi_yalniz_moda_ait():
    """Ayrılmış bir kanalın işlemsel tanımı: hue bandına başka jeton GİREMEZ.

    Bant 285-335° (mor-macenta). Şiddet hue'ları (~24 / ~77 / ~154) ve veri-ölçek kutupları
    (~250 mavi / ~84 toprak) bu bandın dışında; giren olursa mod artık ayrılmış değildir.
    """
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        for jeton in tablo:
            if not re.fullmatch(r"--[a-z0-9-]+", jeton):
                continue
            v = _coz(jeton, tablo)
            if not re.fullmatch(r"#[0-9a-fA-F]{3,6}", v):
                continue
            _, C, H = oklch(v)
            if C < 0.02:                       # akromatik — hue anlamsız
                continue
            icinde = MOD_BANDI[0] <= H <= MOD_BANDI[1]
            if jeton.startswith("--mod-"):
                assert icinde, f"{ad} {jeton}: hue {H:.1f}° mod bandının DIŞINDA"
            else:
                assert not icinde, f"{ad} {jeton}: hue {H:.1f}° MOD bandını işgal ediyor"


def test_mod_jetonu_siddet_jetonuna_bagli_degil():
    """Şiddet/yön hue'ları moda ÖDÜNÇ VERİLMEZ: `--mod-*` bir `--sev-*`e çözülemez."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        for jeton in [j for j in tablo if j.startswith("--mod-")]:
            zincir, v = [jeton], tablo[jeton].strip()
            while (m := re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)):
                zincir.append(m.group(1))
                v = tablo[m.group(1)].strip()
            kirli = [z for z in zincir if z.startswith(("--sev-", "--yon-", "--green", "--amber", "--red"))]
            assert not kirli, f"{ad} {jeton}: şiddet/yön jetonuna bağlı ({zincir})"


def test_mod_yapisal_tasiyici_var_ve_ucuncu_hal_uyduruk_degil():
    """Design rules: mod "any pixel"den okunur ve taşıyıcı YAPISALdır, köşe rozeti değil.

    Üçüncü hâl (ölçülemedi) `paper`a DÜŞMEZ: uydurma yasağının mod hattındaki karşılığı.
    """
    assert re.search(r"body\[data-mod\]::before\{[^}]*var\(--mod-kagit\)", INDEX), "yapısal mod bandı yok"
    assert 'body[data-mod="live"]::before' in INDEX, "canlı mod kanalı açılmıyor"
    assert 'body[data-mod="olculemedi"]::before' in INDEX, "ÖLÇÜLEMEDİ hâlinin kanalı yok"
    assert 'document.body.dataset.mod = m || "olculemedi"' in APPJS, \
        "app.js `data-mod`u <body>ye yazmıyor — bant hiçbir zaman canlıya dönmez"


# ---------------------------------------------------------------------------
# §5 — YÖN KROMASI ŞİDDETİN ALTINDA
# ---------------------------------------------------------------------------
def test_yon_kromasi_siddetin_gorunur_altinda():
    """Kârlı bir gün, bir risk ihlaliyle DİKKAT İÇİN YARIŞAMAZ.

    Yön üçüncü sinyaldir (işaret ve ok önce gelir), o yüzden kroması şiddetin altında
    olmalı. Kısıt sayısaldır ve iki zeminde de ölçülür: maks(yön C) < min(şiddet C).
    """
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        sev = min(oklch(_coz(f"--sev-{i}", tablo))[1] for i in (1, 2, 3))
        yon = max(oklch(_coz(j, tablo))[1] for j in ("--yon-arti", "--yon-eksi"))
        assert yon < sev, f"{ad}: yön C={yon:.4f} şiddet C={sev:.4f} altında DEĞİL"
        assert yon / sev <= 0.75, f"{ad}: yön/şiddet kroma oranı {yon / sev:.2f} — 'görünür altında' değil"


def test_yon_ikinci_kanali_kodda_duruyor():
    """Hue üçüncü sinyaldir; birinci ve ikinci kanal (işaret, biçim) kaldırılmadı."""
    assert "const isr = (x, metin)" in APPJS, "açık `+` işareti sözleşmesi (isr) kayboldu"
    assert "Yokluk bir işaret değildir" in APPJS, "isr sözleşmesinin gerekçesi silinmiş"


# ---------------------------------------------------------------------------
# §6 — KOŞULSUZ EMİSYON TAVANI
# ---------------------------------------------------------------------------
def _tarayici():
    yol = OLCUM / "tara_emisyon.py"
    assert yol.exists(), f"ölçüm betiği YOK: {yol}"
    spec = importlib.util.spec_from_file_location("tara_emisyon", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_kosulsuz_emisyon_tavani():
    """KOŞULSUZ emisyon = veri ne olursa olsun basılan renk. "Renk yalnız anomalide" der.

    Denetim 164 koşulsuz emisyon saydı. Bu tur onları taradı, sınıflandırdı ve temizledi.
    TAVAN 0: bir emisyon ya bir anomali dalındadır (meşru) ya da rengi hak etmiyordur.
    Sayı elle değil ÖLÇÜM BETİĞİYLE üretilir — tavanı yükseltmek bilinçli bir karardır.
    """
    mod = _tarayici()
    ks, kl = mod.scan(str(SRC / "meridian" / "web" / "app.js"))
    kuyruk = [f'{x["satir"]}:{x["sinif"]} {x["kod"][:90]}' for x in ks]
    assert len(ks) == 0, f"koşulsuz emisyon ({len(ks)}) — sessiz kısaltma yok, kuyruk:\n" + "\n".join(kuyruk)
    assert kl, "koşullu emisyon sıfır — tarayıcı bozulmuş olmalı (anomali renkleri de silinmiş)"


# ---------------------------------------------------------------------------
# §7 — KONTRAST ÇİVİLERİ (WCAG 2.2 AA)
# ---------------------------------------------------------------------------
ZEMIN = {
    "gündüz": {"bg": "#fbf9f8", "bg2": "#f5f4f2", "card": "#f2efed", "card-2": "#ece7e3"},
    "gece": {"bg": "#1c1a18", "bg2": "#232120", "card": "#262320", "card-2": "#2f2b27"},
}
TABLO = {"gündüz": GUNDUZ, "gece": GECE}


@pytest.mark.parametrize("jeton", ["--yon-arti", "--yon-eksi", "--mod-canli", "--mod-kesif", "--olcek-guven"])
def test_yeni_jetonlar_iki_zeminde_AA(jeton):
    """Her yeni jeton, ÇIPLAK yüzeylerde ve KENDİ %10 tinti üstünde AA geçer.

    Tint ölçülür çünkü çip içinde jetonun fiilen oturduğu zemin odur — ve tint zemini
    kendi mürekkebine doğru taşır (Tint-Direction Rule): açık zeminde yardım eder, koyu
    zeminde ZARAR verir. Naif ters çevirme bu yüzden yasak.
    """
    for tema, Z in ZEMIN.items():
        v = _coz(jeton, TABLO[tema])
        for ad, zem in Z.items():
            assert kontrast(v, zem) >= 4.5, f"{tema} {jeton} çıplak {ad}: {kontrast(v, zem):.2f}"
            g = bilesik(v, 0.10, zem)
            assert kontrast(v, g) >= 4.5, f"{tema} {jeton} kendi tinti /{ad}: {kontrast(v, g):.2f}"


def test_matris_hucre_rakami_AA_kalir():
    """Yön hue'su düştü ama hücre rakamı DÜŞMEDİ: dolgu zemini daha az kaydırıyor."""
    for tema, Z in ZEMIN.items():
        T = TABLO[tema]
        tx, tx2 = _coz("--tx", T), _coz("--tx2", T)
        for jeton, alfa in (("--yon-arti", 0.08), ("--yon-eksi", 0.07)):
            for z in ("bg", "card"):
                huc = bilesik(_coz(jeton, T), alfa, Z[z])
                assert kontrast(tx, huc) >= 4.5, f"{tema} hücre rakamı /{z}: {kontrast(tx, huc):.2f}"
                assert kontrast(tx2, huc) >= 4.5, f"{tema} hücre meta /{z}: {kontrast(tx2, huc):.2f}"


def test_mod_bandi_ve_guven_kenari_metin_disi_3_1():
    """WCAG 2.2 1.4.11: bir BİLEŞENİ TANIMLAYAN bilgi 3:1 ister.

    İkisi de tam olarak bu sınıfta: mod bandı "hangi moddayım"ın yapısal cevabı, kesik
    kenar da "bu hücrenin örneklemi ince"nin. Kart/çip saç telleri BEYANLI SAPMADA kalır
    (DESIGN.md § Non-text contrast) — onlar dolgularıyla tanınır, bunlar tek taşıyıcı.
    """
    for tema, Z in ZEMIN.items():
        T = TABLO[tema]
        bant = bilesik(_coz("--mod-kagit", T), 0.65, Z["bg"])
        assert kontrast(bant, Z["bg"]) >= 3.0, f"{tema} kâğıt mod bandı: {kontrast(bant, Z['bg']):.2f}"
        assert kontrast(_coz("--mod-canli", T), Z["bg"]) >= 3.0, f"{tema} canlı mod bandı"
        alfa = float(re.search(r"[.\d]+\)$", T["--olcek-guven-h"]).group(0)[:-1])
        mur = re.search(r"rgba\((\d+),\s*(\d+),\s*(\d+)", T["--olcek-guven-h"]).groups()
        for jeton, a in (("--yon-arti", 0.08), ("--yon-eksi", 0.07)):
            for z in ("bg", "card"):
                huc = bilesik(_coz(jeton, T), a, Z[z])
                kenar = bilesik(tuple(int(x) for x in mur), alfa, huc)
                assert kontrast(kenar, huc) >= 3.0, \
                    f"{tema} ince-örneklem kenarı /{z}: {kontrast(kenar, huc):.2f}"


def test_kaynak_sirasi_cakismasi_kapali():
    """Rol sınıfı, AYNI özgüllükteki kaptan sonra gelmeli — yoksa renk sessizce ölür.

    Ölçüldü: `.chain`/`.hint` rol sınıflarından SONRA tanımlıydı ve `class="hint warn"`
    basan altı emisyon ekranda GRİ çıkıyordu. Kural kaynakta canlı, ekranda ölüydü —
    `.pm-yield` için 2026-07'de belgelenen çakışmanın aynısı.
    """
    for kap, rol in (("chain", "sev-1"), ("hint", "warn"), ("hint", "sev-2")):
        assert f".{kap}.{rol}{{" in INDEX, f".{kap}.{rol} kuralı yok — rol rengi kap tarafından eziliyor"


# ---------------------------------------------------------------------------
# §8 — KAPATILAN SIZINTILARIN TEK TEK ÇİVİSİ
# ---------------------------------------------------------------------------
def test_stop_ve_hedef_fiyati_notr():
    """Bir FİYAT SEVİYESİ bir sonuç değildir: koşulsuz kırmızı/yeşil olamaz (T5)."""
    assert 'class="mono-num neg">stop' not in APPJS, "stop fiyatı hâlâ koşulsuz kırmızı"
    assert 'class="mono-num pos">hedef' not in APPJS, "hedef fiyatı hâlâ koşulsuz yeşil"
    assert 'class="mono-num">stop ${trn(p.stop, 2)}' in APPJS, "stop satırı kaybolmuş"


def test_risk_buyuklukleri_notr():
    """gerçekleşen/açık/geri verilen R üçü de BÜYÜKLÜK, hiçbiri hüküm (T6)."""
    for kalip in ('class="mono-num pos">gerçekleşen', 'class="mono-num warn">açık',
                  'class="mono-num neg">${v.geri_verilen_r'):
        assert kalip not in APPJS, f"risk büyüklüğü hâlâ renkli: {kalip}"


def test_kesif_modu_siddet_kanalindan_cikti():
    """KEŞİF MODU bir çalışma kipidir, bir alarm seviyesi değil (T7)."""
    m = re.search(r"\.hudchip\.explore\{([^}]*)\}", INDEX)
    assert m and "--mod-kesif" in m.group(1) and "--amber" not in m.group(1), \
        "keşif çipi hâlâ şiddet kanalında"
    m2 = re.search(r"body\.explore-mode::after\{[^}]*\}", INDEX, re.S)
    assert m2 and "--mod-kesif" in m2.group(0), "keşif çerçevesi hâlâ şiddet kanalında"


def test_ince_orneklem_veri_guveni_kanalinda():
    """"ince örneklem" bir güven ölçüsüdür — §5'in rolü, §2'nin hue'sunda duramaz."""
    m = re.search(r"\.pm-cell\.thin\{([^}]*)\}", INDEX)
    assert m and "--olcek-guven-h" in m.group(1), "ince örneklem halkası hâlâ kehribar"
    assert 'class="guven">ince örneklem' in APPJS, "ince örneklem metni güven kanalında değil"


def test_etiket_ve_kimlik_dizeleri_akromatik():
    """ROL 1: bir aile adı, bir pencere kimliği ya da bir sayaç kromatik BOYANMAZ."""
    for kalip in ('<b class="warn">${esc(f.en_yogun_aile', '<b class="pos">${esc(ur.pencere_id',
                  '<b class="pos">DOĞDU', '<b class="warn">${sm.tickers}'):
        assert kalip not in APPJS, f"etiket/kimlik dizesi hâlâ kromatik: {kalip}"


def test_dinamik_jeton_adlari_rol_adidir():
    """`var(--${renk})` kalıbı hue adı TAŞIYAMAZ — orada da rol adı geçerlidir."""
    ihlal = [m.group(1) for m in re.finditer(r'var\(--\$\{[^}]*?"(green|red|amber)"', APPJS)]
    assert not ihlal, f"dinamik jeton hâlâ hue adıyla: {ihlal}"


# --- sermaye reset'i: TEK OLGU, TEK KANAL (v246-D) --------------------------------------------
# YORUM SATIRLARI SAYILMAZ (repo deseni: test_pano_durum_kartlari_v191, test_wp2d_pano_beyani_v246):
# gerekçe kaynakta durur ama BİLDİRİM değildir — bir yorumdaki "sermaye reset'i" bir emisyon değil.
APPJS_KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
ROL_SINIFI = re.compile(r'\b(pos|neg|warn)\b')


def _saran_etiket(metin: str, i: int) -> str:
    """`i` konumundaki metni saran EN YAKIN AÇILIŞ etiketini döndür (`<b>`, `<span class="…">`).

    PENCERE DEĞİL ETİKET ölçülür: "şu kadar karakter geride `warn` geçmiyor" kırılgan bir
    iddiadır (araya giren bir kardeş emisyon onu hem yanlış düşürür hem yanlış geçirir);
    metni fiilen boyayan şey saran etikettir. Kapanış etiketleri atlanır; etiket metinden
    önce kapanmıyorsa saran etiket YOKTUR (çıplak metin) ve boş dize döner.
    """
    j = metin.rfind("<", 0, i)
    while j >= 0:
        k = metin.find(">", j)
        if k < 0 or k >= i:
            return ""
        if metin[j + 1:j + 2] != "/":
            return metin[j:k + 1]
        j = metin.rfind("<", 0, j)
    return ""


def test_sermaye_reseti_hicbir_yuzeyde_siddet_tasimaz():
    """Sermaye reset'i bir ANOMALİ DEĞİLDİR: operatörün kayıtlı, kasıtlı eylemidir.

    `sermaye.uygula` onu yazar, işaretin bir KİMLİĞİ vardır (`SR-…`) ve olay defterinde
    izlenir. Ona `warn` vermek "bir şey yanlış" der — YANLIŞ BİLGİ. Ölçülen kusur bu turda
    İKİ YERDEYDİ ve ikisi AYRIŞMIŞTI: Birikim şeridi (`egriBeyani` ④) kehribar basıyordu,
    Genel Bakış mini eğrisi de (`gb-alt`) ayrı bir kehribar. Aynı olgu iki yüzeyde iki
    şiddet taşıyorsa okuyucu hangisine inanacağını bilemez — bu deponun "aynı gerçek iki
    yerde" sınıfı. Çivi ÜÇÜNCÜ bir yüzeyde yeniden doğmasını engeller.

    Renk gitti diye BİLGİ gitmedi: kırılma sayısı, tarihi, iki değeri, kimliği ve konum
    beyanı yerinde — nötr `<b>` ile. İkinci blok tam da "rengi silerek geçme" hilesini
    kapatır (§6'nın `kl` assert'iyle aynı gerekçe).
    """
    ihlal = []
    for m in re.finditer(r"sermaye reset", APPJS_KOD):
        etiket = _saran_etiket(APPJS_KOD, m.start())
        if ROL_SINIFI.search(etiket):
            ihlal.append((APPJS_KOD[:m.start()].count("\n") + 1, etiket, APPJS_KOD[m.start():m.start() + 40]))
    assert not ihlal, f"sermaye reset şiddet kanalında: {ihlal}"

    # GÖRÜNÜRLÜK KAYBI DEĞİL — dört yüzeyin dördü de kırılmayı hâlâ söylüyor:
    assert "<b>sermaye reset ${esc(String(m.tarih" in APPJS, "Birikim şeridi (④) reset satırını basmıyor"
    assert "sermaye reset'i</b>" in APPJS, "Genel Bakış mini eğrisi reset SAYISINI basmıyor"
    assert ">sermaye reset · ${esc(String(m.tarih" in APPJS, "grafikteki kırılma işareti etiketsiz"
    assert "sermaye reset işareti" in APPJS, "aria beyanı kırılmayı söylemiyor (sesli gizleme)"
    # ŞERİT KİMLİĞİ VE KONUMU TAŞIMAYA DEVAM EDER: kimliksiz bir kırılma izlenemez.
    assert "<code>${esc(m.id)}</code>" in APPJS, "reset kimliği şeritten düşmüş"
    assert "m.konum_neden" in APPJS, "konum beyanı şeritten düşmüş"
