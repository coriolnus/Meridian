"""v400 — TSK-117 S4: rol çiftleri deuteranopi/protanopi simülasyonunda ışıklılıkla ayrılıyor mu.
Simülasyon: Viénot-Brettel-Mollon (1999) LMS projeksiyonu (RGB→LMS Hunt-Pointer-Estevez, D65).
Eşik ön-kayıt: kontrast oranı ≥ 1,4:1 (WCAG bağıl ışıklılık). (TSK-117, 2026-09-03)

TSK-136 (2026-09-04, operatör kararı 10:10Z) HEDEFİ DEĞİŞTİRDİ: gece `yon-eksi`nin K-0
düzeltmesi (#f98080→#f6966f) VARSAYILAN tokens.json'dan preset'e taşındı. Bu xfail testin
ANLAMI hâlâ AYNI soru: düzeltme SONRASI hâlâ eşiğin altında mı — bu yüzden `_jeton` gece
yon-eksi'yi artık preset CSS'inden okur (`ui/src/styles/presets/meridian-palet.css`), diğer
jetonlar (sev-1/2/3, yon-arti — palet turundan ETKİLENMEDİ) tokens.json'dan gelmeye devam
eder. VARSAYILANIN (preset UYGULANMADAN, orijinal #f98080) ölçümü PYTEST ÇİVİSİ DEĞİL — rapora
elle işlendi (`.superpowers/sdd/2026-09-04-tsk136/report.md`), çünkü aynı renk-körlüğü
çakışması hem eski hem yeni değerde ölçülüyor ve ikinci bir xfail sessiz gürültü olurdu."""
import json, pathlib, re

import pytest
from meridian import config

TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
PRESET = pathlib.Path(config.ROOT) / "ui" / "src" / "styles" / "presets" / "meridian-palet.css"
ESIK = 1.4
CIFTLER = [("siddet", "sev-2", "siddet", "sev-3"), ("yon", "yon-eksi", "yon", "yon-arti"), ("siddet", "sev-1", "siddet", "sev-2")]


# sRGB → linear
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(hexstr):
    return [_lin(int(hexstr[i:i + 2], 16)) for i in (1, 3, 5)]


# RGB→LMS (Hunt-Pointer-Estevez, D65) ve deuteranopi/protanopi projeksiyonları (Viénot 1999)
RGB2LMS = [[0.31399022, 0.63951294, 0.04649755], [0.15537241, 0.75789446, 0.08670142], [0.01775239, 0.10944209, 0.87256922]]
LMS2RGB = [[5.47221206, -4.6419601, 0.16963708], [-1.1252419, 2.29317094, -0.1678952], [0.02980165, -0.19318073, 1.16364789]]
DEUTAN = [[1, 0, 0], [0.9513092, 0, 0.04866992], [0, 0, 1]]
PROTAN = [[0, 1.05118294, -0.05116099], [0, 1, 0], [0, 0, 1]]


def _mm(M, v):
    return [sum(M[i][j] * v[j] for j in range(3)) for i in range(3)]


def _sim(rgb, P):
    return _mm(LMS2RGB, _mm(P, _mm(RGB2LMS, rgb)))


def _Y(rgb):
    # gamut kırpması BEYANLI: simülasyon projeksiyonu [0,1] dışına taşabilir (Viénot matrisleri
    # tam-gamut korumaz), WCAG bağıl ışıklılık [0,1] varsayar — clamp burada.
    r, g, b = (max(0, min(1, x)) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _kontrast(a, b):
    ya, yb = _Y(a), _Y(b)
    hi, lo = max(ya, yb), min(ya, yb)
    return (hi + 0.05) / (lo + 0.05)


def _jeton(tema, grup, ad):
    # tokens.json $value İKİ biçimde ölçüldü: rol.*.siddet/yon düz "#hex" dizgesi; tema.* (ve
    # bazı başka gruplar) {"colorSpace":"srgb","components":[...],"alpha":1,"hex":"#..."} sözlüğü
    # (bkz. /tema/gunduz/zemin/bg). Bu ölçüm yalnız rol.*.siddet/yon ana jetonlarını okur (düz
    # dizge) ama yardımcı ikisini de destekler — uydurma yok, ölçülen biçim ne ise o okunur.
    if tema == "gece" and grup == "yon" and ad == "yon-eksi":
        # TSK-136, 2026-09-04: K-0 düzeltmesi VARSAYILANDA değil — preset'ten OKU.
        css = PRESET.read_text(encoding="utf-8")
        m = re.search(r"--yon-eksi:\s*(#[0-9a-fA-F]{6})", css)
        assert m, f"preset'te --yon-eksi bulunamadı: {PRESET}"
        return m.group(1)
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    v = d["rol"][tema][grup][ad]["$value"]
    return v["hex"] if isinstance(v, dict) else v


@pytest.mark.xfail(
    strict=True,
    reason="S4 ÖLÇÜLDÜ 2026-09-04 (TSK-117 G8): 12 kontrastın 9'u ön-kayıtlı 1,4 eşiğinin altında (min 1,0076 gece "
           "sev-2↔sev-3 protan). Eşik DEĞİŞMEZ; düzeltme rol jetonlarının IŞIKLILIĞIDIR (hue değil) ve altı çekirdek "
           "jetonun ekrandaki hâlini değiştirir → operatör görsel kararı [TSK-133]. strict=True: jetonlar düzelince bu "
           "test 'beklenmedik geçti' ile KIRMIZI olur, o gün xfail kalkar — sessiz yeşil yok.",
)
def test_rol_ciftleri_renk_korlugunde_isiklilikla_ayrilir():
    ihlal = []
    for tema in ("gunduz", "gece"):
        for g1, a1, g2, a2 in CIFTLER:
            x, y = _rgb(_jeton(tema, g1, a1)), _rgb(_jeton(tema, g2, a2))
            for adi, P in (("deutan", DEUTAN), ("protan", PROTAN)):
                k = _kontrast(_sim(x, P), _sim(y, P))
                if k < ESIK:
                    ihlal.append((tema, a1, a2, adi, round(k, 2)))
    assert not ihlal, f"renk körlüğünde ayrışmayan rol çiftleri (kontrast<{ESIK}): {ihlal}"
