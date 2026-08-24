"""ÖE1 DÖRDÜNCÜ SEÇENEK — Dub'ın KENDİ hue'ları + zorunlu luminans merdiveni.

NEDEN: 2026-08-24 jeton turu üç aday ölçtü (A: Dub hue'ları aynen ΔE 5,39 · B: kırmızı +17°
ΔE 13,53 · C: Omega ailesi 22-32) ve C'yi seçti. Ama A, luminans merdiveni ZORLANMADAN
ölçüldü — Dub'ın üç değeri birbirine yakın açıklıkta, ΔE'nin küçük çıkmasının ana sebebi bu.
B ise eşiği 1,5 puanla kaçırdı. DÖRDÜNCÜ seçenek hiç denenmedi: Dub'ın yeşil ve turuncu
HUE'larını koru, kırmızıyı turuncudan GERÇEKTEN uzağa it (kızıl bandı), ve üçüne birden
1,25'lik luminans merdivenini uygula.

EŞİK DEĞİŞMEDİ — docs/KARAR-2026-08-24-B §9.3'ten AYNEN:
  ÖE1-a komşu luminans oranı >= 1,20  · ÖE1-b komşu ΔE2000 >= 15  · ÖE1-c kendi tinti üstünde AA >= 4,5
Sıra bağlayıcı: a ve b sağlanmıyorsa c gevşetilemez.
"""
import math, json, pathlib

def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def unlin(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
def Y(rgb):
    r, g, b = [lin(v) for v in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def rgb2lab(rgb):
    r, g, b = [lin(v) for v in rgb]
    X = r*0.4124564 + g*0.3575761 + b*0.1804375
    Yy = r*0.2126729 + g*0.7151522 + b*0.0721750
    Z = r*0.0193339 + g*0.1191920 + b*0.9503041
    Xn, Yn, Zn = 0.95047, 1.0, 1.08883
    f = lambda t: t ** (1/3) if t > 216/24389 else (841/108) * t + 4/29
    fx, fy, fz = f(X/Xn), f(Yy/Yn), f(Z/Zn)
    return (116*fy - 16, 500*(fx - fy), 200*(fy - fz))
def lab2rgb(L, a, bb):
    fy = (L + 16) / 116; fx = fy + a/500; fz = fy - bb/200
    g = lambda t: t**3 if t**3 > 216/24389 else (116*t - 16) * 108/841
    X, Yy, Z = g(fx)*0.95047, g(fy)*1.0, g(fz)*1.08883
    r =  X*3.2404542 + Yy*-1.5371385 + Z*-0.4985314
    gg = X*-0.9692660 + Yy*1.8760108 + Z*0.0415560
    b =  X*0.0556434 + Yy*-0.2040259 + Z*1.0572252
    out = []
    for v in (r, gg, b):
        v = unlin(max(0.0, min(1.0, v)))
        out.append(max(0, min(255, round(v * 255))))
    return tuple(out)
def hexs(rgb): return "#%02x%02x%02x" % rgb
def unhex(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def dE2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb**7 / (Cb**7 + 25**7))) if Cb > 0 else 0
    a1p, a2p = (1+G)*a1, (1+G)*a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp = L2 - L1; dCp = C2p - C1p
    if C1p * C2p == 0: dhp = 0
    elif abs(h2p - h1p) <= 180: dhp = h2p - h1p
    elif h2p - h1p > 180: dhp = h2p - h1p - 360
    else: dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p*C2p) * math.sin(math.radians(dhp)/2)
    Lbp = (L1+L2)/2; Cbp = (C1p+C2p)/2
    if C1p*C2p == 0: hbp = h1p + h2p
    elif abs(h1p-h2p) <= 180: hbp = (h1p+h2p)/2
    elif h1p+h2p < 360: hbp = (h1p+h2p+360)/2
    else: hbp = (h1p+h2p-360)/2
    T = (1 - 0.17*math.cos(math.radians(hbp-30)) + 0.24*math.cos(math.radians(2*hbp))
         + 0.32*math.cos(math.radians(3*hbp+6)) - 0.20*math.cos(math.radians(4*hbp-63)))
    dTh = 30 * math.exp(-(((hbp-275)/25)**2))
    Rc = 2 * math.sqrt(Cbp**7 / (Cbp**7 + 25**7)) if Cbp > 0 else 0
    Sl = 1 + (0.015*(Lbp-50)**2) / math.sqrt(20 + (Lbp-50)**2)
    Sc = 1 + 0.045*Cbp; Sh = 1 + 0.015*Cbp*T
    Rt = -math.sin(math.radians(2*dTh)) * Rc
    return math.sqrt((dLp/Sl)**2 + (dCp/Sc)**2 + (dHp/Sh)**2 + Rt*(dCp/Sc)*(dHp/Sh))

