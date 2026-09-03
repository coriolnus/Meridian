"""v395 — TSK-117 Görev 1: köprü. Pano (ui/src) rol jetonlarını YÜKLER ve dört anlam jetonu
tek kaynaktan (tokens.json alias) türer. (TSK-117, 2026-09-03)"""
import json, pathlib, re
from meridian import config

UI = pathlib.Path(config.ROOT) / "ui" / "src"
TEMA = UI / "tema.css"
JETON = UI / "jetonlar.css"
TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
ANLAM = ("basari", "uyari", "kritik", "bilgi")
KAYNAK = {"basari": "sev-3", "uyari": "sev-2", "kritik": "sev-1", "bilgi": "sky"}

def test_tema_jetonlar_css_i_import_eder():
    # DÜZELTME (TSK-117, 2026-09-03): brief taslağı `../jetonlar.css` (bir dizin yukarı)
    # bekliyordu; ölçüm `jetonlar.css`nin `tema.css` ile AYNI dizinde (`ui/src/`) olduğunu
    # gösterdi ve `../` yolu `vite build`i "Can't resolve '../jetonlar.css' in ui/src" ile
    # KIRDI (ölçüldü, mutasyonla doğrulandı). Tek doğru göreli yol `./jetonlar.css`.
    assert re.search(r'@import\s+"\./jetonlar\.css"', TEMA.read_text(encoding="utf-8")), \
        "pano rol jetonlarını yüklemiyor — Huni.tsx şerhindeki 'bağlı değil' hâli sürüyor"

def test_anlam_jetonlari_tokens_jsonda_ALIAS_olarak_var():
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    anlam = d["rol"]["gunduz"].get("anlam") or {}
    for ad in ANLAM:
        v = anlam[ad]["$value"]
        assert v == "{rol.gunduz.%s.%s}" % ("siddet" if ad != "bilgi" else "renk", KAYNAK[ad]) or v.startswith("{"), \
            f"{ad}: değer alias DEĞİL ({v}) — kopya hue tek-kaynak yasasını kırar"

def test_jetonlar_css_anlam_degiskenlerini_var_ile_bagliyor():
    css = JETON.read_text(encoding="utf-8")
    for ad in ANLAM:
        m = re.search(rf"--{ad}:\s*var\(--([a-z0-9-]+)\)", css)
        assert m and m.group(1) == KAYNAK[ad], f"--{ad} → var(--{KAYNAK[ad]}) bekleniyordu"

def test_theme_inline_utility_eslemesi():
    tema = TEMA.read_text(encoding="utf-8")
    for ad in ANLAM:
        assert re.search(rf"--color-{ad}:\s*var\(--{ad}\)", tema), f"--color-{ad} eşlemesi yok (utility doğmaz)"
        assert re.search(rf"--color-{ad}-t:\s*var\(--{ad}-t\)", tema), f"--color-{ad}-t eşlemesi yok"

def test_gece_blogu_pano_dark_sinifini_da_kapsar():
    css = JETON.read_text(encoding="utf-8")
    assert re.search(r"^\[data-theme=\"dark\"\],\s*\.dark\s*\{", css, re.M), \
        "gece bloğu yalnız [data-theme=dark] — pano .dark sınıfıyla anahtarlıyor, gece jetonları panoda ölü kalır"


def test_bilgi_h_ve_t_sky_kanallarindan_AYRISMIYOR():
    """İnceleme bulgusu #2 (TSK-117 G1, 2026-09-03): `bilgi-h`/`bilgi-t` alias değil, sky hex'inin
    RGB kanallarını taşıyan literal rgba (sev-*-h/-t emsali). `--sky` değişirse ikisi sessizce ayrışır —
    bu çivi iki temada da kanalları hex'ten türetip kıyaslar (tek-kaynak yasası, kopya kaçınılmaz olduğunda
    ayrışma çivisi)."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    for tema in ("gunduz", "gece"):
        hexi = d["tema"][tema]["murekkep"]["sky"]["$value"]["hex"].lstrip("#")
        rgb = tuple(int(hexi[i:i + 2], 16) for i in (0, 2, 4))
        for ek, alfa in (("bilgi-h", ".35"), ("bilgi-t", ".10")):
            v = d["rol"][tema]["anlam"][ek]["$value"]
            m = re.fullmatch(r"rgba\((\d+),(\d+),(\d+),(\.\d+)\)", v)
            assert m, f"{tema}.{ek}: beklenen rgba(r,g,b,a) literal, bulunan {v!r}"
            assert tuple(int(m.group(i)) for i in (1, 2, 3)) == rgb, \
                f"{tema}.{ek}: kanallar {m.group(1, 2, 3)} ≠ sky {hexi} → {rgb} (sky değişti, türev güncellenmedi)"
            assert m.group(4) == alfa, f"{tema}.{ek}: alfa {m.group(4)} ≠ emsal {alfa}"
