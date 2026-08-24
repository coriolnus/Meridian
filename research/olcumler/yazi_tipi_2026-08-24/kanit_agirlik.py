#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════════════
# AĞIRLIK EKSENİ + GÖVDE KALINLIĞI KANITLAYICISI — 08-07 `weights_and_stems.py`nin KOPYASI.
# ORİJİNAL: research/olcumler/yazi_tipi_2026-08-07/weights_and_stems.py (DONMUŞ, dokunulmadı).
#
# NE DEĞİŞTİ (tek kalem): `main()`e EKSEN DÖKÜMÜ eklendi. Orijinal `wght` ekseninin
# NEREDEN NEREYE gittiğini ve VARSAYILANINI hiç yazmıyordu — bu turun sorusu tam olarak o
# ("eksen 400-700'ü gerçekten kapsıyor mu, varsayılan 400 mü"). Eklenen `eksen_dokumu()`
# fvar min/default/max + OS/2 usWeightClass okur ve 400 ile 700 arasındaki GÖVDE
# KALINLIĞI FARKINI de kayda geçirir: eksen bildirilmiş ama ATIL olabilir (Meridian'ın
# daha önce Geist'te yakaladığı cv11/ss01 vakası) — kalınlık değişmiyorsa eksen yalan söyler.
# Ölçüm gövdeleri (`runs`, `raster_metrics`, `digit_advances_at`) BİREBİR AYNI.
# ═══════════════════════════════════════════════════════════════════════════════════════
"""Two things the default-instance dump cannot answer:

1. Do digit advances stay uniform across the weights the interface actually uses?
   (hmtx varies through HVAR; a font can be tabular at 400 and not at 700.)
2. Stroke weight and stroke contrast -> the halation argument for the night ground.
   Measured by rasterising at high ppem and counting ink runs, not by eyeballing.
"""
import json
import pathlib
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

D = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
WEIGHTS = (400, 500, 700)
PPEM = 400  # raster size for stem measurement


def runs(vals, thresh=128):
    """[(start,len)] of ink runs in a 1-D sample line."""
    out, s = [], None
    for i, v in enumerate(vals):
        ink = v < thresh          # black ink on white
        if ink and s is None:
            s = i
        elif not ink and s is not None:
            out.append((s, i - s))
            s = None
    if s is not None:
        out.append((s, len(vals) - s))
    return out


