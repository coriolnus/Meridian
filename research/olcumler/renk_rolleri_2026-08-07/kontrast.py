#!/usr/bin/env python3
"""WCAG 2.2 kontrast + OKLCh kroma ölçer (D1 renk rolleri, 2026-08-07).

Ölçüm burada yapılır, gözle değil. Alfa bileşimi açıkça hesaplanır: bir jeton
kendi %10 tinti üzerinde oturuyorsa ölçülen zemin ODUR, çıplak yüzey değil.
"""
import math, itertools, sys

ZEMIN = {
    "gunduz": {"bg": "#fbf9f8", "bg2": "#f5f4f2", "card": "#f2efed", "card-2": "#ece7e3",
               "accent-tint": "#eeeeee", "raise": "#fbf9f8", "slip": "#ece7e3"},
    "gece":   {"bg": "#1c1a18", "bg2": "#232120", "card": "#262320", "card-2": "#2f2b27",
               "accent-tint": "#302c28", "raise": "#38342f", "slip": "#2f2b27"},
}


def hx(s):
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def tohex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb):
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b):
    la, lb = lum(hx(a) if isinstance(a, str) else a), lum(hx(b) if isinstance(b, str) else b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def bilesik(ust, alfa, alt):
    """ust rengi alfa ile alt üzerine bindir → düz sRGB."""
    u = hx(ust) if isinstance(ust, str) else ust
    a = hx(alt) if isinstance(alt, str) else alt
    return tuple(u[i] * alfa + a[i] * (1 - alfa) for i in range(3))


# ---- OKLab / OKLCh ----
def srgb_oklab(rgb):
    r, g, b = (lin(v) for v in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3) if l > 0 else 0, m ** (1 / 3) if m > 0 else 0, s ** (1 / 3) if s > 0 else 0
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklab_srgb(lab):
    L, A, B = lab
    l_ = L + 0.3963377774 * A + 0.2158037573 * B
    m_ = L - 0.1055613458 * A - 0.0638541728 * B
    s_ = L - 0.0894841775 * A - 1.2914855480 * B
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    def gam(c):
        c = max(0.0, min(1.0, c))
        return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)
    return (gam(r), gam(g), gam(b))


def oklch(h):
    L, a, b = srgb_oklab(hx(h) if isinstance(h, str) else h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def oklch_hex(L, C, H):
    return tohex(oklab_srgb((L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))))


def rapor(ad, deger, tema, tint_alfa=0.10, zeminler=("bg", "bg2", "card", "card-2")):
    """jeton × (çıplak yüzey + kendi tinti o yüzeyin üstünde) kontrast satırları."""
    Z = ZEMIN[tema]
    out = []
    for z in zeminler:
        out.append((f"çıplak {z}", kontrast(deger, Z[z])))
    for z in zeminler:
        g = bilesik(deger, tint_alfa, Z[z])
        out.append((f"kendi tinti /{z}", kontrast(deger, g)))
    L, C, H = oklch(deger)
    return {"ad": ad, "deger": deger, "tema": tema, "L": round(L, 4), "C": round(C, 4),
            "H": round(H, 1), "olcum": [(k, round(v, 2)) for k, v in out],
            "en_kotu": round(min(v for _, v in out), 2)}


if __name__ == "__main__":
    for tema, jet in (("gunduz", {"--green": "#0c6a3b", "--amber": "#6e4a00", "--red": "#b3242c"}),
                      ("gece", {"--green": "#4cc38a", "--amber": "#e0a82e", "--red": "#f58b8f"})):
        print(f"--- {tema} (mevcut) ---")
        for ad, v in jet.items():
            r = rapor(ad, v, tema)
            print(f'{ad:<10} {v}  L={r["L"]:.3f} C={r["C"]:.4f} H={r["H"]:>5.1f}  en kötü={r["en_kotu"]}')
