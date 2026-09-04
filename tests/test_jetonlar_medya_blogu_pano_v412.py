"""v412 — jetonlar.css `@media (prefers-color-scheme: dark)` gece bloğu PANO'nun gündüz modunu EZMEMELİ.

Vaka (operatör, 2026-09-04 17:47Z, ekran görüntüsü): Mac koyu modda, pano GÜNDÜZ modunda — Hafıza kartları siyah.
Kök neden: pano temayı `data-theme="gunduz|gece"` (theme-utils) + `.dark` sınıfıyla damgalar; üretilmiş medya bloğunun
seçicisi `:root:not([data-theme='light'])` yalnız `light`i dışlıyordu → `gunduz` damgalı kökte OS koyuyken blok uygulanır
ve özgüllüğü (0,2,0) tema.css'in `:root` (0,1,0) bloğunu ezer. Düzeltme: blok `:not([data-theme='gunduz'])` da taşır —
pano kökü her zaman `gunduz`/`gece` damgalı olduğundan medya bloğu panoda HİÇ uygulanmaz (pano `.dark`ı kendi yönetir);
eski sayfalar (data-theme damgasız) eskisi gibi OS'e uyar. (TSK-134 devamı; 2026-09-04)"""
import pathlib
import re

from meridian import config

ROOT = pathlib.Path(config.ROOT)
JETON = ROOT / "ui" / "src" / "jetonlar.css"
URETICI = ROOT / "ops" / "jeton_css_uret.py"
PANO_TEMA = ROOT / "ui" / "src" / "lib" / "preferences" / "theme-utils.ts"


def _medya_blogu_secicileri(css: str) -> list[str]:
    m = re.search(r"@media \(prefers-color-scheme: dark\) \{(.*?)\n\}", css, re.S)
    assert m, "jetonlar.css'te @media (prefers-color-scheme: dark) bloğu yok — üretici değişti mi?"
    return re.findall(r"^\s*([^{\n]+)\{", m.group(1), re.M)


def test_pano_temayi_gunduz_gece_ile_damgaliyor():
    """Ön koşul (ölçüm): pano `data-theme` değerleri 'gunduz'/'gece' — 'light' DEĞİL. Değişirse bu çivi de gözden geçirilir."""
    src = PANO_TEMA.read_text(encoding="utf-8")
    assert re.search(r'setAttribute\("data-theme",\s*resolved === "dark" \? "gece" : "gunduz"\)', src), \
        "pano data-theme damgası gunduz/gece değil — v412'nin varsayımı değişti"


def test_medya_gece_blogu_pano_gunduz_kokunu_disliyor():
    secililer = _medya_blogu_secicileri(JETON.read_text(encoding="utf-8"))
    assert secililer, "medya bloğunda seçici yok"
    for s in secililer:
        assert ":not([data-theme='light'])" in s and ":not([data-theme='gunduz'])" in s, \
            f"medya gece bloğu pano gündüz kökünü ({s.strip()!r}) dışlamıyor — OS koyuyken gündüz panosu kararır"


def test_uretici_ile_ayni_secici():
    """Tek kaynak: seçici üreticide tanımlı, jetonlar.css üretilmiş — ikisi aynı."""
    u = URETICI.read_text(encoding="utf-8")
    assert ":root:not([data-theme='light']):not([data-theme='gunduz'])" in u, "üretici seçiciyi taşımıyor"
