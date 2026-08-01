"""v153 — UIUX S1-T1/T2: DTCG jeton eş-kaydı · ham-renk linti · kontrast çivisi.

ÖLÇÜLEN KUSUR SINIFI (tek ve yeni): **jeton katmanının SESSİZCE ayrışması.**
Bu deponun kayıtlı emsali `--nav-bg`dir: renk taşıyan bir değer bir kuralın içine
sabit yazılmıştı, gece temasında dönmüyordu ve üst bar beyaz kalınca HALT kırmızısı
1.27:1'e düşüyordu — acil durdurma görünmez olmuştu. Arıza gürültüsüzdü: hiçbir test
kırmızı vermedi, çünkü "her renk jetondan gelir" ve "her renk jetonunun iki teması
vardır" kuralları YAZILIYDI ama ÖLÇÜLMÜYORDU.

Bu dosya o iki kuralı ölçer, ve üçüncüsünü ekler:

  Ç1 · EŞ-KAYIT   — meridian/web/tokens.json ile index.html'in iki :root katmanı
                    bire-bir aynı olmalı. tokens.json üretim kaynağı DEĞİL (stack'te
                    bundler yok, dagit.sh'e derleme adımı eklenmedi — UIUX iş emri
                    "strangler" kuralı); bağ derleme değil, bu çividir. Sürüklenme
                    = kırmızı.
  Ç2 · TAM PALET  — bir renk jetonu iki temaya birden girmezse kırmızı. --nav-bg
                    sınıfının kapısı burasıdır.
  Ç3 · HAM RENK   — index.html/app.js/palette.js/theme.js'te jeton dışı renk yok.
                    Allowlist BOŞ ve bu ölçüldü (bkz. IZIN_VERILEN).

  Ç4 · KONTRAST   — docs/kontrast-denetimi.md'nin çivi tablosundaki her rakam
                    KAYNAKTAN yeniden hesaplanır. Bir jeton değerlenirse rapor
                    bayatlar ve test bunu söyler; sessizce eskimiş bir denetim
                    raporu, hiç yapılmamış bir denetimden daha kötüdür.

Testler KAYNAĞA bakar (repo deseni: test_pano_turu_v139, test_pano_sessiz_hat_v151).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
INDEX = (WEB / "index.html").read_text()
APPJS = (WEB / "app.js").read_text()
PALETTE = (WEB / "palette.js").read_text()
THEME = (WEB / "theme.js").read_text()
TOKENS = json.loads((WEB / "tokens.json").read_text())
RAPOR = (SRC / "docs" / "kontrast-denetimi.md").read_text()


# =============================== KAYNAK OKUMA ===============================
def _css() -> str:
    """index.html'in YALNIZ CSS'i, yorumlar ayıklanmış. Belge metni kural sanılmasın
    (v139/v151'in aynı kuralı: bu dosyada her karar GEREKÇESİYLE yazılıyor)."""
    css = INDEX[INDEX.index("<style>") + 7:INDEX.index("</style>")]
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


CSS = _css()


def _blok(sel: str) -> str:
    i = CSS.index(sel)
    j = CSS.index("{", i)
    k = CSS.index("}", j)
    return CSS[j + 1:k]


def _jetonlar(blok: str) -> dict:
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*([^;}]+)", blok)}


ROOT = _jetonlar(_blok(":root{"))
GECE_OV = _jetonlar(_blok(':root[data-theme="gece"]'))


def _duz(dugum, yol=()):
    """tokens.json'ı (yol, token) çiftlerine indir. Token = $value taşıyan sözlük."""
    if isinstance(dugum, dict) and "$value" in dugum:
        yield yol, dugum
        return
    if isinstance(dugum, dict):
        for k, v in dugum.items():
            if k.startswith("$"):
                continue
            yield from _duz(v, yol + (k,))


TOKEN_LISTESI = list(_duz(TOKENS))
TOKEN_YOLU = {yol: tk for yol, tk in TOKEN_LISTESI}


def _css_adi(tk) -> str:
    return tk["$extensions"]["org.meridian.css"]["var"]


