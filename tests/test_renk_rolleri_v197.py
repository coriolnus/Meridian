"""v197 — ALTI RENK ROLÜ, ALTI AYRI KANAL (D1 2026-08-07 · ROL 6 2026-08-24).

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
  §9  ROL 6 · GEZİNME/SEÇİM (2026-08-24) — kroma tavanı + bağlam ayrıklığı

ROL 6 NİYE VAR VE NİYE BİR SIZINTI DEĞİL. Omega "yapı hue TAŞIMAZ" diyordu ve aksanı
siyaha çekmişti. Dub'ın dili gezinmeyi maviyle taşır (aktif menü dolgusu, sayaç hapları,
bağlantılar) ve operatör kararı (KARAR-2026-08-24-B §2) bu dili bağlayıcı kıldı. Rolü
KIRMAK — yani mavinin şiddet/yön/mod kanallarına sızmasına izin vermek — ile onu ALTINCI
bir kanal olarak AÇMAK arasındaki fark ölçülebilir bir farktır ve §9 tam olarak onu ölçer:
  · mavi YALNIZ gezinme/seçim/sayaç bağlamında görünür,
  · `--nav*` hiçbir şiddet/yön/mod jetonuna BAĞLANAMAZ,
  · gezinme kroması bir TAVANA tabidir (Ö3) ve tavan burada ÇİVİLİDİR.
Birincil eylem dolgusu hâlâ akromatiktir (`--accent` midnight-ink) — "renk yalnız ölçüme
aittir" kuralının çekirdeği böylece korunur; Dub da öyle yapar.
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
# ROL 6 (2026-08-24) ÖNEKLE DEĞİL AD LİSTESİYLE tanınır, ve bu bir titizlik değil ölçülmüş
# bir tuzak: `--navh` (üst barın JS'in ölçtüğü YÜKSEKLİĞİ, `.shell`/`.pdrawer` bunu okur)
# `--nav` önekiyle eşleşir ama bir renk değil bir ÖLÇÜdür. Önek kullanan ilk sürüm dört
# yerleşim kuralını "gezinme rengi taşıyor" diye kırmızı yaktı. Rolün kendi adı `--nav`dır
# ve ailesi kapalıdır; yeni bir üye eklemek buraya bir satır yazmaktır.
# `--nav-bg` (üst bar perdesi) bu turda `tema`dan `rol`e TAŞINDI: üst bar bir GEZİNME
# yüzeyidir ve değer katmanında bırakılırsa iki katman adıyla karışır.
ROL6_AILESI = ("--nav", "--nav-2", "--nav-t", "--nav-h", "--nav-bg")


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


def test_alti_rolun_hepsi_iki_zeminde_tanimli():
    """Rol katmanının kendisi eksiksiz: her rolün jeton ailesi iki zeminde de var.

    ESKİ ADI: test_bes_rolun_hepsi_iki_zeminde_tanimli (2026-08-07 → 2026-08-24). Ad,
    ROL 6 eklenince gerçeğe uyduruldu — yanlış bir ad, kapsamı okumadan varsayan bir
    okuyucu üretir (v153'ün `dort_yuzeyde` dersi)."""
    beklenen = {
        "--sev-1", "--sev-2", "--sev-3", "--sev-1-t", "--sev-2-t", "--sev-3-t",
        "--sev-1-h", "--sev-2-h", "--sev-3-h", "--sev-2-h2", "--sev-3-damga",
        "--yon-arti", "--yon-eksi", "--yon-arti-t", "--yon-eksi-t",
        "--yon-arti-h", "--yon-eksi-h", "--yon-arti-zemin", "--yon-eksi-zemin",
        "--mod-kagit", "--mod-canli", "--mod-kesif",
        "--mod-kagit-t", "--mod-canli-t", "--mod-kesif-t",
        "--mod-kagit-h", "--mod-canli-h", "--mod-kesif-h",
        "--olcek-guven", "--olcek-guven-t", "--olcek-guven-h",
        "--nav", "--nav-2", "--nav-t", "--nav-h", "--nav-bg",
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
    """Bir kural gövdesinin OKUDUĞU roller. ROL 1-5 önekle, ROL 6 AD LİSTESİYLE tanınır
    (bkz. ROL6_AILESI gerekçesi: `--navh` bir ölçüdür, bir renk değil)."""
    r = set()
    for m in re.finditer(r"var\(\s*(--[a-z0-9-]+)", govde):
        ad = m.group(1)
        if ad in ROL6_AILESI:
            r.add("--nav")
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


def test_yapi_seciciler_YALNIZ_ROL6_tasir():
    """ROL 1: yapı akromatiktir — ŞİDDET/YÖN/MOD/ÖLÇEK hue'su gezinme rayına GİREMEZ.

    Ölçülen sızıntı (baseline T14): oturum çıkışının hover'ı HALT/FLATTEN ile AYNI kırmızı
    jetonu kullanıyordu — geri alınabilir bir eylem, geri alınamayanların dilinde.

    2026-08-24 · KAPSAM DARALDI, İDDİA DEĞİL. ROL 6 gezinme rayının KENDİ kanalıdır ve
    orada bulunması bir sızıntı değil, rolün TANIMIdır. Yasak olan hâlâ aynı: rayın bir
    alarm, bir yön ya da bir çalışma kipi rengiyle boyanması. Bu yüzden test artık
    "hiç rol yok" değil "YALNIZ ROL 6" ölçüyor — daha zayıf değil, daha KESKİN: eskiden
    `.sitem.on{background:var(--sev-2-t)}` yazan biri de, mavi yazan biri de aynı
    kırmızıyı alırdı ve ikisi aynı şey değildir."""
    for sec, govde in KURALLAR:
        if ".sitem" in sec or ".side " in sec:
            yabanci = _roller(govde) - {"--nav"}
            assert not yabanci, (
                f"gezinme rayı ROL 6 DIŞI bir rol taşıyor: {sec} → {sorted(yabanci)} "
                f"({govde.strip()})")


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
# 2026-08-24 · DUB DÖNÜŞÜMÜ. Yüzeyler Dub'ın soğuk nötr rampasına geçti.
# ~~Emekli: gündüz #fbf9f8 / #f5f4f2 / #f2efed / #ece7e3 · gece #1c1a18 / #232120 /
#   #262320 / #2f2b27 (sıcak kemik rampası, WP-P/P9).~~
# Bu sözlük index.html'in jeton bloğunun KOPYASIDIR ve ayrışırsa aşağıdaki AA ölçümleri
# gerçekte var olmayan bir zemine karşı yeşil verir. Kopya olmasının sebebi ölçüldü:
# GUNDUZ/GECE tabloları alias zincirini taşır, bu liste ise HANGİ yüzeylerin gerçek bir
# mürekkep zemini olduğunu SEÇER — o seçim bir karardır, bir çıkarım değil.
ZEMIN = {
    "gündüz": {"bg": "#fafafa", "bg2": "#f5f5f5", "card": "#ffffff", "card-2": "#fafafa"},
    "gece": {"bg": "#171717", "bg2": "#1f1f1f", "card": "#262626", "card-2": "#2e2e2e"},
}


def test_ZEMIN_kopyasi_index_html_ile_AYRISMAMIS():
    """Kopya bir tablo, ayrıştığı gün sessizce yalan söyler — ve bu dosyadaki HER AA
    ölçümü ona bağlıdır. Kaynak index.html'in jeton bloğudur; burada yalnız SEÇİM yapılır."""
    for tema, tablo in ZEMIN.items():
        kaynak = GUNDUZ if tema == "gündüz" else dict(GUNDUZ, **GECE)
        for ad, deger in tablo.items():
            assert kaynak["--" + ad] == deger, (
                f"{tema} --{ad}: ZEMIN {deger} ↔ index.html {kaynak['--' + ad]} — "
                f"kopya ayrışmış, bu dosyadaki tüm AA ölçümleri şüpheli")
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


# ---------------------------------------------------------------------------
# §9 — ROL 6 · GEZİNME/SEÇİM (2026-08-24, KARAR-2026-08-24-B §2)
# ---------------------------------------------------------------------------
# ÖLÇÜLEN KUSUR SINIFI, §2-§4'ünkiyle AYNI ama yeni bir kanalda: bir rolün ödünç
# alınması. Yeni kanal maviyi sisteme sokuyor ve mavi bu depoda bir yıl boyunca YASAKTI
# ("renk yalnız ölçüme aittir"). Yasak KALKMADI, KAPSAMI DARALDI: mavi yalnız gezinmeye
# ait. Bu bölüm o daralmanın sınırını çiviler — yoksa "gezinme rengi" bir yıl içinde
# "vurgu rengi"ne, oradan "önemli sayı rengi"ne kayar (D1'in ölçtüğü çürümenin tam yolu).

NAV_AILESI = ("--nav", "--nav-2", "--nav-t", "--nav-h", "--nav-bg")


def test_ROL6_yalniz_gezinme_secim_baglaminda():
    """`--nav*` gezinme · seçim · sayaç · konum DIŞI bir seçicide görünemez.

    İzin bir DESEN LİSTESİDİR ve her desenin ≥20 karakter GEREKÇESİ vardır (YASA 4'ün rol
    hattındaki karşılığı): liste sessizce büyürse "gezinme rengi" bir yıl içinde "vurgu
    rengi"ne, oradan "önemli sayı rengi"ne kayar — D1'in ölçtüğü çürümenin tam yolu.
    Yeni bir bağlam eklemek buraya bir SATIR YAZMAKTIR ve o satır bir karardır."""
    IZIN = {
        "nav": "üst bar perdesi ve sınırı — gezinme yüzeyinin kendisi",
        ".sitem": "görünüm listesi öğesi: seçim çubuğu + aktif dolgu (ROL 6'nın çekirdek vakası)",
        ".side": "gezinme rayının kabı",
        ".pillc": "sayaç hapı — Dub'ın sayaç dili; bir ölçüm değil bir gezinme sayacı",
        "aria-pressed": "SEÇİM durumu; rolün adı zaten GEZİNME/SEÇİM ve basılı kontrol seçimdir",
        "aria-selected": "SEÇİM durumu (sekme/filtre) — aynı kanal, aynı gerekçe",
        ".durdu": ("akış zincirinde KONUM işareti: 'şu an burada durdu' bir ARIZA değil bir YER "
                   "bildirimidir. Şiddet kanalına koymak, onay bekleyen her planı kalıcı bir "
                   "uyarıya çevirirdi — sakin turda ekranda sürekli kehribar demek olurdu."),
        ".pv-gorev": ("'Seni bekleyenler' satırı bir GEZİNME HEDEFİdir (tıklayınca ilgili "
                      "görünüme gider); uyarı hâli AYRI kuralda ve şiddet kanalındadır"),
        ".pv-fcip": "aktif filtre çipi — seçimin görünür hâli, kaldırılabilir bir seçim rozeti",
        ".pv-fsatir": "Top Views satırı bir FİLTRE KONTROLÜdür; seçili hâli aynı seçim kanalı",
        ".pv-fbar": "aynı satırın oran çubuğu — kontrolün zemini, ayrı bir anlam taşımaz",
        ".pv-rz.aktif": "aktif filtre rozeti — seçim durumunun rozet grameri içindeki hâli",
    }
    for desen, gerekce in IZIN.items():
        assert len(gerekce) >= 20, f"{desen}: gerekçe {len(gerekce)} karakter (≥20 gerekli)"
    ihlal = [(s_, sorted(_roller(g))) for s_, g in KURALLAR
             if "--nav" in _roller(g) and not any(k in s_ for k in IZIN)]
    assert not ihlal, (
        f"ROL 6 jetonu gezinme/seçim/konum DIŞI seçicide: {ihlal}\n"
        f"İzinli desenler: {sorted(IZIN)}. Yeni bir bağlam bir KARARDIR — listeye "
        f"gerekçesiyle yaz, ya da kuralı rolüne uygun bir jetona bağla.")


def test_ROL6_siddet_yon_mod_jetonuna_BAGLANAMAZ():
    """`--nav*` bir `--sev-*`/`--yon-*`/`--mod-*`/para jetonuna çözülemez.

    Ödünç alma iki yönlü olur ve ikisi de sessizdir: gezinme bir alarm hue'suna bağlanırsa
    "seçili" ile "sorunlu" aynı renk olur; tersi olursa bir alarm gezinme diliyle konuşur.
    §4'ün mod için yaptığının aynısı, ROL 6 için."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        for jeton in [j for j in tablo if j.startswith("--nav")]:
            zincir, v = [jeton], tablo[jeton].strip()
            while (m := re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)):
                zincir.append(m.group(1))
                v = tablo[m.group(1)].strip()
            kirli = [z for z in zincir[1:]
                     if z.startswith(("--sev-", "--yon-", "--mod-", "--green", "--amber", "--red"))]
            assert not kirli, f"{ad} {jeton}: şiddet/yön/mod/para jetonuna bağlı ({zincir})"


def test_ROL6_hue_MOD_bandina_girmiyor():
    """Gezinme mavisi mod için AYRILMIŞ 285-335° bandına giremez.

    §4 bunu zaten tüm jetonlar için ölçüyor; burada ROL 6 ADIYLA anılıyor ki bir gün
    gezinme moru denenirse hata mesajı hangi kararın çiğnendiğini söylesin."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        for jeton in ("--nav", "--nav-2", "--nav-t"):
            _, C, H = oklch(_coz(jeton, tablo))
            if C < 0.02:
                continue
            assert not (MOD_BANDI[0] <= H <= MOD_BANDI[1]), \
                f"{ad} {jeton}: hue {H:.1f}° MOD bandını işgal ediyor"


# Ö3'ÜN KROMA TAVANI — ÇİVİ. Ölçülen sayılar:
#   gündüz  min C(şiddet) 0,1392 (--sev-3) · C(--nav) 0,2152 · C(--nav-t) 0,0328
#   gece    min C(şiddet) 0,1054 (--sev-2) · C(--nav) 0,1458 · C(--nav-t) 0,0791..0,0874
# MÜREKKEP TAVANI TUTMADI ve değer ZORLANMADI (karar §2.1: "jeton uydurulmaz").
# Daraltma: gezinmenin BÜYÜK YÜZEYİ washtır ve TAVANA TABİ OLAN ODUR. Aşağıdaki iki test
# bu hükmün iki yarısını ayrı ayrı çakar — biri "wash tavanın altında KALMALI" (yürürlükteki
# kısıt), öteki "mürekkep tavanın üstünde ve bu BEYANLI" (bilinen sapma, sessizce
# genişleyemez). İkincisi bir gün yeşile dönerse (mürekkep tavanın altına inerse) test
# DÜŞER ve düşmesi doğrudur: o zaman daraltmaya artık gerek yoktur ve §12 güncellenmelidir.
def test_ROL6_DOLGU_kromasi_siddetin_ALTINDA():
    """Yürürlükteki kısıt: gezinmenin büyük yüzeyi (`--nav-t`) şiddetin kroma tavanının
    ALTINDA kalır. Bu, "bir alarm ile bir seçim dikkat için yarışamaz" kuralının Ö3'teki
    sayısal karşılığıdır ve `--nav-t` fiilen boyanan en geniş gezinme yüzeyidir."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        sev = min(oklch(_coz(f"--sev-{i}", tablo))[1] for i in (1, 2, 3))
        wash = oklch(_coz("--nav-t", tablo))[1]
        assert wash < sev, f"{ad}: gezinme dolgusu C={wash:.4f} şiddet C={sev:.4f} altında DEĞİL"


def test_ROL6_MUREKKEP_tavan_asimi_BEYANLI_ve_MUREKKEP_KALIYOR():
    """BEYANLI SAPMA + ONU SINIRLAYAN KURAL.

    `--nav`/`--nav-2` kroma tavanını AŞAR (electric-blue doygundur); bu karar §2.1'de
    öngörülmüş ve docs/kontrast-denetimi.md §12.3'te ölçülmüştür. Sapmanın bedeli
    kullanım yüzeyinin DARLIĞIdır — ama "darlık" KURAL SAYISI değildir: yirmi kural bir
    3px çubuğu boyayabilir, tek bir kural sayfanın yarısını. Ölçülebilir tanım şudur:

        `--nav`/`--nav-2` MÜREKKEPTİR. Büyük dolguyu washa (`--nav-t`) bırakır.

    İşlemsel hâli: bu iki jeton `color` / `box-shadow` / `border*` / `fill` / `stroke`
    olarak serbesttir; `background` olarak YALNIZ iki ADI GEÇEN küçük yüzeyde durabilir.
    Üçüncü bir dolgu, sapmayı sessizce genişletmektir ve hüküm Rol-1'e döner (jetonun
    kroması mı iner, yüzey mi daralır).

    ESKİ ADI: test_ROL6_MUREKKEP_tavan_asimi_BEYANLI_ve_YUZEYI_DAR (2026-08-24 sabahı).
    Kural-sayısı tavanıydı ve pano v2 bileşenleri gelince yanlış kırmızı verdi: on beş
    kuralın tamamı ince mürekkepti. Ölçüt değişti, İDDİA DEĞİL."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        sev = min(oklch(_coz(f"--sev-{i}", tablo))[1] for i in (1, 2, 3))
        murekkep = max(oklch(_coz(j, tablo))[1] for j in ("--nav", "--nav-2"))
        assert murekkep >= sev, (
            f"{ad}: gezinme mürekkebi C={murekkep:.4f} artık şiddet C={sev:.4f} ALTINDA — "
            f"sapma kapandı, docs/kontrast-denetimi.md §12.3'teki daraltma beyanı BAYAT")
    # DOLGU İSTİSNALARI — ADIYLA, gerekçesiyle ve ölçülmüş küçük yüzeyle.
    DOLGU_IZNI = {
        ".sitem::before": "3px genişliğinde seçim çubuğu — yüzeyi bir saç teli kadar",
        ".pillc": "sayaç hapı: iki-üç haneli, 10px mono; yüzeyi bir rozet kadar",
    }
    for sec_, gerekce in DOLGU_IZNI.items():
        assert len(gerekce) >= 20, f"{sec_}: gerekçe kısa"
    _DOLGU = re.compile(r"background(?:-color)?\s*:\s*[^;]*var\(\s*--nav(?:-2)?\s*\)")
    ihlal = [s_ for s_, g in KURALLAR if _DOLGU.search(g) and s_ not in DOLGU_IZNI]
    assert not ihlal, (
        f"ROL 6 MÜREKKEBİ büyük dolgu olarak kullanılmış: {ihlal}. Tavanı aşan bir jeton "
        f"dolguya geçemez — büyük yüzey `--nav-t` washıdır (C tavanın altında, Ö3).")
    # Ve iki istisna GERÇEKTEN duruyor mu: silinirlerse liste sessizce anlamsızlaşır.
    duran = {s_ for s_, g in KURALLAR if _DOLGU.search(g)}
    assert duran == set(DOLGU_IZNI), (
        f"dolgu istisnaları ayrışmış — kaynakta {sorted(duran)}, listede {sorted(DOLGU_IZNI)}")


def test_ROL6_wash_ustundeki_murekkep_AA():
    """Ö5'in yürürlükteki hâli: washın üstündeki metin `--nav-2`dir ve AA geçer.

    `--nav` gündüz washın üstünde 4.24 ölçtü (AA ALTI) — o yüzden `.sitem.on` `--nav-2`
    okur. Bu test iki şeyi birden çakar: (a) `--nav-2` gerçekten geçiyor, (b) `.sitem.on`
    gerçekten onu okuyor. Yalnız (a) ölçülseydi, kural yarın `--nav`a dönebilir ve ölçüm
    yeşil kalırdı."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        wash = _coz("--nav-t", tablo)
        o = kontrast(_coz("--nav-2", tablo), wash)
        assert o >= 4.5, f"{ad}: --nav-2 washın üstünde {o:.2f} — AA ALTI"
    m = re.search(r"\.sitem\.on\{([^}]*)\}", INDEX)
    assert m, ".sitem.on kuralı yok — aktif gezinme öğesinin dolgusu kayboldu"
    assert "var(--nav-t)" in m.group(1) and "var(--nav-2)" in m.group(1), \
        (f".sitem.on wash+mürekkep çiftini okumuyor: {m.group(1)!r} — Ö5 daraltması "
         f"kaynakta karşılıksız kaldı")
    assert "var(--nav)" not in m.group(1).replace("var(--nav-t)", "").replace("var(--nav-2)", ""), \
        ".sitem.on metni `--nav` ile boyuyor — Ö5 ölçtü, o kombinasyon AA ALTI (4.24)"


def test_ROL6_sayac_hapinin_murekkebi_AA():
    """Sayaç hapı: `--nav` DOLGU, `--bg2` mürekkep. Dolgu olarak mavi meşrudur (metin
    değil), ama üstündeki rakam AA geçmek zorunda — hap bir SAYI taşıyor."""
    m = re.search(r"\.pillc\{([^}]*)\}", INDEX)
    assert m and "var(--nav)" in m.group(1), ".pillc ROL 6 dolgusunu okumuyor"
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        o = kontrast(_coz("--bg2", tablo), _coz("--nav", tablo))
        assert o >= 4.5, f"{ad}: sayaç hapının rakamı {o:.2f} — AA ALTI"


def test_ROL6_birincil_eylem_dolgusu_HALA_AKROMATIK():
    """Kuralın çekirdeği: mavi gezinmeye ait, EYLEME değil. `--accent` (birincil eylem
    dolgusu) kroma taşımaz ve `--nav`a bağlanamaz — Dub'ın kendi kararı da budur
    (`primary-action-fill` siyahtır, mavi değil)."""
    for ad, tablo in (("gündüz", GUNDUZ), ("gece", GECE)):
        for jeton in ("--accent", "--accent-2"):
            _, C, _ = oklch(_coz(jeton, tablo))
            assert C < 0.02, f"{ad} {jeton}: kroma {C:.4f} — birincil eylem hue TAŞIYAMAZ"
        assert "nav" not in tablo["--accent"], "--accent gezinme jetonuna bağlanmış"


# ---------------------------------------------------------------------------
# §10 — ŞİDDET SEVİYELERİ BİRBİRİNDEN AYRILABİLİYOR MU (ÖE1 · karar §9.5)
# ---------------------------------------------------------------------------
# ÖLÇÜLEN KUSUR SINIFI VE KÖR NOKTA. Bu dosya rol AYRILIĞINI ölçer (bir kural iki rolün
# jetonunu karıştırmasın); `test_tasarim_token_v153.py` KONTRASTI ölçer (her renk kendi
# zemininde AA). İKİSİ DE "iki ŞİDDET SEVİYESİ birbirinden ayırt edilebiliyor mu" diye
# SORMUYORDU — ve sormadıkları şey 2026-08-24'te gerçekleşti: Dub ataması `--sev-1` ile
# `--sev-2`yi aynı renge çökertti (gündüz #b54000 ↔ #ba3a00, ΔE2000 5,39) ve `--sev-2` ile
# `--sev-3`ü aynı luminansa oturttu (oran 1,004, yani ayrım TAMAMEN protan/deutan'ın
# sildiği eksende). Her iki hâlde de bu dosya YEŞİL kalıyordu: roller ayrıktı, kontrastlar
# AA idi, yalnız İKİ SEVİYE AYNI GÖRÜNÜYORDU.
#
# Bedeli soyut değil: şiddet merdiveni operatörün "şimdi müdahale" ile "insan gerekiyor"
# ile "nominal"i ayırdığı kanaldır. Çökerse pano bir alarmı bir uyarıdan ayıramaz.
#
# EŞİKLER ÖLÇÜMDEN ÖNCE DONDURULDU (Rol-1, karar §9.3) ve BURADA YENİDEN YAZILIR AMA
# DEĞİŞTİRİLMEZ. Bir eşiği gevşetmek, kusurun kendisini yeniden meşrulaştırmaktır.
OE1_LUMINANS_ORANI = 1.20     # ÖE1-a · renk körlüğünün SİLEMEDİĞİ tek kanal
OE1_DELTA_E2000 = 15.0        # ÖE1-b · JND ~2,3; küçük çipte bir bakışta ayrılmalı
OE1_TINT_AA = 4.5             # ÖE1-c · mevcut G3 garantisi, GEVŞEMEZ
OE1_KOMSU = (("--sev-1", "--sev-2"), ("--sev-2", "--sev-3"))


def _lab(rgb):
    """CIE L*a*b*, D65. ΔE2000 eşiği Lab'de donduruldu; OKLab ile ölçmek başka bir
    sayı verirdi ve donmuş bir eşik başka bir metrikle ölçülemez."""
    r, g, b = (_lin(v) for v in (_hx(rgb) if isinstance(rgb, str) else rgb))
    X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    def f(t):
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29
    fx, fy, fz = f(X / 0.95047), f(Y / 1.0), f(Z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e2000(c1, c2):
    """CIEDE2000 (Sharma/Wu/Dalal). Ölçüm betiğindeki uygulamayla AYNI formül —
    `research/olcumler/dub_donusumu_2026-08-24/olc.py::delta_e2000`. İki kopya
    kasıtlıdır ve `test_OE1_delta_e2000_KENDINI_KANITLAR` ikisinin de aynı referans
    değerleri verdiğini sınar; test bir ölçüm betiğini import edip ona GÜVENEMEZ."""
    L1, a1, b1 = _lab(c1)
    L2, a2, b2 = _lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb > 0 else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp > 0 else 0.0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * (30 * math.exp(-(((hbp - 275) / 25) ** 2))))) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def test_OE1_delta_e2000_KENDINI_KANITLAR():
    """Ölçen aracın kendi çivisi. Sessizce sıfır dönen bir ΔE, aşağıdaki eşiği bir SÜSe
    çevirir; sessizce şişen bir ΔE ise gerçek bir çökmeyi yeşil gösterir."""
    assert abs(delta_e2000("#ffffff", "#000000") - 100.0) < 0.5, "beyaz↔siyah 100 olmalı"
    assert delta_e2000("#16a34a", "#16a34a") == 0.0, "aynı renk 0 olmalı"
    # ÖLÇÜLEN VAKA: Dub atamasının çökmüş çifti eşiğin ALTINDA çıkmalı — araç bu vakayı
    # görebiliyor mu diye sınanır (bkz. docs/kontrast-denetimi.md §12.7).
    assert delta_e2000("#b54000", "#ba3a00") < OE1_DELTA_E2000, \
        "araç, kusurun ta kendisi olan çifti eşiğin üstünde gösteriyor"


@pytest.mark.parametrize("tema", ["gündüz", "gece"])
def test_OE1_a_komsu_siddet_seviyeleri_LUMINANSTA_ayrisiyor(tema):
    """ÖE1-a (karar §9.3): komşu şiddet seviyelerinin luminans oranı ≥1,20, İKİ temada.

    NİYE LUMİNANS. Protan/deutan renk körlüğü kırmızı-yeşil eksenini siler ama luminans
    kanalını KORUR. Ayrımı yalnız hue'ya emanet eden bir merdiven, okuyucuların bir
    kısmında HİÇ merdiven değildir. Ölçülen çökme tam buydu: `--sev-2` ↔ `--sev-3`
    oranı 1,004 idi, yani iki seviye aynı ağırlıkta basılıyordu."""
    T = TABLO[tema]
    for a, b in OE1_KOMSU:
        o = kontrast(_coz(a, T), _coz(b, T))
        assert o >= OE1_LUMINANS_ORANI, (
            f"{tema} {a} ↔ {b}: luminans oranı {o:.3f} < {OE1_LUMINANS_ORANI} — şiddet "
            f"merdiveni renk körü okuyucu için ÇÖKMÜŞ. Eşik karar §9.3'te ölçümden ÖNCE "
            f"donduruldu ve gevşetilemez; çözüm merdiveni yeniden kurmaktır "
            f"(research/olcumler/dub_donusumu_2026-08-24/olc.py::_merdiven).")


@pytest.mark.parametrize("tema", ["gündüz", "gece"])
def test_OE1_b_komsu_siddet_seviyeleri_DELTA_E2000_ayrisiyor(tema):
    """ÖE1-b (karar §9.3): komşu seviyeler arasında ΔE2000 ≥15, İKİ temada.

    JND ~2,3'tür; bir alarm çipi küçük bir yüzeydir ve BİR BAKIŞTA ayrılması gerekir, o
    yüzden eşik JND'nin katlarındadır. Ölçülen çökme: Dub'ın `tangerine`i (41,1°) ile
    türetilmiş `loss-red`i (38,4°) arasında yalnız 2,7° vardı ve AA türetmesi ikisini
    ΔE2000 5,39'a indiriyordu."""
    T = TABLO[tema]
    for a, b in OE1_KOMSU:
        d = delta_e2000(_coz(a, T), _coz(b, T))
        assert d >= OE1_DELTA_E2000, (
            f"{tema} {a} ↔ {b}: ΔE2000 {d:.2f} < {OE1_DELTA_E2000} — iki şiddet seviyesi "
            f"bir bakışta ayrılamıyor. Eşik karar §9.3'te dondu.")


@pytest.mark.parametrize("tema", ["gündüz", "gece"])
def test_OE1_c_her_siddet_seviyesi_KENDI_TINTI_ustunde_AA(tema):
    """ÖE1-c (karar §9.3): mevcut G3 garantisi GEVŞEMEZ.

    SIRA BAĞLAYICIDIR: a ve b sağlanamıyorsa c'yi gevşetmek YASAK. Bu test o yasağın
    kapısıdır — merdiveni kurmak için okunabilirlikten çalınamaz."""
    T = TABLO[tema]
    kart = ZEMIN[tema]["card"]
    for jeton in ("--sev-1", "--sev-2", "--sev-3"):
        v = _coz(jeton, T)
        o = kontrast(v, bilesik(v, 0.10, kart))
        assert o >= OE1_TINT_AA, \
            f"{tema} {jeton} kendi %10 tinti (--card) üstünde {o:.2f} — AA ALTI"


def test_OE1_merdiven_YONU_iki_temada_TUTARLI():
    """Merdiven bir KURALDIR, bir tesadüf değil: şiddet arttıkça mürekkep zeminden
    UZAKLAŞIR. Gündüz sev-1 en KOYU, gece en AÇIK; nominal (sev-3) zemine en yakındır.

    Yön iki temada ters DÜŞERSE operatörün kas hafızası bozulur: aynı olay bir temada
    "daha ağır", ötekinde "daha hafif" görünür. Sıralamanın kendisi çivilenir, sayılar
    değil — sayılar zaten a ve b'de ölçülüyor."""
    for tema, ters in (("gündüz", False), ("gece", True)):
        T = TABLO[tema]
        Y = {j: _lum(_hx(_coz(j, T))) for j in ("--sev-1", "--sev-2", "--sev-3")}
        sirali = Y["--sev-1"] < Y["--sev-2"] < Y["--sev-3"]
        beklenen = (not sirali) if ters else sirali
        assert beklenen, (
            f"{tema} şiddet merdiveninin yönü yanlış: {Y}. "
            f"{'Gecede' if ters else 'Gündüzde'} sev-1 en "
            f"{'AÇIK' if ters else 'KOYU'} olmalı (zeminden en uzak).")


def test_OE1_hukum_BELGEDE_ve_esik_OYNAMAMIS():
    """Eşik kaynakta durur ama HÜKÜM belgede durur; ikisi ayrışırsa test bir sayıyı korur,
    kararı değil. Karar §9.3'ün üç eşiği bu dosyadakilerle BİREBİR aynı olmalı."""
    karar = (SRC / "docs" / "KARAR-2026-08-24-B-DUB-DONUSUMU.md").read_text(encoding="utf-8")
    assert "## 9 · ÖE1" in karar, "ÖE1 hükmü kararda yok — bu testin dayanağı kayboldu"
    for iz in ("1,20", "15", "4,5"):
        assert iz in karar.split("### 9.3", 1)[1].split("### 9.4", 1)[0], \
            f"karar §9.3'te {iz} eşiği bulunamadı — eşik oynatılmış olabilir"
    rapor = (SRC / "docs" / "kontrast-denetimi.md").read_text(encoding="utf-8")
    assert "12.7" in rapor and "ÖE1" in rapor, \
        "ÖE1 hükmünün ölçümü docs/kontrast-denetimi.md'ye yazılmamış (karar §9 madde 3)"
