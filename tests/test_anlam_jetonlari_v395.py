"""v395 — TSK-117 Görev 1: köprü. Pano (ui/src) rol jetonlarını YÜKLER ve dört anlam jetonu
tanımlıdır (TSK-117, 2026-09-03).

TSK-136 (2026-09-04, operatör kararı 10:10Z: "renk seçimleri ayrı bir tema olmalıydı; ana
renkleri geri al, yaptığını tema olarak yap") HEDEFİ DEĞİŞTİRDİ: dört anlam jetonu
(basari/uyari/kritik/bilgi) artık VARSAYILAN temada `--sev-N`/`--sky` ALIAS'ı DEĞİL — TSK-117
ÖNCESİ literal Tailwind hue'sudur (ölçülen göç dağılımı: amber/emerald/red/sky,
`ui/node_modules/tailwindcss/theme.css` oklch→sRGB, `_tailwind_renk_hex` v388'den ithal —
tek kaynak, sabit hex tablosu YAZILMADI). ALIAS hâli 'Meridian Palet' preset'inde yaşıyor
(`ui/src/styles/presets/meridian-palet.css`) — o preset seçilince `--basari: var(--sev-3)` vb.
CSS'i EZER."""
import json, pathlib, re
from meridian import config
from tests.test_hafiza_genel_bakis_v388 import _tailwind_renk_hex

UI = pathlib.Path(config.ROOT) / "ui" / "src"
TEMA = UI / "tema.css"
JETON = UI / "jetonlar.css"
PRESET = UI / "styles" / "presets" / "meridian-palet.css"
TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
ANLAM = ("basari", "uyari", "kritik", "bilgi")
# TSK-117'nin sev/sky alias'ı — preset'te YAŞAMAYA DEVAM EDER, VARSAYILANDA DEĞİL (TSK-136).
KAYNAK = {"basari": "sev-3", "uyari": "sev-2", "kritik": "sev-1", "bilgi": "sky"}
# TSK-136 VARSAYILAN literal hue ailesi + gündüz/gece tonu (göç dağılımından ölçülen).
AILE = {"basari": "emerald", "uyari": "amber", "kritik": "red", "bilgi": "sky"}
TON = {"gunduz": {"basari": 600, "uyari": 600, "kritik": 600, "bilgi": 700},
       "gece": {"basari": 400, "uyari": 400, "kritik": 400, "bilgi": 400}}
# -h/-t TÜREVLERİ: family-500 tonundan, HER İKİ temada AYNI (D1 kararı — Tailwind swatch
# numarası temaya göre değişmez). Alfa: %40 (-h) / %10 (-t), bilgi ailesi (sky) %25 (-h).
ALFA_H = {"basari": ".40", "uyari": ".40", "kritik": ".40", "bilgi": ".25"}
ALFA_T = ".10"


def _hex(ad: str, zemin: str) -> str:
    return _tailwind_renk_hex(f"--color-{AILE[ad]}-{TON[zemin][ad]}")


def _rgba500(ad: str, alfa: str) -> str:
    h = _tailwind_renk_hex(f"--color-{AILE[ad]}-500").lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alfa})"


def test_tema_jetonlar_css_i_import_eder():
    # DÜZELTME (TSK-117, 2026-09-03): brief taslağı `../jetonlar.css` (bir dizin yukarı)
    # bekliyordu; ölçüm `jetonlar.css`nin `tema.css` ile AYNI dizinde (`ui/src/`) olduğunu
    # gösterdi ve `../` yolu `vite build`i "Can't resolve '../jetonlar.css' in ui/src" ile
    # KIRDI (ölçüldü, mutasyonla doğrulandı). Tek doğru göreli yol `./jetonlar.css`.
    assert re.search(r'@import\s+"\./jetonlar\.css"', TEMA.read_text(encoding="utf-8")), \
        "pano rol jetonlarını yüklemiyor — Huni.tsx şerhindeki 'bağlı değil' hâli sürüyor"