def _literal(tk) -> str:
    return tk["$extensions"]["org.meridian.css"]["literal"]


TEMEL = {_css_adi(tk)[2:]: _literal(tk) for yol, tk in TOKEN_LISTESI if yol[0] == "temel"}
GUNDUZ = {_css_adi(tk)[2:]: _literal(tk)
          for yol, tk in TOKEN_LISTESI if yol[:2] == ("tema", "gunduz")}
GECE = {_css_adi(tk)[2:]: _literal(tk)
        for yol, tk in TOKEN_LISTESI if yol[:2] == ("tema", "gece")}


# =============================== Ç1 · EŞ-KAYIT ===============================
def test_tokens_json_UC_KATMAN_ve_TEK_dosya():
    """Yapı beyanı kaynakta durmalı: bir okuyucu tema temsilini dosyanın kendisinden
    öğrenebilmeli, bir commit mesajından değil."""
    assert set(TOKENS) >= {"temel", "tema", "$description", "$extensions"}
    assert set(TOKENS["tema"]) >= {"gunduz", "gece"}
    beyan = TOKENS["$extensions"]["org.meridian"]
    assert "tema-temsili" in beyan and len(beyan["tema-temsili"]) >= 200, \
        "tema temsili BEYAN EDİLMEDEN kurulmuş — DTCG'nin tema yapısı yok, seçim gerekçe ister"
    assert beyan["uretim-yolu"].startswith("eş-doğrulama"), \
        "üretim yolu değişmişse (build adımı) bu testin sözleşmesi de değişmeli"


def test_her_CSS_jetonu_tokens_jsonda_BIRE_BIR():
    """Sürüklenmenin birinci yönü: CSS'te olup jetonda olmayan."""
    css_hepsi = set(ROOT)
    json_hepsi = set(TEMEL) | set(GUNDUZ)
    eksik = css_hepsi - json_hepsi
    assert not eksik, f"CSS :root'ta olup tokens.json'da olmayan jeton: {sorted(eksik)}"
    for ad, deger in ROOT.items():
        kayit = TEMEL.get(ad, GUNDUZ.get(ad))
        assert kayit == deger, \
            f"--{ad}: CSS {deger!r} ↔ tokens.json {kayit!r} — jeton katmanı ayrışmış"


def test_gece_blogu_BIRE_BIR():
    for ad, deger in GECE_OV.items():
        assert GECE.get(ad) == deger, \
            f"--{ad} (gece): CSS {deger!r} ↔ tokens.json {GECE.get(ad)!r}"


def test_tokens_jsonda_CSSte_OLMAYAN_jeton_YOK():
    """Sürüklenmenin ikinci yönü: silinmiş bir jetonun kayıtta hayalet kalması.
    Bu, kaldırılmış bir kararı hâlâ yürürlükteymiş gibi göstermek olurdu."""
    fazla = (set(TEMEL) | set(GUNDUZ)) - set(ROOT)
    assert not fazla, f"tokens.json'da olup CSS'te olmayan jeton: {sorted(fazla)}"
    fazla_gece = set(GECE) - set(GECE_OV)
    assert not fazla_gece, f"gece katmanında karşılığı olmayan jeton: {sorted(fazla_gece)}"


def test_temel_katman_TEMADAN_BAGIMSIZ():
    """`temel`e konan bir jeton gece bloğunda override EDİLEMEZ; edilirse yeri yanlış
    ve tema sessizce yarım çalışır."""
    kacak = set(TEMEL) & set(GECE_OV)
    assert not kacak, f"`temel`de duran ama gece bloğunda override edilen jeton: {sorted(kacak)}"


