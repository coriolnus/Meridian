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
    """TSK-117 G1 r2, 2026-09-04 — DÜZELTME: eski sürüm DTCG `{a.b.c}` alias dizgesi
    bekliyordu (`v == "{rol.gunduz...}" or v.startswith("{")`); v153'ün rol sözleşmesi
    BAŞKA bir gramer ister — `$value` zincirin UCUNDAKİ çözülmüş değer (hex/rgba), takma
    ad CSS tarafında `$extensions.org.meridian.css.literal`de bir `var()` ifadesi olarak
    durur ve `cozulen-deger` o zincirin ucunu AYRICA taşır (v153::test_ROL_alias_zinciri_
    TEK_gercek_soyler). Gevşek `or v.startswith("{")` dalı KALKTI — Rol-1 notu: o dal her
    string alias'ı (doğru gramerdekini de, yanlış gramerdekini de) sessizce geçirdiği için
    ölçmüyordu, yalnız "bir şey yazılmış" diyordu.

    Bu test artık ÜÇ şeyi birden ölçer, iki zeminde de: literal `var(--kaynak)` zincirini
    doğru jetona bağlıyor mu, `$value` kaynağın kendi `$value`'suyla birebir mi, ve
    `cozulen-deger` de aynı değere mi çözülüyor mu — üçü ayrışırsa dosya aynı jeton
    hakkında iki farklı gerçek söyler (v153'ün kovaladığı sınıf). `bilgi-h`/`bilgi-t`
    kapsam DIŞI: onlar alias değil, sky'ın RGB kanallarından türetilmiş rgba literalidir
    ve o ayrışma zaten `test_bilgi_h_ve_t_sky_kanallarindan_AYRISMIYOR` tarafından ölçülüyor."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    for zemin in ("gunduz", "gece"):
        anlam = d["rol"][zemin].get("anlam") or {}
        for ad in ANLAM:
            kaynak = KAYNAK[ad]
            if ad == "bilgi":
                hedef = d["tema"][zemin]["murekkep"]["sky"]["$value"]["hex"]
            else:
                hedef = d["rol"][zemin]["siddet"][kaynak]["$value"]
            tk = anlam[ad]
            ext = tk["$extensions"]["org.meridian.css"]
            assert ext.get("literal") == f"var(--{kaynak})", \
                f"{zemin}.{ad}: literal {ext.get('literal')!r} ≠ var(--{kaynak}) — zincir kopuk"
            assert tk["$value"] == hedef, \
                f"{zemin}.{ad}: $value {tk['$value']!r} ≠ kaynağın $value'su {hedef!r}"
            assert ext.get("cozulen-deger") == hedef, \
                f"{zemin}.{ad}: cozulen-deger {ext.get('cozulen-deger')!r} ≠ kaynağın $value'su {hedef!r}"
            if ad == "bilgi":
                continue  # bilgi-h/-t rgba literaldir, alias zinciri taşımaz (yukarı bkz.)
            for ek in ("-h", "-t"):
                kaynak_ek = kaynak + ek
                hedef_ek = d["rol"][zemin]["siddet"][kaynak_ek]["$value"]
                tk_ek = anlam[ad + ek]
                ext_ek = tk_ek["$extensions"]["org.meridian.css"]
                assert ext_ek.get("literal") == f"var(--{kaynak_ek})", \
                    f"{zemin}.{ad}{ek}: literal {ext_ek.get('literal')!r} ≠ var(--{kaynak_ek})"
                assert tk_ek["$value"] == hedef_ek, \
                    f"{zemin}.{ad}{ek}: $value {tk_ek['$value']!r} ≠ kaynağın $value'su {hedef_ek!r}"
                assert ext_ek.get("cozulen-deger") == hedef_ek, \
                    f"{zemin}.{ad}{ek}: cozulen-deger {ext_ek.get('cozulen-deger')!r} ≠ {hedef_ek!r}"

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
