"""v412 — jetonlar.css `@media (prefers-color-scheme: dark)` gece bloğu YALNIZ damgasız kökü hedefler.

Vaka (operatör, 2026-09-04 17:47Z, ekran görüntüsü): Mac koyu modda, pano GÜNDÜZ modunda — Hafıza kartları siyah.
İlk kök neden: pano temayı `data-theme="gunduz|gece"` (theme-utils) + `.dark` sınıfıyla damgalar; üretilmiş medya
bloğunun seçicisi `:root:not([data-theme='light'])` yalnız `light`i dışlıyordu → `gunduz` damgalı kökte OS koyuyken
blok uygulanır ve özgüllüğü (0,2,0) tema.css'in `:root` (0,1,0) bloğunu ezer. İlk düzeltme `:not([data-theme='gunduz'])`
de ekledi — ama değer-bazlı dışlama listesi sözlük büyüdükçe yeniden delinir: 2026-09-04 21:0xZ ikinci ölçüm `gece`
kökünün AÇIKTA kaldığını gösterdi (gece + OS-koyu'da pano kartı jetonlar #262626 çıkıyor, tema.css `.dark` oklch(0.205)
DEĞİL). ARTIK (D1, Rol-1 2026-09-04): seçici NİTELİK-varlığı dışlar — `:root:not([data-theme])`. OS tercihi YALNIZ
damgasız köke uygulanır; damgalı her kök (gunduz|gece|light|dark|…) temayı KENDİ yönetir — pano geceyi `.dark`
sınıfıyla (jetonlar `[data-theme='dark'], .dark` bloğu ÖNCE, tema.css'in KENDİ `.dark` bloğu SONRA yüklenir → tema.css
kazanır, v407 hükmüyle tutarlı, bkz. test_DARK_SIRASI aşağıda). Eski sayfalar (data-theme damgasız) eskisi gibi OS'e
uyar. (TSK-134 devamı; 2026-09-04)"""
import pathlib
import re

from meridian import config

ROOT = pathlib.Path(config.ROOT)
JETON = ROOT / "ui" / "src" / "jetonlar.css"
TEMA = ROOT / "ui" / "src" / "tema.css"
URETICI = ROOT / "ops" / "jeton_css_uret.py"
PANO_TEMA = ROOT / "ui" / "src" / "lib" / "preferences" / "theme-utils.ts"


def _medya_blogu_secicileri(css: str) -> list[str]:
    m = re.search(r"@media \(prefers-color-scheme: dark\) \{(.*?)\n\}", css, re.S)
    assert m, "jetonlar.css'te @media (prefers-color-scheme: dark) bloğu yok — üretici değişti mi?"
    return re.findall(r"^\s*([^{\n]+)\{", m.group(1), re.M)


def _secici_esler_mi(secici: str, data_theme: str | None) -> bool:
    """SEÇİCİ-ANLAM YARDIMCISI (10 satır). Bir `:root` seçicisinin, verilen `data-theme` değerine
    (None = nitelik YOK) sahip bir kökü eşleyip eşlemediğini semantik olarak değerlendirir — bu
    depoda görülen iki `:not([data-theme...])` biçimini de anlar: nitelik-varlığı (`[data-theme]`,
    değersiz) ve değer-bazlı (`[data-theme='X']`). Değer listesine BAKMADAN çalışır."""
    if not secici.strip().startswith(":root"):
        return False
    for m in re.finditer(r":not\(\[data-theme(?:='([^']*)')?\]\)", secici):
        deger = m.group(1)
        if deger is None:  # nitelik-varlığı dışlaması: HERHANGİ damgalı kök elenir
            if data_theme is not None:
                return False
        elif data_theme == deger:  # değer-bazlı dışlama: yalnız O değer elenir
            return False
    return True


def test_secici_esler_mi_POZITIF_KONTROL():
    """Yardımcının kendisi ölçülüyor (nitelik-varlığı ve değer-bazlı biçim ayrı ayrı) — yanlış
    yazılmış bir yardımcı aşağıdaki testleri sessizce yanlış sebeple yeşil/kırmızı yapardı."""
    assert _secici_esler_mi(":root:not([data-theme])", None) is True
    assert _secici_esler_mi(":root:not([data-theme])", "gece") is False
    assert _secici_esler_mi(":root:not([data-theme='light'])", "light") is False
    assert _secici_esler_mi(":root:not([data-theme='light'])", "gece") is True  # eski (bayat) biçim: gece'yi dışlamaz