# =============================== Ç2 · TAM PALET ===============================
def test_gece_TAM_palet_hicbir_renk_jetonu_YARIM_KALMAZ():
    """--nav-bg ARIZASININ KAPISI. O jeton bir kuralın içinde sabit rgba idi, gece
    dönmüyordu ve üst barda HALT kırmızısı 1.27:1'e düşüyordu. Kural: renk taşıyan
    her jeton İKİ temaya birden girer. Eksikse burada durur."""
    assert set(GUNDUZ) == set(GECE), \
        f"tema katmanları ayrışıyor: {sorted(set(GUNDUZ) ^ set(GECE))}"
    assert set(GUNDUZ) == set(GECE_OV), \
        ("gündüz renk katmanı ile CSS'in gece override kümesi ayrışıyor "
         f"(GECE bloğunda karşılığı olmayan renk jetonu): {sorted(set(GUNDUZ) ^ set(GECE_OV))}")
    # ölçülmüş sayım — beyan kaynakta dursun
    assert len(GUNDUZ) == 36 and len(TEMEL) == 23 and len(ROOT) == 59, \
        f"jeton sayımı değişmiş: temel {len(TEMEL)} · renk {len(GUNDUZ)} · toplam {len(ROOT)}"


def test_renk_jetonlarinin_HEPSI_renk_TEMEL_jetonlarin_HICBIRI_degil():
    """Katman ayrımı ANLAMLI olmalı: `tema` altında renk olmayan bir şey varsa ya da
    `temel` altında renk varsa, bölünme keyfîdir ve bir sonraki turda çöker."""
    renk = re.compile(r"#[0-9a-fA-F]{6}|rgba?\(")
    for ad, lit in GUNDUZ.items():
        assert renk.match(lit), f"`tema` katmanında renk olmayan jeton: --{ad} = {lit!r}"
    for ad, lit in TEMEL.items():
        assert not renk.match(lit), f"`temel` katmanında renk jetonu: --{ad} = {lit!r}"


# =============================== Ç1b · DTCG ŞEMASI ===============================
IZINLI_ANAHTAR = {"$value", "$type", "$description", "$deprecated", "$extensions",
                  "$extends", "$ref"}
IZINLI_TIP = {"color", "dimension", "duration", "cubicBezier", "fontFamily",
              "fontWeight", "number", "shadow", "strokeStyle", "border",
              "transition", "gradient", "typography"}


def _gez(dugum, yol=(), miras=None):
    if not isinstance(dugum, dict):
        return
    tip = dugum.get("$type", miras)
    if "$value" in dugum:
        yield yol, dugum, tip
        return
    for k, v in dugum.items():
        if k.startswith("$"):
            assert k in IZINLI_ANAHTAR, f"{'.'.join(yol)}: bilinmeyen $ anahtarı {k}"
            continue
        assert not k.startswith("$"), k
        assert not re.search(r"[{}.]", k), f"DTCG ad kuralı: {k!r} `{{`/`}}`/`.` taşıyamaz"
        yield from _gez(v, yol + (k,), tip)


def test_DTCG_semasi_gecerli():
    """Biçim doğruluğu SONRADAN kanıtlanmaz: dosya DTCG diye adlandırıldıysa DTCG
    kurallarını burada geçmek zorundadır."""
    sayac = 0
    for yol, tk, tip in _gez(TOKENS):
        sayac += 1
        p = ".".join(yol)
        for k in tk:
            assert k in IZINLI_ANAHTAR, f"{p}: bilinmeyen $ anahtarı {k}"
        assert tip is None or tip in IZINLI_TIP, f"{p}: bilinmeyen $type {tip!r}"
        assert "$description" in tk and tk["$description"].strip(), \
            f"{p}: açıklamasız jeton — okuyucusuz yazım yok (YASA 6)"
        assert "$extensions" in tk and "org.meridian.css" in tk["$extensions"], \
            f"{p}: CSS eş-kaydı yok — eş-doğrulama yolu bu alan olmadan kurulamaz"
    assert sayac == 59 + 36, f"jeton sayımı {sayac} (beklenen 95 = 23 temel + 2×36 renk)"


