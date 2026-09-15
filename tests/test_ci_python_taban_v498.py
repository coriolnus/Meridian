"""test_ci_python_taban_v498.py — CI PYTHON TABANI (>=3.11) GRAMER ÇİVİSİ (TSK-190, 2026-09-15).

NEDEN VAR — ÖLÇÜM. CI'ın duman kapısı ilk adımda `compileall`i BEYAN EDİLEN tabanda (3.11) koşar;
CI Python'ı bunun için bilerek 3.11'e sabitlenir. Yerel geliştirme venv'i ise 3.12'dir. Bu fark iki
kez aynı sınıf arızayı üretti: 3.12+'da geçerli, 3.11'de SÖZDİZİMİ HATASI olan bir ifade yerelde
yeşil görünüp CI'ı derleme adımında kesti — ve derleme kesildiği için CI'da SIFIR test koştu.
  · 2026-08-15: ilk PEP 701 f-string vakası (CI bu yüzden 3.11'e sabitlendi).
  · 2026-09-07 (TSK-012 B1): AYNI SINIF geri geldi — meridian/sohbet.py içinde bir f-string
    YERLEŞTİRME ALANI satır kırıyor ve alan içinde tırnak kullanıyordu. main'deki son 100 CI
    koşumunun HEPSİ (en az 2026-09-13'ten beri) bu tek satırda öldü.
İlk vaka bir kural bıraktı ama ÇİVİ bırakmadı: kapı yalnız CI'da, yani birleşme ANINDAN SONRA
konuşuyordu. Bu dosya aynı hükmü YEREL 3.12 suite'inde verir — kırmızı, PR açılmadan düşer.

ÜÇ İDDİA:
  T1  meridian/ + tests/ + ops/ altındaki her .py dosyası 3.11 tabanında DERLENİR.
  T2  Çivinin taradığı kök kümesi, duman kapısının derlediği kümeyi EN AZ kapsar (ops fazladan —
      bilinçli: duman kapısı listesi dar tutulur, çivinin dakikası yoktur).
  T3  Taban ÜÇ yerde aynı sayıyı söyler: pyproject requires-python · CI iş akışının --python
      bayrağı · bu dosyanın TABAN sabiti. Ayrışırsa kırmızı (tek-kaynak yasası).

NASIL ÖLÇÜLÜR — İKİ KATMAN, ÇÜNKÜ TEK KATMAN KÖR (ölçüldü 2026-09-15, bu depoda, 3.12.7 ile):
  (A) ast.parse(..., feature_version=(3, 11)) — PEP 695 tip parametrelerini ve `type` ifadesini
      REDDEDER (ölçüldü: "Type parameter lists are only supported in Python 3.12 and greater").
      AMA PEP 701 f-string'lerini REDDETMEZ: feature_version GRAMER kapısıdır, TOKENIZER'ı
      geriye sarmaz — yukarıdaki iki vakanın İKİSİ de bu katmandan sessizce geçer.
  (B) 3.11 TOKENIZER EMÜLASYONU — 3.12 tokenize'ının f-string parçalarını (FSTRING_START /
      FSTRING_END) kullanarak literalin KAYNAK METNİNİ geri toplar ve 3.11'in dizgeyi nerede
      kapatacağını kaçış-duyarlı tarar. 3.11'in dört yasağı burada ölçülür (hepsi 3.11.15
      yorumlayıcısıyla ÖLÇÜLDÜ, tahmin edilmedi):
        1. tek tırnaklı f-string literali satır kıramaz  → "unterminated string literal"
        2. yerleştirme alanı dış tırnağı yeniden kullanamaz → "f-string: unmatched '['" vb.
        3. yerleştirme alanı ters-bölü içeremez
        4. yerleştirme alanı yorum (#) içeremez
      NEGATİF KONTROL (aynı ölçüm): ÜÇ tırnaklı f-string'in alanı 3.11'de SATIR KIRABİLİR —
      bu katman onu ihlal saymaz, aksi hâlde yanlış alarm üretirdi (yasanın en pahalı arızası).
  Çivi 3.11'in KENDİSİNDE koşarsa (CI) hiçbiri kullanılmaz: hüküm doğrudan compile()'dan alınır.
  Yorumlayıcı-atlamalı bir SKIP yoktur — katmanlar her yorumlayıcıda hüküm verir.

KAPSAM SINIRI: bu dosya SÖZDİZİMİ tabanını ölçer, KÜTÜPHANE tabanını (3.12'de doğan stdlib
işlevleri, örneğin yeni itertools üyeleri) ÖLÇMEZ — o sınıf ancak koşum zamanında patlar ve
duman kapısının pytest adımının işidir.
"""
from __future__ import annotations