def raster_metrics(path, wght):
    """Stem width of 'l' and stroke contrast of 'o', in units/em."""
    try:
        f = ImageFont.truetype(str(path), PPEM)
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    except Exception as e:
        return {"ERROR": repr(e)}
    res = {}
    for ch, key in (("l", "stem_l"), ("H", "stem_H"), ("o", "o")):
        img = Image.new("L", (PPEM * 2, PPEM * 2), 255)
        d = ImageDraw.Draw(img)
        d.text((PPEM // 2, PPEM // 2), ch, font=f, fill=0)
        px = img.load()
        bbox = img.getbbox() if img.getbbox() else None
        inv = Image.eval(img, lambda v: 255 - v)
        bb = inv.getbbox()
        if not bb:
            continue
        x0, y0, x1, y1 = bb
        midy = (y0 + y1) // 2
        row = [px[x, midy] for x in range(x0, x1)]
        rr = runs(row)
        if ch in ("l", "H"):
            if rr:
                res[key] = round(min(r[1] for r in rr) / PPEM * 1000)
        else:
            # 'o': mid row gives the two vertical stems; mid column gives top/bottom bars
            if len(rr) >= 2:
                res["o_stem_vert"] = round(
                    sum(sorted(r[1] for r in rr)[:2]) / 2 / PPEM * 1000)
            midx = (x0 + x1) // 2
            col = [px[midx, y] for y in range(y0, y1)]
            cr = runs(col)
            if len(cr) >= 2:
                res["o_bar_horiz"] = round(
                    sum(sorted(r[1] for r in cr)[:2]) / 2 / PPEM * 1000)
    if res.get("o_bar_horiz"):
        res["stroke_contrast"] = round(res["o_stem_vert"] / res["o_bar_horiz"], 2)
    return res


def digit_advances_at(path, wght):
    f = TTFont(str(path))
    if "fvar" not in f:
        return None
    tags = {a.axisTag for a in f["fvar"].axes}
    if "wght" not in tags:
        return None
    ax = next(a for a in f["fvar"].axes if a.axisTag == "wght")
    w = max(ax.minValue, min(ax.maxValue, wght))
    inst = instancer.instantiateVariableFont(f, {"wght": w}, inplace=False)
    cmap = inst.getBestCmap()
    advs = {d: inst["hmtx"][cmap[ord(d)]][0] for d in "0123456789" if ord(d) in cmap}
    return {"requested": wght, "applied": w, "advances": advs,
            "uniform": len(set(advs.values())) == 1, "value": sorted(set(advs.values()))}


# ── TEK EKLEME (bkz. başlık) ──────────────────────────────────────────────────────────────
def eksen_dokumu(path, e):
    """`wght` ekseni GERÇEKTEN 400-700 mü, VARSAYILANI 400 mü, ve ATIL mı?

    Üç ayrı iddia, üç ayrı ölçüm:
      1. BİLDİRİM — fvar'daki min/default/max ve OS/2 usWeightClass (font ne diyor).
      2. KAPSAMA  — istenen 400 ve 700 bildirilen aralığın İÇİNDE mi (kırpılma olur mu).
      3. ATILLIK  — 400'de ve 700'de rasterize edilen 'l' gövde kalınlığı FARKLI mı.
                    Eksen bildirilip de kalınlık değişmiyorsa bildirim yalandır."""
    f = TTFont(str(path))
    if "fvar" not in f:
        return {"fvar": None, "neden": "fvar tablosu YOK — bu bir değişken font değil"}
    ax = {a.axisTag: [a.minValue, a.defaultValue, a.maxValue] for a in f["fvar"].axes}
    w = ax.get("wght")
    s400 = e["w400"]["raster"].get("stem_l")
    s700 = e["w700"]["raster"].get("stem_l")
    d = {
        "fvar": ax,
        "eksen_sayisi": len(ax),
        "usWeightClass": f["OS/2"].usWeightClass,
        "wght_min_default_max": w,
        "ARALIK_400_700_MU": w == [400.0, 400.0, 700.0] if w else False,
        "VARSAYILAN_400_MU": (w[1] == 400.0) if w else False,
        "400_kapsaniyor": (w[0] <= 400 <= w[2]) if w else False,
        "700_kapsaniyor": (w[0] <= 700 <= w[2]) if w else False,
        "stem_l_400": s400,
        "stem_l_700": s700,
        "stem_farki": (s700 - s400) if (s400 is not None and s700 is not None) else None,
        "EKSEN_ATIL_MI": (s400 == s700) if (s400 is not None and s700 is not None) else None,
    }
    if d["stem_farki"] is None:
        d["neden"] = "ÖLÇÜLEMEDİ — rasterizasyon 'l' gövdesini bulamadı, kalınlık farkı yok"
    return d
# ──────────────────────────────────────────────────────────────────────────────────────────


def main():
    out = {}
    for p in sorted(D.glob("*.ttf")):
        if p.stem == "Recursive-VF":
            continue  # measured through its two pinned instances instead
        e = out.setdefault(p.stem, {})
        for w in WEIGHTS:
            e[f"w{w}"] = {"tabular": digit_advances_at(p, w),
                          "raster": raster_metrics(p, w)}
        e["eksen"] = eksen_dokumu(p, e)          # TEK EKLEME
        print(p.stem, {w: e[f"w{w}"]["tabular"]["uniform"] if e[f"w{w}"]["tabular"] else None
                       for w in WEIGHTS},
              "stem_l@400=", e["w400"]["raster"].get("stem_l"),
              "contrast=", e["w400"]["raster"].get("stroke_contrast"))
        x = e["eksen"]
        print(f"   EKSEN wght={x.get('wght_min_default_max')} "
              f"aralik400_700={x.get('ARALIK_400_700_MU')} "
              f"varsayilan400={x.get('VARSAYILAN_400_MU')} "
              f"stem 400→700 = {x.get('stem_l_400')}→{x.get('stem_l_700')} "
              f"ATIL={x.get('EKSEN_ATIL_MI')}")
    OUT.write_text(json.dumps(out, indent=1))
    print("->", OUT)


main()
