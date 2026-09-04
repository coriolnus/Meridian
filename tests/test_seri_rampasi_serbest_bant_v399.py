"""v399 — TSK-117 K-4 (S1=A′, S2): seri rampası 6–10 rol bantları DIŞINDA; huni jetonları seri
değerlerinden TÜRER (kopya değil); Tailwind palet hex'leri testin içinde çözülür (tema.css
var(--color-X-N) → tailwind palet dosyası ölçülerek, `_tailwind_renk_hex`). (TSK-117, 2026-09-04)

NUMARA ÇAKIŞMASI TARANDI (2026-09-04): `ls tests | grep v399` BOŞ döndü.

HUNİ YOLU ÖLÇÜLDÜ, BREF'İN TASLAĞI DEĞİL: `grep -n '"huni-1"' meridian/web/tokens.json` iki kayıt
verdi (`tema/gunduz/murekkep/huni-1`, `tema/gece/murekkep/huni-3`) — brief'in taslak yolu
(`d["rol"]["gunduz"]["huni"]`) bu depoda YOK. Aşağıdaki testler ölçülen gerçek yolu kullanır.
`$value` bir dize değil bir sözlük (`{"hex": "#…", "components": […], …}`) — karşılaştırma
`$value["hex"]` üzerinden.

DÜZELTME TURU 1 (TSK-117 G7 r1, 2026-09-04) — İKİ DÜZELTME:
1. HUNİ EŞLEMESİ (1,6),(2,7),(3,8) → (1,6),(2,8),(3,9): ilk yazım "huni sırayla ilk üç seri"
   diye VARSAYDI. Ölçülen gerçek `ui/src/pano/yuzeyler/kanban/Huni.tsx::RENK_ILK/ORTA/VARIS`
   TAM OLARAK `var(--color-seri-6/8/9)` okuyor (huni-2 seri-7 DEĞİL) — huni tokens.json kaydı bu
   GERÇEK UI'yi tarif etmeli, keyfi bir "ilk üç" kuralını değil (tek-kaynak yasası: iki
   tanım aynı gerçeği İKİ FARKLI biçimde söylerse biri yanlıştır).
2. TEK KAYNAK — `BANTLAR`/`_bantta` SİLİNDİ, v388'İN `ROL_BANTLARI`/`_bantta`SI İTHAL EDİLDİ:
   iki dosya aynı bant tablosunun ayrı kopyalarını taşıyordu (v399 ASCII adlarla `(336,366)`
   sarmalı gösterimi, v388 Türkçe adlarla `(336.0,6.0)` `alt>ust` gösterimi) — FONKSİYONEL
   OLARAK eşdeğerdi ama biri değişip öteki unutulursa sessizce ayrışırdı. v388 SSoT: `_bantta`
   ORADA yaşıyor (`_jeton_hue`/pozitif kontrol de onu kullanıyor), v399 sadece ithal eder.
"""
import colorsys
import json
import pathlib
import re

from meridian import config
from tests.test_hafiza_genel_bakis_v388 import ROL_BANTLARI, _bantta, _tailwind_renk_hex

ROOT = pathlib.Path(config.ROOT)
TEMA = ROOT / "ui" / "src" / "tema.css"
TOKENS = ROOT / "meridian" / "web" / "tokens.json"

assert ROL_BANTLARI, "v388 ROL_BANTLARI boş — ithalat bayat mı ölçüldü mü?"  # kullanım kanıtı


def _hue(hexstr: str) -> float:
    r, g, b = (int(hexstr[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    return h * 360


def _tailwind_hex(ad: str) -> str:
    """`--color-teal-600` → hex: `node_modules/tailwindcss/theme.css` içinden ÖLÇÜLEREK
    (v388'in `_tailwind_renk_hex` yardımcısı — oklch→sRGB dönüşümü orada, tek kaynak)."""
    return _tailwind_renk_hex(ad)


def _seri(tema_blok: str) -> dict[int, str]:
    css = TEMA.read_text(encoding="utf-8")
    m = re.search(rf"{tema_blok}\s*\{{([^}}]*)\}}", css, re.S)
    assert m, f"{tema_blok} bloğu tema.css'te bulunamadı — desen bayat"
    blok = m.group(1)
    return {
        int(m2.group(1)): m2.group(2)
        for m2 in re.finditer(r"--seri-(\d+):\s*var\((--color-[a-z]+-\d+)\)", blok)
    }


def test_taranan_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki `_seri`/tokens okuması sessizce boş/hatalı döner."""
    for p in (TEMA, TOKENS):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"


def test_seri_6_10_rol_bantlarinda_DEGIL():
    for blok in (":root", r"\.dark"):
        seri = _seri(blok)
        assert seri, f"{blok} bloğunda hiç --seri-N okunamadı — desen bayat"
        for k, tw in seri.items():
            if k < 6:
                continue
            h = _hue(_tailwind_hex(tw))
            assert _bantta(h) is None, f"{blok} seri-{k} ({tw}, {h:.1f}°) rol bandında: {_bantta(h)}"


def test_huni_jetonlari_seri_degerlerinden_turer():
    """Eşleme (1,6),(2,8),(3,9) — `ui/src/pano/yuzeyler/kanban/Huni.tsx::RENK_ILK/ORTA/VARIS`
    (ÖLÇÜLEN gerçek UI, `grep -n "RENK_ILK\\|RENK_ORTA\\|RENK_VARIS" .../Huni.tsx`) ile BİREBİR;
    "ilk üç seri" gibi keyfi bir sıra DEĞİL (düzeltme turu 1, TSK-117 G7 r1, 2026-09-04)."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    seri_gunduz = _seri(":root")
    seri_gece = _seri(r"\.dark")
    for tema_adi, seri in (("gunduz", seri_gunduz), ("gece", seri_gece)):
        huni = d["tema"][tema_adi]["murekkep"]
        for i, k in ((1, 6), (2, 8), (3, 9)):
            beklenen = _tailwind_hex(seri[k]).lower()
            gercek = huni[f"huni-{i}"]["$value"]["hex"].lower()
            assert gercek == beklenen, (
                f"{tema_adi} huni-{i} ({gercek}) ≠ seri-{k} ({beklenen}) — kopya ayrıştı"
            )
            assert "seri-" in huni[f"huni-{i}"].get("$description", ""), (
                f"{tema_adi} huni-{i} beyanı 'seri-N' türetimini söylemeli"
            )
            # `literal` üretim önceliklidir (`ops/jeton_css_uret.py::uret`): `$value` güncellenip
            # `literal` bayat kalırsa CSS üretimi ESKİ hex'i basar — ikisi BİRLİKTE ölçülür.
            literal = (
                huni[f"huni-{i}"].get("$extensions", {}).get("org.meridian.css", {}).get("literal")
            )
            assert literal is not None and literal.lower() == beklenen, (
                f"{tema_adi} huni-{i} $extensions.literal ({literal}) ≠ $value.hex ({beklenen}) — "
                "üretici `literal`i önceliklendirir, ikisi ayrışırsa CSS eski değeri basar"
            )


def test_dugum_stili_istisnasi_KAPANDI():
    from tests.test_hafiza_genel_bakis_v388 import ISTISNALAR

    assert ISTISNALAR == {}, "palet turu bitti — DUGUM_STILI istisnası ölü muafiyet olmamalı"