def test_takma_adlar_COZULUYOR():
    """`{a.b.c}` biçimindeki DTCG takma adı var olmayan bir yolu gösteremez —
    gösterirse dosya kendi içinde tutarsızdır ve hiçbir araç onu okuyamaz."""
    bulunan = 0
    for yol, tk, _ in _gez(TOKENS):
        v = tk["$value"]
        if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
            hedef = tuple(v[1:-1].split("."))
            assert hedef in TOKEN_YOLU, f"{'.'.join(yol)}: çözülmeyen takma ad {v}"
            bulunan += 1
    assert bulunan >= 2, "CSS'te var(--sans)'a bağlı iki jeton var; takma ad olarak yazılmalıydı"


def _renk_coz(lit):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", lit)
    if m:
        h = m.group(1)
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)], 1.0
    m = re.fullmatch(r"rgba?\((\d+),(\d+),(\d+),([0-9.]+)\)", lit.replace(" ", ""))
    assert m, f"renk çözülemedi: {lit!r}"
    return [int(m.group(i)) for i in (1, 2, 3)], float(m.group(4))


def test_DTCG_degeri_CSS_LITERALINDEN_yeniden_uretilebilir():
    """$value ile literal ayrı ayrı elle güncellenebilir; ayrışırlarsa dosya iki
    farklı gerçeği aynı anda söyler. İkisi arasındaki bağ da ölçülür."""
    for yol, tk, tip in _gez(TOKENS):
        lit, v, p = None, tk["$value"], ".".join(yol)
        lit = tk["$extensions"]["org.meridian.css"]["literal"]
        if tip == "color":
            c, a = _renk_coz(lit)
            assert v["colorSpace"] == "srgb"
            assert v["components"] == [round(x / 255, 6) for x in c], f"{p}: bileşen ayrışmış"
            assert abs(v["alpha"] - a) < 1e-9, f"{p}: alfa ayrışmış"
            if a == 1.0:
                assert v["hex"] == lit.lower(), f"{p}: hex ayrışmış"
            else:
                assert "hex" not in v, \
                    f"{p}: alfa taşıyan jetonda opak `hex` — ekranda var olmayan bir renk beyanı"
        elif tip == "dimension":
            m = re.fullmatch(r"([0-9.]+)(px|rem)", lit)
            assert m and float(v["value"]) == float(m.group(1)) and v["unit"] == m.group(2), p
        elif tip == "duration":
            m = re.fullmatch(r"([0-9.]+)(ms|s)", lit)
            assert m and float(v["value"]) == float(m.group(1)) and v["unit"] == m.group(2), p
        elif tip == "cubicBezier":
            sayilar = [float(x) for x in re.fullmatch(r"cubic-bezier\(([^)]*)\)", lit).group(1).split(",")]
            assert v == sayilar, p
        elif tip == "shadow":
            assert lit == "none" and v == [], \
                f"{p}: gölge geri gelmiş — Omega'da box-shadow:none ölçülmüş bir karardır"


# =============================== Ç3 · HAM RENK LİNTİ ===============================
# ALLOWLIST BOŞ VE BU ÖLÇÜLDÜ (2026-08-01): dört yüzeyin tamamı tarandı, jeton
# blokları dışında TEK ham renk çıkmadı. Boş bir liste bir eksiklik değil bir bulgu:
# jeton sözleşmesi bugün fiilen %100 tutuyor. Buraya bir satır eklemek, ≥20 karakter
# gerekçe yazmayı GEREKTİRİR (YASA 4) — istisna sessizce büyüyemez.
IZIN_VERILEN: dict[str, str] = {}

_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_FONK = re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^)]*\)")
# `white-space` / `black-box` gibi bileşik sözcükler renk DEĞİL: ad tek başına durmalı.
_ADLI = re.compile(r":\s*(black|white|red|green|blue|gray|grey|orange|yellow|purple|silver)\b")


def _yorumsuz_js(s: str) -> str:
    s = "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("//"))
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def _css_govdeleri() -> str:
    """CSS'in YALNIZ bildirim gövdeleri, jeton blokları çıkarılmış.
    Seçiciler dışarıda kalır — yoksa `#gate-pw2-wrap` gibi bir id seçicisi renk sanılır."""
    css = CSS
    for sel in (":root{", ':root[data-theme="gece"]'):
        i = css.index(sel)
        j = css.index("{", i)
        k = css.index("}", j)
        css = css[:i] + css[k + 1:]
        assert sel not in css or sel == ":root{", sel
    return "\n".join(m.group(1) for m in re.finditer(r"\{([^{}]*)\}", css))