def test_pano_temayi_gunduz_gece_ile_damgaliyor():
    """Ön koşul (ölçüm): pano `data-theme` değerleri 'gunduz'/'gece' — 'light' DEĞİL. Değişirse bu çivi de gözden geçirilir."""
    src = PANO_TEMA.read_text(encoding="utf-8")
    assert re.search(r'setAttribute\("data-theme",\s*resolved === "dark" \? "gece" : "gunduz"\)', src), \
        "pano data-theme damgası gunduz/gece değil — v412'nin varsayımı değişti"


def test_medya_gece_blogu_pano_gunduz_kokunu_disliyor():
    """ARTIK (D1, 2026-09-04): iddia 'DAMGALI KÖKÜ dışlıyor' — değer listesine (light/gunduz/…)
    bakmadan, nitelik-varlığıyla. Eskiden yalnız `gunduz`+`light` dışlanıyordu; `gece` damgalı
    pano kökü (OS-koyu'da) AÇIKTA kalıyordu — bu test artık dört bilinen damganın HİÇBİRİNİN
    (gunduz/gece/light/dark) medya bloğuyla eşleşmediğini, damgasız kökün eşleştiğini doğrular."""
    secililer = _medya_blogu_secicileri(JETON.read_text(encoding="utf-8"))
    assert secililer, "medya bloğunda seçici yok"
    for s in secililer:
        assert s.strip().startswith(":root:not([data-theme])"), (
            f"medya gece bloğu ({s.strip()!r}) nitelik-varlığı dışlaması kullanmıyor — "
            "değer-bazlı liste sözlük büyüdükçe yeniden delinir")
        for damga in ("gunduz", "gece", "light", "dark"):
            assert not _secici_esler_mi(s, damga), (
                f"medya gece bloğu {damga!r} damgalı kökü DIŞLAMIYOR — OS koyuyken o kök "
                "jetonlar.css'in gece bloğunu (tema.css'in üstüne) alır")
        assert _secici_esler_mi(s, None), (
            "medya gece bloğu damgasız kökü eşlemiyor — eski sayfalar (index/landing/…) OS'e uymaz olur")


def test_uretici_ile_ayni_secici():
    """Tek kaynak: seçici üreticide tanımlı, jetonlar.css üretilmiş — ikisi aynı."""
    u = URETICI.read_text(encoding="utf-8")
    assert ":root:not([data-theme])" in u, "üretici seçiciyi taşımıyor"


def test_DARK_SIRASI_jetonlar_ONCE_tema_govde_SONRA():
    """(D2d, TSK-134 2026-09-04) v407'nin `:root` için ölçtüğünü `.dark` için ölçer: tema.css'te
    `@import "./jetonlar.css"` satırı, tema.css'in KENDİ shadcn `.dark` gövdesinden (`--card`in
    GERÇEK gece tanımı, `--background` ile başlar) metinde ÖNCE gelmeli. Pano temayı `.dark`
    sınıfıyla geçtiğinde jetonlar `[data-theme='dark'], .dark` bloğu ÖNCE, tema.css'in KENDİ
    `.dark` bloğu SONRA yüklenir ve aynı özgüllükte (0,1,0) SON bildirim kazanır — tema.css'in
    gece `--card`i (oklch(0.205)) jetonlar'ın gece `--card`ini (#262626) ezer. Sıra tersine
    dönerse pano gece kartı jetonlar'ın eski değerine düşer (bu turun kök-neden vakası)."""
    css = TEMA.read_text(encoding="utf-8")
    import_idx = css.index('@import "./jetonlar.css"')
    govde_idx = css.index("\n.dark {\n  --background:")
    assert import_idx < govde_idx, (
        "tema.css'in shadcn .dark gövdesi import'tan ÖNCE — cascade sırası ters, "
        "pano gece kartı jetonlar.css'in eski değerine düşer")
