#!/usr/bin/env python3
"""D1 · DEĞİŞEN HER ÇİFTİN ÖLÇÜMÜ — WCAG 2.2 AA (metin 4,5:1 · metin-dışı UI 3:1).

Bu betiğin çıktısı rapordaki tablodur. Elle yazılmış tek bir oran YOKTUR.
"""
from kontrast import ZEMIN, kontrast, bilesik, oklch, hx

G = ZEMIN["gunduz"]; N = ZEMIN["gece"]
JET = {
 "gunduz": {"tx": "#050505", "tx2": "#585450", "bg2": "#f5f4f2",
            "sev-1": "#b3242c", "sev-2": "#6e4a00", "sev-3": "#0c6a3b",
            "yon-arti": "#40654c", "yon-eksi": "#784e4b",
            "mod-kagit": "#585450", "mod-canli": "#723a96", "mod-kesif": "#635071",
            "olcek-guven": "#585450", "line-2": "#d4cfca", "card-2": "#ece7e3", "accent": "#050505"},
 "gece":   {"tx": "#d4d0cb", "tx2": "#b0a9a0", "bg2": "#232120",
            "sev-1": "#f58b8f", "sev-2": "#e0a82e", "sev-3": "#4cc38a",
            "yon-arti": "#8ab59c", "yon-eksi": "#d1a0a0",
            "mod-kagit": "#b0a9a0", "mod-canli": "#c598e7", "mod-kesif": "#b9a4ca",
            "olcek-guven": "#b0a9a0", "line-2": "#4a453f", "card-2": "#2f2b27", "accent": "#d4d0cb"},
}
# (etiket, ön, zemin-üreteci, tür)  — tür: "metin" 4.5 · "ui" 3.0
def satirlar(t):
    J, Z = JET[t], ZEMIN[t]
    hucre_a = lambda z: bilesik(J["yon-arti"], .08, Z[z])
    hucre_e = lambda z: bilesik(J["yon-eksi"], .07, Z[z])
    out = []
    for z in ("bg", "bg2", "card", "card-2"):
        for ad, v in (("yon-arti", J["yon-arti"]), ("yon-eksi", J["yon-eksi"]),
                      ("mod-canli", J["mod-canli"]), ("mod-kesif", J["mod-kesif"]),
                      ("olcek-guven", J["olcek-guven"])):
            out.append((f"{ad} · çıplak {z}", v, Z[z], "metin"))
            out.append((f"{ad} · kendi tinti /{z}", v, bilesik(v, .10, Z[z]), "metin"))
    # matris hücresi: rakam + değer + ince-örneklem rozeti hücrenin ÜSTÜNDE oturur
    for z in ("bg", "card"):
        out += [(f"matris + hücre · tx /{z}", J["tx"], hucre_a(z), "metin"),
                (f"matris + hücre · tx2 /{z}", J["tx2"], hucre_a(z), "metin"),
                (f"matris + hücre · yon-arti /{z}", J["yon-arti"], hucre_a(z), "metin"),
                (f"matris − hücre · tx /{z}", J["tx"], hucre_e(z), "metin"),
                (f"matris − hücre · yon-eksi /{z}", J["yon-eksi"], hucre_e(z), "metin"),
                (f"ince örneklem rozeti · guven /{z}", J["olcek-guven"], hucre_a(z), "metin"),
                (f"ince örneklem ROZETİ (accent-tint dolgu) /{z}", J["olcek-guven"],
                 bilesik(Z["accent-tint"] if "accent-tint" in Z else J["bg2"], 1.0, hucre_a(z)), "metin"),
                (f"ince örneklem KESİK kenar (UI) /{z}", bilesik(J["accent"], .45, hucre_a(z)), hucre_a(z), "ui")]
    # yeniden canlanan çiftler: kaynak-sırası çakışması kapandı
    for z in ("bg", "card"):
        out += [(f".chain.sev-1 /{z}", J["sev-1"], Z[z], "metin"),
                (f".hint.sev-2 /{z}", J["sev-2"], Z[z], "metin"),
                (f".hint.guven /{z}", J["olcek-guven"], Z[z], "metin")]
    # mod bandı ve mod çipi — metin DEĞİL, bileşen tanıtıcı (1.4.11)
    out += [("mod bandı · kâğıt (UI) /bg", bilesik(J["mod-kagit"], .65, Z["bg"]), Z["bg"], "ui"),
            ("mod bandı · canlı (UI) /bg", J["mod-canli"], Z["bg"], "ui"),
            ("mod çipi canlı · metin /kendi tinti üstünde",
             J["mod-canli"], bilesik(J["mod-canli"], .10, Z["card"]), "metin"),
            ("mod çipi canlı · saç teli (UI)",
             bilesik(J["mod-canli"], .35, bilesik(J["mod-canli"], .10, Z["card"])),
             bilesik(J["mod-canli"], .10, Z["card"]), "ui"),
            ("keşif çerçevesi (UI) /bg", bilesik(J["mod-kesif"], .70, Z["bg"]), Z["bg"], "ui"),
            ("keşif çipi · metin /card", J["mod-kesif"], bilesik(J["mod-kesif"], .10, Z["card"]), "metin"),
            ("oturum çıkışı hover · tx /card-2", J["tx"], Z["card-2"], "metin")]
    return out

print(f'{"çift":<46}{"gündüz":>9}{"gece":>9}   eşik  hüküm')
kotu = []
gun = {a: (o, z, k) for a, o, z, k in satirlar("gunduz")}
gec = {a: (o, z, k) for a, o, z, k in satirlar("gece")}
for ad in gun:
    g = kontrast(gun[ad][0], gun[ad][1]); n = kontrast(gec[ad][0], gec[ad][1])
    esik = 4.5 if gun[ad][2] == "metin" else 3.0
    ok = g >= esik and n >= esik
    if not ok:
        kotu.append((ad, round(g, 2), round(n, 2), esik))
    print(f'{ad:<46}{g:>9.2f}{n:>9.2f}{esik:>7.1f}  {"GEÇTİ" if ok else "KALDI"}')
print()
print("KROMA KISITI (yön < şiddet, her iki zeminde):")
for t in ("gunduz", "gece"):
    J = JET[t]
    sv = min(oklch(J[f"sev-{i}"])[1] for i in (1, 2, 3))
    yn = max(oklch(J["yon-arti"])[1], oklch(J["yon-eksi"])[1])
    print(f"  {t}: şiddet min C={sv:.4f} · yön maks C={yn:.4f} · oran {yn/sv:.2f} "
          f'{"GEÇTİ" if yn < sv else "KALDI"}')
print()
print("EŞİK ALTI:", kotu if kotu else "YOK")