def _ham_renkler(metin: str) -> list:
    return sorted(set(_HEX.findall(metin)) | set(_FONK.findall(metin)) |
                  {"named:" + a for a in _ADLI.findall(metin)})


def _yuzeyler() -> dict:
    return {
        "index.html <style> (jeton blokları hariç)": _css_govdeleri(),
        "index.html gövdesi (satır içi stil)": INDEX[INDEX.index("</style>"):],
        "app.js": _yorumsuz_js(APPJS),
        "palette.js": _yorumsuz_js(PALETTE),
        "theme.js": _yorumsuz_js(THEME),
    }


def test_ham_renk_YOK_dort_yuzeyde():
    """Renk taşıyan hiçbir değer kuralın içine YAZILMAZ, jetondan gelir. Aksi hâlde
    ikinci tema sessizce kırılır — bu tam olarak --nav-bg'de yaşandı."""
    for ad, metin in _yuzeyler().items():
        bulunan = [h for h in _ham_renkler(metin) if h not in IZIN_VERILEN]
        assert not bulunan, f"{ad}: jeton dışı ham renk {bulunan}"


def test_allowlist_ISTISNALARI_GEREKCESIZ_OLAMAZ():
    """YASA 4: sessiz-yutma işaretli + ≥20 karakter gerekçe. Bir istisna, gerekçesi
    olmadan listeye giremez; girerse liste bir yılda anlamsızlaşır."""
    for renk, gerekce in IZIN_VERILEN.items():
        assert len(gerekce) >= 20, f"{renk}: gerekçe {len(gerekce)} karakter (≥20 gerekli)"


def test_lint_KENDINI_KANITLAR():
    """Kıramayan bir lint, yeşil veren bir süstür. Enjekte edilmiş bir ham renk
    yakalanmıyorsa yukarıdaki üç test hiçbir şey ölçmüyor demektir."""
    for tuzak in ("color:#ff00aa", "background:rgba(1,2,3,.5)", "border-color:white"):
        assert _ham_renkler("x{" + tuzak + "}"), f"lint bu tuzağı kaçırıyor: {tuzak}"
    # ve YANLIŞ POZİTİF vermemeli
    for temiz in ("white-space:nowrap", "#gate-pw2-wrap{display:none}",
                  "color:var(--tx)", "background:transparent", "fill:currentColor"):
        assert not _ham_renkler(temiz), f"lint yanlış pozitif: {temiz}"


# =============================== Ç4 · KONTRAST ÇİVİSİ ===============================
def _rgba(deger, tema):
    d, tablo = deger.strip(), (dict(ROOT, **GECE_OV) if tema == "gece" else ROOT)
    for _ in range(8):
        m = re.fullmatch(r"--([a-z0-9-]+)", d)
        if not m:
            break
        d = tablo[m.group(1)].strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", d)
    if m:
        h = m.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = re.fullmatch(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)", d)
    assert m, f"renk değil: {d!r}"
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))


def _uzerine(ust, alt):
    """8-bit sRGB'de source-over — tarayıcının fiilen yaptığı işlem. Alfa'yı
    yok sayıp jetonun ham değerini ölçmek, ekranda var OLMAYAN bir rengi ölçmektir."""
    return tuple(round(ust[i] * ust[3] + alt[i] * (1 - ust[3])) for i in range(3)) + (1.0,)


def _yigin(katmanlar, tema):
    c = _rgba(katmanlar[0], tema)
    for k in katmanlar[1:]:
        c = _uzerine(_rgba(k, tema), c)
    return c