def test_anlam_jetonlari_VARSAYILANDA_literal_tailwind_hex():
    """TSK-136 D1 — Ç1 ÖLÇÜMÜ: VARSAYILAN (tokens.json) dört anlam jetonu (+ -h/-t) artık
    `var(--sev-N)` ALIAS'I DEĞİL, ölçülen Tailwind hex'idir; üç alan (`$value`, `literal`,
    `cozulen-deger`) BİREBİR AYNI olmalı (v153'ün rol sözleşmesi, alias YOKKEN üçü zaten
    tek bir gerçeğe iner — ayrışırlarsa dosya aynı jeton hakkında iki gerçek söyler)."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    for zemin in ("gunduz", "gece"):
        anlam = d["rol"][zemin]["anlam"]
        for ad in ANLAM:
            hedef = _hex(ad, zemin)
            tk = anlam[ad]
            ext = tk["$extensions"]["org.meridian.css"]
            assert tk["$value"].lower() == hedef.lower(), \
                f"{zemin}.{ad}: $value {tk['$value']!r} ≠ ölçülen {hedef!r}"
            assert ext.get("literal", "").lower() == hedef.lower(), \
                f"{zemin}.{ad}: literal {ext.get('literal')!r} ≠ ölçülen {hedef!r} — hâlâ alias mı?"
            assert ext.get("cozulen-deger", "").lower() == hedef.lower(), \
                f"{zemin}.{ad}: cozulen-deger {ext.get('cozulen-deger')!r} ≠ ölçülen {hedef!r}"
            for ek, alfa in (("-h", ALFA_H[ad]), ("-t", ALFA_T)):
                hedef_ek = _rgba500(ad, alfa)
                tk_ek = anlam[ad + ek]
                ext_ek = tk_ek["$extensions"]["org.meridian.css"]
                assert tk_ek["$value"] == hedef_ek, \
                    f"{zemin}.{ad}{ek}: $value {tk_ek['$value']!r} ≠ ölçülen {hedef_ek!r}"
                assert ext_ek.get("literal") == hedef_ek, \
                    f"{zemin}.{ad}{ek}: literal {ext_ek.get('literal')!r} ≠ ölçülen {hedef_ek!r}"
                assert ext_ek.get("cozulen-deger") == hedef_ek, \
                    f"{zemin}.{ad}{ek}: cozulen-deger {ext_ek.get('cozulen-deger')!r} ≠ {hedef_ek!r}"


def test_meridian_palet_preset_anlam_ALIAS_tasiyor():
    """TSK-136 D2: eski TSK-117 alias davranışı (`--basari: var(--sev-3)` vb.) SİLİNMEDİ —
    'Meridian Palet' preset'ine taşındı. Preset seçilmeden bu blok hiç uygulanmaz
    (`:root[data-theme-preset="meridian-palet"]` özgüllüğü varsayılan `:root`u ezer)."""
    assert PRESET.is_file(), f"preset dosyası yok: {PRESET}"
    css = PRESET.read_text(encoding="utf-8")
    assert re.search(r'--basari:\s*var\(--sev-3\)', css), "preset --basari alias'ı yok"
    assert re.search(r'--uyari:\s*var\(--sev-2\)', css), "preset --uyari alias'ı yok"
    assert re.search(r'--kritik:\s*var\(--sev-1\)', css), "preset --kritik alias'ı yok"
    assert re.search(r'--bilgi:\s*var\(--sky\)', css), "preset --bilgi alias'ı yok"
    for ad, kaynak in KAYNAK.items():
        if ad == "bilgi":
            continue  # bilgi-h/-t rgba literaldir (sky kanallarından), alias zinciri taşımaz
        assert re.search(rf'--{ad}-h:\s*var\(--{kaynak}-h\)', css), f"preset --{ad}-h alias'ı yok"
        assert re.search(rf'--{ad}-t:\s*var\(--{kaynak}-t\)', css), f"preset --{ad}-t alias'ı yok"


def test_jetonlar_css_anlam_VARSAYILANDA_literal_hex_tasiyor():
    """Üretilen CSS (`ops/jeton_css_uret.py` çıktısı) `literal` alanını basar — VARSAYILAN
    artık alias değil, jetonlar.css'te `--basari: var(--sev-3)` DEĞİL ölçülen hex durmalı
    (TSK-136, 2026-09-04)."""
    css = JETON.read_text(encoding="utf-8")
    for ad in ANLAM:
        gunduz_hex = _hex(ad, "gunduz")
        gece_hex = _hex(ad, "gece")
        assert re.search(rf"--{ad}:\s*{re.escape(gunduz_hex)}\s*;", css, re.I), \
            f"jetonlar.css'te --{ad} (gündüz) {gunduz_hex} bulunamadı"
        assert re.search(rf"--{ad}:\s*{re.escape(gece_hex)}\s*;", css, re.I), \
            f"jetonlar.css'te --{ad} (gece) {gece_hex} bulunamadı"


def test_theme_inline_utility_eslemesi():
    tema = TEMA.read_text(encoding="utf-8")
    for ad in ANLAM:
        assert re.search(rf"--color-{ad}:\s*var\(--{ad}\)", tema), f"--color-{ad} eşlemesi yok (utility doğmaz)"
        assert re.search(rf"--color-{ad}-t:\s*var\(--{ad}-t\)", tema), f"--color-{ad}-t eşlemesi yok"


def test_gece_blogu_pano_dark_sinifini_da_kapsar():
    css = JETON.read_text(encoding="utf-8")
    assert re.search(r"^\[data-theme=\"dark\"\],\s*\.dark\s*\{", css, re.M), \
        "gece bloğu yalnız [data-theme=dark] — pano .dark sınıfıyla anahtarlıyor, gece jetonları panoda ölü kalır"


def test_bilgi_h_ve_t_TAILWIND_sky_500_KANALLARINDAN_turer():
    """TSK-136 (2026-09-04) — DÜZELTME: eski test `bilgi-h`/`bilgi-t`nin Meridian'ın KENDİ
    `--sky` jetonundan (tema.gunduz/gece.murekkep.sky, 'Dub' paleti) türediğini ölçüyordu; D1
    kararıyla VARSAYILAN `bilgi` artık Tailwind sky ailesine bağlı ve -h/-t de aynı ailenin
    -500 tonundan türer (family-500 kuralı, ALFA_H['bilgi']=.25) — iki temada da AYNI (temaya
    göre değişen yalnız `bilgi`nin KENDİSİ, 700 gündüz / 400 gece)."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    hedef_h, hedef_t = _rgba500("bilgi", ALFA_H["bilgi"]), _rgba500("bilgi", ALFA_T)
    for tema in ("gunduz", "gece"):
        assert d["rol"][tema]["anlam"]["bilgi-h"]["$value"] == hedef_h, \
            f"{tema}.bilgi-h {d['rol'][tema]['anlam']['bilgi-h']['$value']!r} ≠ {hedef_h!r}"
        assert d["rol"][tema]["anlam"]["bilgi-t"]["$value"] == hedef_t, \
            f"{tema}.bilgi-t {d['rol'][tema]['anlam']['bilgi-t']['$value']!r} ≠ {hedef_t!r}"