import ast
import io
import pathlib
import re
import sys
import tokenize

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

#: Beyan edilen taban. T3 bunu pyproject ve CI iş akışıyla KARŞILAŞTIRIR — burada elle yazılı
#: olması bir kopya değil, ayrışmayı görünür kılan ÜÇÜNCÜ tanıktır.
TABAN = (3, 11)

#: Taranan kökler. T2 bunun duman kapısının kümesini kapsadığını ölçer.
KOKLER = ("meridian", "tests", "ops")

#: 2026-09-07'de CI'ı kesen İFADENİN KENDİSİ — düz dizge olarak saklanır (bu dosya onu ASLA
#: derlemez). Çivinin mutasyon kontrolü: bu metin ihlal ÜRETMEZSE çivi kör demektir.
ESKI_IFADE = (
    'cevap = (f"model yok — zincirin hiçbir ayağı cevap vermedi ({sebepler or \'sebep \'\n'
    "         'ölçülemedi'}). Cevap ÜRETİLMEDİ; uydurulmadı.\")\n"
)

_ONEK_HARFLERI = "fFrRbBuU"


# ---------------------------------------------------------------------------
# ÖLÇÜM ÇEKİRDEĞİ
# ---------------------------------------------------------------------------
def _satir_baslangiclari(kaynak: str) -> list[int]:
    """Her satırın MUTLAK karakter indeksi. tokenize konumları (satır, sütun) verir; literalin
    kaynak metnini geri toplamak için düz indekse çevrilir. Bölme `\\n` ile yapılır — splitlines
    `\\x0c`/`\\u2028` gibi karakterleri de böler ve tokenize'ın satır sayımıyla AYRIŞIRDI."""
    bas = [0]
    for satir in kaynak.split("\n"):
        bas.append(bas[-1] + len(satir) + 1)
    return bas


def _tirnak(baslangic_metni: str) -> str:
    """FSTRING_START metninden (`f"`, `rf'''` …) tırnak dizisini ayırır."""
    return baslangic_metni.lstrip(_ONEK_HARFLERI)


def _literal_ihlali(lit: str, tirnak: str) -> str | None:
    """3.11 TOKENIZER EMÜLASYONU. Literal gövdesini kaçış-duyarlı tarar (ters-bölü bir sonraki
    karakteri yutar — ham dizgelerde de tokenizasyon açısından öyledir) ve 3.11'in dizgeyi
    NEREDE kapatacağını bulur. İki hüküm: tek tırnaklı literalde ham satır sonu (kapanmamış
    dizge) ve kapanışın literal SONUNDAN önce gelmesi (alan dış tırnağı yeniden kullanmış)."""
    tek = len(tirnak) == 1
    i = len(lit) - len(lit.lstrip(_ONEK_HARFLERI)) + len(tirnak)
    while i < len(lit):
        if lit[i] == "\\":
            i += 2
            continue
        if tek and lit[i] == "\n":
            return ("tek tırnaklı f-string literali SATIR KIRIYOR (PEP 701, 3.12+); "
                    "3.11 tokenizer'ı burada 'unterminated string literal' der")
        if lit.startswith(tirnak, i):
            if i + len(tirnak) != len(lit):
                return (f"f-string yerleştirme alanı DIŞ TIRNAĞI ({tirnak}) yeniden kullanıyor "
                        "(PEP 701, 3.12+); 3.11 dizgeyi orada kapatır")
            return None
        i += 1
    return None      # kapanış hiç yok: tokenize zaten TokenError verirdi, aşağıda yakalanır