def _lum(c):
    def k(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * k(c[0]) + 0.7152 * k(c[1]) + 0.0722 * k(c[2])


def _oran(a, b):
    l1, l2 = sorted((_lum(a), _lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def _civi_satirlari():
    """docs/kontrast-denetimi.md'nin ÇİVİ TABLOSU bölümü. Biçim:
    | mürekkep | zemin-yığını | tema | oran | eşik |"""
    i = RAPOR.index("<!-- CIVI-TABLOSU-BASI -->")
    j = RAPOR.index("<!-- CIVI-TABLOSU-SONU -->")
    for satir in RAPOR[i:j].splitlines():
        h = [x.strip() for x in satir.strip().strip("|").split("|")]
        if len(h) != 5 or h[0].startswith(("mürekkep", ":--", "---")):
            continue
        yield h


def test_rapordaki_KONTRAST_RAKAMLARI_yeniden_uretilebilir():
    """Bayat bir erişilebilirlik raporu, hiç yapılmamış bir denetimden daha kötüdür:
    okuyucu ona güvenir. Jeton değeri kımıldarsa rapor burada bayat ilan edilir."""
    sayac = 0
    for murekkep, zemin, tema, oran_s, _esik in _civi_satirlari():
        katmanlar = [k.strip() for k in zemin.split("+")]
        zc = _yigin(katmanlar, tema)
        ic = _rgba(murekkep, tema)
        ic = _uzerine(ic, zc) if ic[3] < 1.0 else ic
        olculen = _oran(ic, zc)
        assert abs(olculen - float(oran_s)) < 0.005, \
            (f"rapor BAYAT: {murekkep} üzerinde {zemin} ({tema}) — "
             f"raporda {oran_s}, kaynaktan {olculen:.2f}")
        sayac += 1
    assert sayac >= 24, f"çivi tablosu {sayac} satır — kapsam daralmış"


def test_para_renkleri_EN_KOTU_GERCEK_ZEMINDE_AA_kalir():
    """Jeton yeniden-değerleme turu geldiğinde (gündüz beyazı) bu üç renk AA altına
    düşerse pano parayı okunamaz yazıyor demektir. Eşik SONRADAN düşürülemez."""
    en_kotu = {"--green": "--green-t", "--amber": "--amber-t", "--red": "--red-t"}
    for tema in ("gunduz", "gece"):
        for ink, tint in en_kotu.items():
            zc = _yigin(["--card-2", tint], tema)
            assert _oran(_rgba(ink, tema), zc) >= 4.5, \
                f"{ink} ({tema}) kendi tinti gömülü panelde AA ALTI"


def test_odak_halkasi_HER_ZEMINDE_3_1():
    """WCAG 2.2 2.4.11/1.4.11: odak göstergesi görünür OLMAK ZORUNDA. Bu pano
    klavye-öncelikli tasarlandı; halka kaybolursa gezinme kaybolur."""
    for tema in ("gunduz", "gece"):
        for zemin in (["--bg"], ["--card"], ["--card-2"], ["--accent-tint"],
                      ["--card-2", "--red-t"], ["--card-2", "--amber-t"]):
            assert _oran(_rgba("--accent", tema), _yigin(zemin, tema)) >= 3.0, \
                f"odak halkası {tema}/{zemin} üzerinde 3:1 altında"


def test_rapor_BILINCLI_ISTISNA_ve_ONERI_bolumlerini_TASIR():
    """Kalan çiftler için hüküm önerisi rapordadır, değer değişikliği DEĞİL (WP0
    kararı: jeton yeniden-değerlemesi ayrı onay turu). İki bölüm de zorunlu:
    biri olmadan rapor ya sansürlü ya da yetkisiz bir değişiklik olur."""
    for baslik in ("## 6 · Bilinçli istisnalar", "## 7 · Değişiklik önerileri",
                   "<!-- CIVI-TABLOSU-BASI -->"):
        assert baslik in RAPOR, f"kontrast raporunda eksik bölüm: {baslik}"
    assert "ÖNERİ — UYGULANMADI" in RAPOR, \
        "öneriler uygulanmadıkları açıkça yazılmadan durursa okuyucu onları hüküm sanır"
