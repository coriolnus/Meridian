"""v396 — TSK-117 K-0: gece rol jetonları arasında hue çakışması yok (yön-eksi 0° ↔ kritik 1° vakası).
Hue hesabı testin İÇİNDE (colorsys) — sabit tablo yazılmaz. (TSK-117, 2026-09-03)"""
import colorsys, json, pathlib, re
from meridian import config

TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
MIN_FARK = 8.0   # derece; spec §4 K-0

def _hue(hexstr):
    r, g, b = (int(hexstr[i:i+2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l

def _rol_kromatik(tema):
    d = json.loads(TOKENS.read_text(encoding="utf-8"))["rol"][tema]
    out = {}
    for grup in ("siddet", "yon", "mod", "nav"):
        for ad, j in d.get(grup, {}).items():
            if ad.startswith("$"): continue
            v = j.get("$value") if isinstance(j, dict) else None
            if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
                h, s, l = _hue(v)
                if s >= 0.12: out[f"{grup}/{ad}"] = h
    return out

def _dairesel(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

def test_gece_yon_eksi_ile_kritik_ayri_hue():
    h = _rol_kromatik("gece")
    assert _dairesel(h["yon/yon-eksi"], h["siddet/sev-1"]) >= MIN_FARK, \
        f"gece yön-eksi {h['yon/yon-eksi']:.0f}° ≈ kritik {h['siddet/sev-1']:.0f}° — negatif K/Z ile P1 alarmı aynı renk"

def test_gece_yon_eksi_gunduz_hue_ailesinde():
    g = _rol_kromatik("gunduz"); n = _rol_kromatik("gece")
    assert _dairesel(g["yon/yon-eksi"], n["yon/yon-eksi"]) <= 6.0, "gece yön-eksi gündüzle aynı hue ailesinde olmalı (kimlik hue, ışıklılık temayla)"

def test_gece_rol_ciftleri_farkli_gruplar_arasi_min_fark():
    h = _rol_kromatik("gece")
    ihlal = []
    adlar = sorted(h)
    for i, a in enumerate(adlar):
        for b in adlar[i+1:]:
            if a.split("/")[0] != b.split("/")[0] and _dairesel(h[a], h[b]) < MIN_FARK:
                ihlal.append((a, b, round(h[a]), round(h[b])))
    # BEYANLI istisnalar — spec §2 "Rezerve bantlar" tablosunun "sahibi" sütunu iki çifti aynı banda
    # koyar: "UYARI + YÖN-EKSİ" satırı (sev-2/yon-eksi; not sütunu "bilinçli, ışıklılıkla ayrılır" der,
    # brief'te AYNEN) ve "BAŞARI + YÖN-ARTI" satırı (sev-3/yon-arti; not sütunu emerald hizasını anlatır,
    # ışıklılık farkı ÖLÇÜLDÜ: gece l=0,29 / 0,58) — ikincisi K-0'dan BAĞIMSIZ ÖN-VAROLAN bir çakışma
    # (gündüz+gece eşit ~2.7°), bu turda dokunulmadı; brief'in test kodunda eksikti, istisna olarak
    # eklendi (TSK-117, 2026-09-03, task-2-report.md'de not — Rol-1 KABUL; inceleme KÜÇÜK-1 düzeltmesi).
    BEYANLI_AYNI_BANT = [{"sev-2", "yon-eksi"}, {"sev-3", "yon-arti"}]
    ihlal = [x for x in ihlal if {x[0].split("/")[1], x[1].split("/")[1]} not in BEYANLI_AYNI_BANT]
    assert not ihlal, f"gece rol hue çakışmaları: {ihlal}"

def test_yon_eksi_turevleri_ve_yon_arti_zemin_ana_hexten_ayrismiyor():
    """Düzeltme turu 1 (TSK-117, 2026-09-04): Rol-1 ruling (B) — gece `yon-eksi-zemin` ESKİ kırmızının
    kanallarını taşıyordu (K-0 sınıfının kendisi: matris hücresi gece hâlâ kritikle aynı hue'daydı).
    v395'teki `bilgi-h/-t` deseni: -h/-t/-zemin alias DEĞİL, ana hex'in RGB kanallarını taşıyan literal
    rgba — ana hex değişince türevler sessizce ayrışabilir. Bu çivi iki temada da kanalları ana hex'ten
    türetip kıyaslar; alfa emsalleri ölçülmüş sınır (.35/.10/.07/.08), dokunulmaz."""
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    for tema in ("gunduz", "gece"):
        yon = d["rol"][tema]["yon"]
        eksi_hex = yon["yon-eksi"]["$value"].lstrip("#")
        eksi_rgb = tuple(int(eksi_hex[i:i + 2], 16) for i in (0, 2, 4))
        for ek, alfa in (("yon-eksi-h", ".35"), ("yon-eksi-t", ".10"), ("yon-eksi-zemin", ".07")):
            v = yon[ek]["$value"]
            m = re.fullmatch(r"rgba\((\d+),(\d+),(\d+),(\.\d+)\)", v)
            assert m, f"{tema}.{ek}: beklenen rgba(r,g,b,a) literal, bulunan {v!r}"
            assert tuple(int(m.group(i)) for i in (1, 2, 3)) == eksi_rgb, \
                f"{tema}.{ek}: kanallar {m.group(1, 2, 3)} ≠ yon-eksi {eksi_hex} → {eksi_rgb} (ana hex değişti, türev güncellenmedi)"
            assert m.group(4) == alfa, f"{tema}.{ek}: alfa {m.group(4)} ≠ emsal {alfa}"

        arti_hex = yon["yon-arti"]["$value"].lstrip("#")
        arti_rgb = tuple(int(arti_hex[i:i + 2], 16) for i in (0, 2, 4))
        v = yon["yon-arti-zemin"]["$value"]
        m = re.fullmatch(r"rgba\((\d+),(\d+),(\d+),(\.\d+)\)", v)
        assert m, f"{tema}.yon-arti-zemin: beklenen rgba(r,g,b,a) literal, bulunan {v!r}"
        assert tuple(int(m.group(i)) for i in (1, 2, 3)) == arti_rgb, \
            f"{tema}.yon-arti-zemin: kanallar {m.group(1, 2, 3)} ≠ yon-arti {arti_hex} → {arti_rgb} (ana hex değişti, türev güncellenmedi)"
        assert m.group(4) == ".08", f"{tema}.yon-arti-zemin: alfa {m.group(4)} ≠ emsal .08"