def _pep701_ihlalleri(kaynak: str, kunye: str) -> list[str]:
    """KATMAN B. 3.12'nin f-string parçalarını kullanır; 3.11 ve öncesinde (parça yok) boş döner
    — orada yorumlayıcının KENDİSİ taban olduğu için bu katmana zaten gerek kalmaz."""
    if not hasattr(tokenize, "FSTRING_START"):
        return []
    bas = _satir_baslangiclari(kaynak)
    ihlaller: list[str] = []
    yigin: list[dict] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(kaynak).readline):
            if tok.type == tokenize.FSTRING_START:
                yigin.append({"bas": bas[tok.start[0] - 1] + tok.start[1],
                              "tirnak": _tirnak(tok.string), "satir": tok.start[0], "suslu": 0})
                continue
            if tok.type == tokenize.FSTRING_END and yigin:
                ust = yigin.pop()
                lit = kaynak[ust["bas"]:bas[tok.end[0] - 1] + tok.end[1]]
                neden = _literal_ihlali(lit, ust["tirnak"])
                if neden is not None:
                    ihlaller.append(f"{kunye}, satır {ust['satir']}: {neden}")
                continue
            if not yigin:
                continue
            ust = yigin[-1]
            if tok.type == tokenize.OP and tok.string in ("{", "}"):
                ust["suslu"] += 1 if tok.string == "{" else -1
                continue
            if ust["suslu"] <= 0:
                continue                      # literal metin / biçim-spesi dışı bölge
            satir_no = ust["satir"]
            if tok.type == tokenize.COMMENT:
                ihlaller.append(f"{kunye}, satır {satir_no}: f-string yerleştirme alanında YORUM "
                                "var (3.12+); 3.11 'expression part cannot include #' der")
            elif tok.type != tokenize.FSTRING_MIDDLE and "\\" in tok.string:
                ihlaller.append(f"{kunye}, satır {satir_no}: f-string yerleştirme alanında "
                                "TERS-BÖLÜ var (3.12+); 3.11 'cannot include a backslash' der")
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        ihlaller.append(f"{kunye}: tokenize edilemedi — {exc!r}")
    return ihlaller


def taban_ihlalleri(kaynak: str, kunye: str) -> list[str]:
    """Kaynağın beyan edilen tabanda (TABAN) DERLENMEYECEĞİNİ gösteren bulgular; boş = temiz."""
    if sys.version_info[:2] <= TABAN:
        try:
            # `dont_inherit=True` iki gerekçeyle (biri v334'ün yasası, biri bu ölçümün özü): bu
            # dosyanın `from __future__ import annotations` satırı ölçülen kaynağa SIZMAMALI —
            # sızarsa hüküm, tabanın değil ÇAĞIRANIN bayraklarının hükmü olurdu.
            compile(kaynak, kunye, "exec", dont_inherit=True)
        except SyntaxError as exc:
            return [f"{kunye}, satır {exc.lineno}: SyntaxError: {exc.msg}"]
        return []
    try:
        ast.parse(kaynak, filename=kunye, feature_version=TABAN)
    except SyntaxError as exc:
        # KATMAN A kırmızıysa B anlamsızdır: ayrıştırılamayan kaynakta ikinci hüküm gürültüdür.
        return [f"{kunye}, satır {exc.lineno}: 3.11 grameri reddediyor — {exc.msg}"]
    return _pep701_ihlalleri(kaynak, kunye)


def _py_dosyalari() -> list[pathlib.Path]:
    ler: list[pathlib.Path] = []
    for kok in KOKLER:
        ler += [p for p in (REPO / kok).rglob("*.py") if "__pycache__" not in p.parts]
    return sorted(ler)


# ---------------------------------------------------------------------------
# T1 — AĞAÇ TABANDA DERLENİR
# ---------------------------------------------------------------------------
def test_T1_butun_kaynak_agaci_beyan_edilen_tabanda_derleniyor():
    dosyalar = _py_dosyalari()
    assert len(dosyalar) > 200, f"tarama kümesi şüpheli derecede küçük: {len(dosyalar)}"
    bulgular: list[str] = []
    for yol in dosyalar:
        bulgular += taban_ihlalleri(yol.read_text(encoding="utf-8"),
                                    str(yol.relative_to(REPO)))
    assert bulgular == [], (
        "Beyan edilen Python tabanında (%d.%d) DERLENMEYEN kaynak var — CI duman kapısının ilk "
        "adımı bunda ölür ve o koşumda SIFIR test koşar:\n  %s"
        % (TABAN[0], TABAN[1], "\n  ".join(bulgular)))


# ---------------------------------------------------------------------------
# T1-MUTASYON — ÇİVİNİN KENDİSİ ISIRIYOR MU
# ---------------------------------------------------------------------------
def test_T1_civisi_CInin_kestigi_ESKI_IFADEYI_isiriyor():
    """Yeşil bir T1 ancak çivi ISIRIYORSA kanıttır: 2026-09-07'de CI'ı kesen ifadenin KENDİSİ
    burada geri konur ve ihlal ÜRETMESİ beklenir."""
    bulgular = taban_ihlalleri(ESKI_IFADE, "sentetik_eski_ifade")
    assert bulgular, "ÇİVİ KÖR: CI'ı fiilen kesen ifade ihlal üretmedi"
    assert "SATIR KIRIYOR" in bulgular[0] or "SyntaxError" in bulgular[0], bulgular