def kont(a, b):
    ya, yb = Y(a)+0.05, Y(b)+0.05
    return max(ya, yb)/min(ya, yb)
def tint(rgb, zemin=(255,255,255), alfa=0.10):
    return tuple(round(alfa*v + (1-alfa)*z) for v, z in zip(rgb, zemin))

# --- Dub'ın kendi hue'ları (LAB'da ölçüldü) ---
DUB = {"vivid-green": "#16a34a", "tangerine": "#ea580c"}
hue = {}
for ad, h in DUB.items():
    L, a, b = rgb2lab(unhex(h))
    hue[ad] = (math.degrees(math.atan2(b, a)) % 360, math.hypot(a, b))
# kırmızı: turuncudan GERÇEKTEN uzak bir kızıl bandı ara (Dub'da yok — TÜRETME, beyanlı)
print("Dub hue'ları:", {k: f"{v[0]:.1f}° C={v[1]:.1f}" for k, v in hue.items()})

def uret(h_deg, L_hedef, C_bas=80):
    """Verilen hue ve hedef L'de, gamut içinde EN YÜKSEK kromalı sRGB rengi."""
    for C in [C_bas - i for i in range(0, C_bas)]:
        a = C * math.cos(math.radians(h_deg)); b = C * math.sin(math.radians(h_deg))
        rgb = lab2rgb(L_hedef, a, b)
        geri = rgb2lab(rgb)
        if abs(geri[0] - L_hedef) < 1.2 and abs(math.hypot(geri[1], geri[2]) - C) < 3:
            return rgb
    return lab2rgb(L_hedef, 0, 0)

sonuc = {"esik": {"OE1a_lum": 1.20, "OE1b_dE2000": 15, "OE1c_AA": 4.5}, "adaylar": []}
KART = (255, 255, 255)

# Luminans merdiveni: sev-3 en açık, sev-1 en koyu (şiddet arttıkça mürekkep zeminden uzaklaşır)
for kirmizi_hue in (0, 355, 350, 345, 340, 20):
    for L3 in (52, 50, 48, 46):
        for adim in (1.32, 1.28, 1.25):
            # hedef Y'ler: Y3 > Y2 > Y1, komşu oran = adim  ((Y+.05) oranı)
            Y3 = (Y(unhex("#16a34a")) + 0.05)
            Y2 = Y3 / adim - 0.0 ; Y1 = Y2 / adim
            def L_from_Y(y):  # Y → L*
                y = max(1e-6, y - 0.05)
                return 116 * ((y) ** (1/3)) - 16 if y > 216/24389 else 903.3 * y
            g = uret(hue["vivid-green"][0], L_from_Y(Y3))
            t = uret(hue["tangerine"][0], L_from_Y(Y2))
            k = uret(kirmizi_hue, L_from_Y(Y1))
            pairs = [("sev1-sev2", k, t), ("sev2-sev3", t, g)]
            lum = [max(Y(x)+0.05, Y(y)+0.05)/min(Y(x)+0.05, Y(y)+0.05) for _, x, y in pairs]
            de = [dE2000(rgb2lab(x), rgb2lab(y)) for _, x, y in pairs]
            aa = [kont(c, tint(c, KART)) for c in (k, t, g)]
            gecti = min(lum) >= 1.20 and min(de) >= 15 and min(aa) >= 4.5
            sonuc["adaylar"].append({
                "kirmizi_hue": kirmizi_hue, "adim": adim,
                "sev1": hexs(k), "sev2": hexs(t), "sev3": hexs(g),
                "lum": [round(x, 3) for x in lum], "dE2000": [round(x, 2) for x in de],
                "AA_kendi_tinti": [round(x, 2) for x in aa], "GECTI": gecti})

gecen = [a for a in sonuc["adaylar"] if a["GECTI"]]
sonuc["gecen_sayisi"] = len(gecen)
pathlib.Path("research/olcumler/oe1_dub_dorduncu_2026-08-24/sonuc.json").write_text(
    json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n{len(sonuc['adaylar'])} kombinasyon denendi · GEÇEN: {len(gecen)}")
for a in gecen[:6]:
    print(f"  kırmızı hue {a['kirmizi_hue']:>3}° adım {a['adim']}  "
          f"{a['sev1']} / {a['sev2']} / {a['sev3']}  "
          f"lum {a['lum']}  ΔE {a['dE2000']}  AA {a['AA_kendi_tinti']}")
if not gecen:
    en = max(sonuc["adaylar"], key=lambda a: min(a["dE2000"]))
    print("  hiçbiri geçmedi · en iyi ΔE:", en["dE2000"], "lum", en["lum"], "AA", en["AA_kendi_tinti"])