@pytest.mark.parametrize("ad,kaynak", [
    ("PEP701 alan içinde dış tırnak", 'x = f"a {d["k"]} b"\n'),
    ("PEP701 iç içe f-string aynı tırnak", 'x = f"{f"{b}"}"\n'),
    ("PEP695 tip parametresi", "def f[T](x: T) -> T: return x\n"),
    ("type ifadesi", "type X = int\n"),
])
def test_T1_civisi_3_12ye_OZGU_grameri_isiriyor(ad, kaynak):
    assert taban_ihlalleri(kaynak, "sentetik_" + ad), f"ÇİVİ KÖR: {ad}"


@pytest.mark.parametrize("ad,kaynak", [
    # NEGATİF KONTROL — 3.11.15 yorumlayıcısıyla ÖLÇÜLDÜ: üçü de 3.11'de DERLENİR. Çivi bunlara
    # kırmızı derse yanlış alarm üretiyor demektir (yasanın en pahalı arızası).
    ("üç tırnaklı f-string alanı satır kırabilir", 'x = f"""a {b +\n  c} d"""\n'),
    ("alanda FARKLI tırnak serbest", "x = f\"a {d['k']} b\"\n"),
    ("üç tırnaklı çok satırlı metin", 'x = f"""a\nb {c} d"""\n'),
    ("except* 3.11'de vardır", "try:\n    pass\nexcept* ValueError:\n    pass\n"),
])
def test_T1_civisi_3_11de_GECERLI_grameri_ISIRMIYOR(ad, kaynak):
    assert taban_ihlalleri(kaynak, "sentetik_" + ad) == [], f"YANLIŞ ALARM: {ad}"


def test_T1_katman_A_tek_basina_PEP701e_KOR_oldugu_icin_B_KATMANI_ZORUNLU():
    """Ölçülmüş gerçek, savunulan tasarım kararının gerekçesi: feature_version TOKENIZER'ı geriye
    sarmaz. Bu davranış bir gün değişirse (CPython feature_version'ı f-string'lere de uygularsa)
    bu test kırılır ve B katmanının gerekçesi YENİDEN ÖLÇÜLÜR — sessizce fazlalığa dönüşmez."""
    if sys.version_info[:2] <= TABAN:
        pytest.skip("yorumlayıcı zaten taban — katman ayrımı bu yorumlayıcıda anlamsız")
    ast.parse('x = f"a {d["k"]} b"\n', feature_version=TABAN)     # KIRMIZI DEĞİL: geçiyor
    assert _pep701_ihlalleri('x = f"a {d["k"]} b"\n', "sentetik"), "B katmanı da körse çivi yoktur"


# ---------------------------------------------------------------------------
# T2 — DUMAN KAPISININ KÜMESİ KAPSANIYOR
# ---------------------------------------------------------------------------
_DUMAN_DESENI = re.compile(r"python -m compileall\s+([^;|&\n]+)")


def test_T2_duman_kapisinin_derledigi_kume_civinin_kapsaminda():
    metin = (REPO / "ops" / "ci_duman.sh").read_text(encoding="utf-8")
    eslesmeler = [m for m in _DUMAN_DESENI.finditer(metin)
                  if not metin[:m.start()].rsplit("\n", 1)[-1].lstrip().startswith("#")]
    assert len(eslesmeler) == 1, f"duman kapısında beklenmeyen compileall sayısı: {eslesmeler}"
    yollar = [p for p in eslesmeler[0].group(1).split() if not p.startswith("-")]
    assert yollar, "duman kapısı compileall'a hiç yol vermiyor"
    eksik = [p for p in yollar if p not in KOKLER]
    assert eksik == [], (
        f"duman kapısı {eksik} yollarını derliyor ama bu çivi taramıyor — CI'ın gördüğü bir "
        f"ihlali yerel suite GÖRMEZ. Çivinin kökleri: {KOKLER}")


# ---------------------------------------------------------------------------
# T3 — TABAN TEK KAYNAK
# ---------------------------------------------------------------------------
def test_T3_taban_pyproject_ci_ve_civide_AYNI():
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^requires-python\s*=\s*"[^0-9]*(\d+)\.(\d+)"', pyproject, re.M)
    assert m, "pyproject.toml requires-python okunamadı"
    beyan = (int(m.group(1)), int(m.group(2)))
    assert beyan == TABAN, f"pyproject tabanı {beyan}, çivi {TABAN} diyor"

    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    surum = f"{TABAN[0]}.{TABAN[1]}"
    assert f"--python {surum}" in ci, (
        f"CI iş akışı venv'i '{surum}' tabanına sabitlemiyor — kapı beyan edilen tabanda "
        "KOŞMAZSA compileall adımı başka bir Python'ın hükmünü verir")
    assert f"uv python install {surum}" in ci, "CI beyan edilen tabanı kurmuyor"
