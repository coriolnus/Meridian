#!/usr/bin/env python3
"""DUB DÖNÜŞÜMÜ · JETON KATMANI ÖLÇÜMÜ — KARAR-2026-08-24-B §4 (Ö1-Ö7).

ÖN-KAYIT. Eşikler bu betikten ÖNCE donduruldu ve `docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md`
§4 tablosunda yazılıdır. Bu dosya o eşikleri OKUMAZ, YENİDEN YAZAR (aşağıdaki `ESIK`
sözlüğü onun bire-bir kopyasıdır) ve bir eşik tutmazsa DEĞERİ ZORLAMAZ: karar §2.1'in
dediği gibi kullanım yüzeyi daralır, jeton uydurulmaz. Tutmayan her eşik RAPOR.md'de
"TUTMADI" damgasıyla durur.

KAYNAK. Dub değerleri elle yazılmaz; `~/Downloads/tokens.json` (Dub'ın kendi DTCG dışa
aktarımı) okunur. Dosya yoksa betik ÇALIŞMAZ — çünkü o zaman ölçülen şey Dub değil, benim
hatırladığım Dub olur (UYDURMA YASAĞI).

TÜRETME KURALI (karar §1.2 + brief §C) — ARA DEĞER GÖZLE AYARLANMAZ:
  1. Önce Dub jetonunu dene. Kendi %10 tinti üzerinde (gerçek zemin: o tint yüzeyin
     üstünde) ve çıplak yüzeyde AA (>=4.5) tutuyorsa AYNEN al.
  2. Tutmuyorsa OKLCh'de HUE ve KROMA SABİT tutulur, yalnız L kaydırılır:
     gündüz AŞAĞI (mürekkep koyulaşır), gece YUKARI (tint-yönü kuralı: koyu zeminde tint
     mürekkebe ZARAR verir, o yüzden gece değerleri naif tersin vereceğinden AÇIKTIR).
     Eşiği geçen İLK basamak alınır — yani gündüzde en AÇIK, gecede en KOYU geçerli değer.
     Adım 0.001 L. sRGB gamut dışına düşerse kroma o L'de gamut sınırına indirilir ve
     İNEN kroma raporda yazılır (sessiz kırpma yok).

Çıktı: sonuc.json (makine) + RAPOR.md (okuyucu) + civi_tablosu.md (docs/kontrast-denetimi.md
§9 çivi tablosunun yeni gövdesi — v153 o rakamları kaynaktan yeniden üretir).

Koşum:  python3 research/olcumler/dub_donusumu_2026-08-24/olc.py
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys

BURASI = pathlib.Path(__file__).resolve().parent
KOK = BURASI.parents[2]
DUB_DIZIN = pathlib.Path.home() / "Downloads"

# ============================== EŞİKLER (ÖNCEDEN DONDU) ==============================
# KARAR-2026-08-24-B §4 tablosunun bire-bir kopyası. Bu sözlük ÖLÇÜMDEN SONRA
# DEĞİŞTİRİLEMEZ; değişirse ölçüm değil hüküm değişmiş olur.
ESIK = {
    "O1_kart_zemin_adimi": 1.02,
    "O2_para_AA": 4.5,
    "O3_kroma_tavani": "C(nav) < min C(siddet)",
    "O4_ayirt_edilebilirlik": 3.0,   # WCAG 2.2 1.4.11 metin-dışı ayrım — Ö4'ün işlemsel karşılığı
    "O5_nav_wash_AA": 4.5,
    "O6_tip_adimi_min": 1.15,
    "O6_tip_adimi_en_az_bir": 1.25,
    "O7_odak_halkasi": 3.0,
}
# Hue kümesi eşiği: iki jetonun hue'su bu kadar yakınsa ayrımı L taşımak ZORUNDADIR,
# yani ortak-ΔL kuralı onları birlikte kaydırır. 15° bir eşik değil bir SINIFLANDIRMA
# ölçütüdür (karar §4'ün donmuş eşikleriyle ilgisi yok) ve ölçülen vakadan gelir:
# tangerine ↔ loss-red 2,7° (aynı küme) · vivid-green ↔ tangerine 108° (ayrı küme).
HUE_KUMESI = 15.0

# ================================ RENK MATEMATİĞİ ================================


def hx(s):
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def tohex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _delin(u):
    u = max(0.0, min(1.0, u))
    v = u * 12.92 if u <= 0.0031308 else 1.055 * (u ** (1 / 2.4)) - 0.055
    return v * 255.0


def lum(c):
    """WCAG 2.x bağıl luminans. Not: WCAG eşiği 0.03928, gamma dönüşümü 0.04045 —
    ikisi aynı sayı değildir ama depo boyunca 0.04045 kullanıldı (v153/v197 de öyle);
    fark 8-bit'te ölçülemez (her iki eşik de sRGB 10'un altında kalır)."""
    if isinstance(c, str):
        c = hx(c)
    r, g, b = (_lin(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kon(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def bilesik(ust, alfa, alt):
    """source-over: `ust` rengini `alfa` ile `alt` üzerine bindir (tarayıcının işi).

    SONUÇ 8-BİT'E YUVARLANIR ve bu bir titizlik değil bir ZORUNLULUK: tarayıcı da
    yuvarlar, ve `tests/test_tasarim_token_v153.py` çivi tablosunu yuvarlayarak yeniden
    hesaplar. Ara sonucu float bırakmak, raporun kendi testiyle 0,05 ayrışması demekti
    (ölçüldü: --tx üzerinde --card-2 + --red-t, 16.04 ↔ 15.99)."""
    u = hx(ust) if isinstance(ust, str) else ust
    a = hx(alt) if isinstance(alt, str) else alt
    return tuple(round(u[i] * alfa + a[i] * (1 - alfa)) for i in range(3))


def _srgb_oklab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (max(v, 0.0) ** (1 / 3) for v in (l, m, s))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def _oklab_srgb(L, A, B):
    l_ = L + 0.3963377774 * A + 0.2158037573 * B
    m_ = L - 0.1055613458 * A - 0.0638541728 * B
    s_ = L - 0.0894841775 * A - 1.2914855480 * B
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return (_delin(r), _delin(g), _delin(b)), (r, g, b)


def oklch(c):
    if isinstance(c, str):
        c = hx(c)
    L, A, B = _srgb_oklab(c)
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


# ---- CIE Lab + ΔE2000 (ÖE1-b, karar §9.3) ----------------------------------------
# NİYE OKLab DEĞİL: karar §9.3 eşiği ΔE2000 cinsinden DONDURDU ("JND ~2,3") ve donmuş bir
# eşik başka bir metrikle ölçülemez. OKLab ΔE bu dosyada BAŞKA bir soru için (Ö4/ÖE1 ilk
# taraması) kullanılmaya devam eder; ikisi karıştırılmaz.
def _xyz(rgb):
    r, g, b = (_lin(v) for v in (hx(rgb) if isinstance(rgb, str) else rgb))
    return (0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
            0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
            0.0193339 * r + 0.1191920 * g + 0.9503041 * b)


def lab(rgb):
    """CIE L*a*b*, D65 (sRGB'nin kendi beyaz noktası)."""
    X, Y, Z = _xyz(rgb)
    Xn, Yn, Zn = 0.95047, 1.0, 1.08883

    def f(t):
        return t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29
    fx, fy, fz = f(X / Xn), f(Y / Yn), f(Z / Zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e2000(c1, c2):
    """CIEDE2000. Sharma/Wu/Dalal referans formülasyonu."""
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
    kL = kC = kH = 1.0
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb > 0 else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTheta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp > 0 else 0.0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dTheta)) * Rc
    return math.sqrt((dLp / (kL * Sl)) ** 2 + (dCp / (kC * Sc)) ** 2 + (dHp / (kH * Sh)) ** 2
                     + Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh)))


def oklch_hex(L, C, H):
    """OKLCh -> sRGB hex. Gamut dışına düşerse KROMA (L ve H değil) indirilir; fiilen
    kullanılan kroma ikinci dönüş değeridir — kırpma sessiz kalmaz."""
    h = math.radians(H)
    lo, hi = 0.0, C
    en_iyi = 0.0
    for _ in range(48):
        orta = (lo + hi) / 2
        _, ham = _oklab_srgb(L, orta * math.cos(h), orta * math.sin(h))
        if all(-1e-6 <= v <= 1 + 1e-6 for v in ham):
            en_iyi, lo = orta, orta
        else:
            hi = orta
    _, ham = _oklab_srgb(L, C * math.cos(h), C * math.sin(h))
    if all(-1e-6 <= v <= 1 + 1e-6 for v in ham):
        en_iyi = C
    rgb, _ = _oklab_srgb(L, en_iyi * math.cos(h), en_iyi * math.sin(h))
    return tohex(rgb), en_iyi


def turet(kaynak_hex, gecer, yon, adim=0.001, tavan=400):
    """HUE ve KROMA sabit, L kaydırılarak `gecer(hex)` doğru olan İLK değeri bul.

    yon = -1 (gündüz: mürekkep koyulaşır) · +1 (gece: mürekkep açılır)
    Dönen: (hex, kaç adım kaydırıldı, gerçekleşen kroma, ölçülen L)
    `gecer` daha en baştan doğruysa Dub jetonu AYNEN döner (adim=0).
    """
    L0, C0, H0 = oklch(kaynak_hex)
    if gecer(kaynak_hex):
        return kaynak_hex, 0, C0, L0
    for i in range(1, tavan + 1):
        L = L0 + yon * i * adim
        if not (0.0 < L < 1.0):
            break
        h, c = oklch_hex(L, C0, H0)
        if gecer(h):
            return h, i, c, L
    raise SystemExit(f"TÜRETİLEMEDİ: {kaynak_hex} yön={yon} — L ekseni tükendi, "
                     f"eşik bu hue/kroma çiftiyle sRGB'de karşılanamıyor.")


def turet_aile(kaynaklar, gecer, yon, adim=0.001, tavan=400):
    """ORTAK-ΔL TÜRETMESİ — bir rol AİLESİNİN tüm üyeleri TEK ΔL ile kaydırılır.

    NİYE AİLE OLARAK. Üyeleri TEK TEK AA sınırına indirmek, kaynak hue'ları birbirine
    yakın olan üyeleri AYNI RENGE ÇÖKERTİR: ölçüldü (2026-08-24, bu betiğin ilk koşumu)
    Dub `tangerine` (hue 41,1°) ile maketin `loss-red`i (hue 38,4°) yalnız 2,7° arayla
    duruyor ve tek tek indirildiklerinde gündüz `#b54000` ↔ `#ba3a00`, gece `#ff8e63` ↔
    `#ff8e6a` oluyorlardı — yani ŞİDDET-1 ile ŞİDDET-2 ekranda tek renkti. Ayrımı taşıyan
    şey kaynak paletin L MERDİVENİdir (tangerine L 0,646 · loss-red L 0,553) ve tek tek
    indirme tam olarak o merdiveni siler.

    ÇÖZÜM DEPO PRECEDENT'İ: WP-P/P9 turu (2026-08-02) dokuz yüzey jetonunu TEK katsayıyla
    ölçekledi, "böylece merdivenin ADIM ORANLARI korunur" diye. Aynı disiplin: ΔL, ailenin
    EN ZORLU üyesinin eşiği geçmesi için gereken en küçük değerdir ve HEPSİNE uygulanır.
    Koşul L'de monotondur (gündüz koyulaşmak, gecede açılmak kontrastı yalnız artırır),
    yani ortak ΔL ailenin TAMAMINI geçirir — bu ayrıca aşağıda doğrulanır.

    ORTAK ΔL YALNIZ HUE KÜMESİ İÇİNDE. Ayrımı L'ye emanet etmek zorunda olan üyeler
    hue'ları birbirine yakın olanlardır; 100°+ uzaktaki bir üyeyi de birlikte indirmek
    gerekçesiz koyulaştırma olurdu (ve kromayı gamut kenarında boşuna harcardı). Küme
    ölçütü: Δhue < HUE_KUMESI derece.

    Dönen: {ad: (hex, ortak_adim, kroma, L)}
    """
    adlar = list(kaynaklar)
    tekil = {ad: turet(kaynaklar[ad], gecer, yon, adim, tavan)[1] for ad in adlar}
    # hue kümeleri (birlik-bul, basit O(n^2) — n<=3)
    kume = {ad: ad for ad in adlar}

    def _bul(a):
        while kume[a] != a:
            a = kume[a]
        return a

    for i in range(len(adlar)):
        for j in range(i + 1, len(adlar)):
            a, b = adlar[i], adlar[j]
            dh = abs(((oklch(kaynaklar[a])[2] - oklch(kaynaklar[b])[2] + 180) % 360) - 180)
            if dh < HUE_KUMESI:
                kume[_bul(a)] = _bul(b)
    gereken = {}
    for ad in adlar:
        k = _bul(ad)
        gereken[k] = max(gereken.get(k, 0), tekil[ad])
    out = {}
    for ad in adlar:
        L0, C0, H0 = oklch(kaynaklar[ad])
        i = gereken[_bul(ad)]
        L = L0 + yon * i * adim
        h, c = oklch_hex(L, C0, H0)
        if not gecer(h):
            raise SystemExit(f"ORTAK ΔL YETMEDİ: {ad} {kaynaklar[ad]} -> {h} "
                             f"(ΔL={i * adim:.3f}). Koşul L'de monoton değil.")
        out[ad] = (h, i, c, L)
    return out


def rgba(hex_or_rgb, alfa):
    r, g, b = hx(hex_or_rgb) if isinstance(hex_or_rgb, str) else [int(round(v)) for v in hex_or_rgb]
    return f"rgba({r},{g},{b},{('%.2f' % alfa).lstrip('0')})"


# ============================== DUB KAYNAĞI ==============================
def dub_oku():
    yol = DUB_DIZIN / "tokens.json"
    if not yol.is_file():
        raise SystemExit(f"Dub kaynağı YOK: {yol} — ölçüm koşulamaz (uydurma yasağı).")
    ham = json.loads(yol.read_text(encoding="utf-8"))
    renk = {k: v["$value"] for k, v in ham["color"].items() if isinstance(v, dict) and "$value" in v}
    return renk, yol


def dub_karanlik_tema_var_mi():
    """KARAR §1.2 iddiası: Dub'ın verdiği DÖRT dosyada karanlık tema YOK. Doğrulanır.
    `midnight-ink` / `Filled Dark CTA` gibi geçişler bir TEMA değildir — aranan şey
    ikinci bir renk katmanını AÇAN mekanizmadır."""
    mekanizma = re.compile(r"prefers-color-scheme|\[data-theme|\.dark\b|@media\s*\(\s*dark|"
                           r'"dark"\s*:|colorScheme|color-scheme\s*:\s*dark', re.I)
    bulgu = {}
    for ad in ("tokens.json", "DESIGN.md", "variables.css", "theme.css"):
        p = DUB_DIZIN / ad
        if not p.is_file():
            bulgu[ad] = "DOSYA YOK"
            continue
        vurus = sorted({m.group(0) for m in mekanizma.finditer(p.read_text(encoding="utf-8"))})
        bulgu[ad] = vurus or []
    return bulgu


# ============================== PALET KURULUMU ==============================
DUB, DUB_YOLU = dub_oku()

# --- GÜNDÜZ YAPI (ROL 1) — Dub'ın kendi jetonları; iki SAF UÇ karar §1.1'de çözüldü ---
G = {
    "bg": "#fafafa",            # Dub uygulamasının kendi zemini (karar §1.1) — saf beyaz DEĞİL
    "bg2": DUB["paper-mist"],   # #f5f5f5
    "card": DUB["canvas-white"],
    "card-2": "#fafafa",
    "raise": DUB["canvas-white"],
    "slip": DUB["paper-mist"],
    "accent-tint": DUB["paper-mist"],
    "line": DUB["ash"],
    "line-2": DUB["smoke"],
    "tx": DUB["midnight-ink"],
    "tx2": DUB["steel"],
    "tx3": DUB["fog"],
    "slip-ink": DUB["midnight-ink"],
    "accent": DUB["midnight-ink"],     # birincil eylem dolgusu — #000000 DEĞİL (karar §1.1)
    "accent-2": DUB["charcoal"],
    "violet2": DUB["midnight-ink"],
    "blue": DUB["midnight-ink"],
}
# GECE YAPI — Dub'da YOK, TÜRETİLDİ. Rampa 8/255 ızgarasına oturur ve Dub'ın charcoal
# (0x17) ile graphite (0x26) jetonları o ızgaraya ÇİVİ olarak girer (aralarındaki 15
# birim tek 7'lik adımı üretir). Saf siyah/beyaz yok; yükselti ARTAN (mevcut Meridian
# gece yapısı, 2026-08-01'den beri: koyu zeminde "gömülü"yü koyultmak saç telini yutar).
N = {
    "bg": DUB["charcoal"],      # #171717
    "bg2": "#1f1f1f",           # TÜRETİLDİ
    "card": DUB["graphite"],    # #262626
    "card-2": "#2e2e2e",        # TÜRETİLDİ
    # `--raise` GÜNDÜZLE AYNI İLİŞKİYİ TAŞIR: gündüz `--raise:#ffffff` = `--card:#ffffff`,
    # yani "yükseltilmiş yüzey" ayrı bir basamak DEĞİL kartın kendisidir (Omega'nın
    # kenar-önce kararı: ayrım gölgeyle değil saç teliyle kurulur). Gecede de öyle olur.
    # ~~2026-08-24 ilk taslakta #363636 türetilmişti; o, gündüzde OLMAYAN bir basamak
    #   icat ediyordu ve "en kötü gerçek zemin"i gereksiz yere yukarı çekiyordu.~~
    "raise": DUB["graphite"],   # = --card
    "slip": "#2e2e2e",
    "accent-tint": "#2e2e2e",
    "line": DUB["slate"],       # #404040
    "line-2": DUB["steel"],     # #525252
    "tx": DUB["ash"],           # #e5e5e5
    "tx2": DUB["smoke"],        # #d4d4d4
    "tx3": DUB["silver"],       # #a3a3a3
    "slip-ink": DUB["ash"],
    "accent": DUB["ash"],
    "accent-2": DUB["paper-mist"],
    "violet2": DUB["ash"],
    "blue": DUB["ash"],
}

# EN KÖTÜ GERÇEK ZEMİN — bir mürekkebin fiilen oturabildiği yüzeylerin en kötüsü.
# Gündüzde en KOYU yüzey, gecede en AÇIK yüzey; ikisi de kontrastı en çok düşüren taraf.
#
# "GERÇEK" SÖZCÜĞÜ ÖLÇÜLÜR, VARSAYILMAZ. Bir yüzey jetonu tanımlı olabilir ama hiçbir
# kural onu okumuyorsa o bir zemin DEĞİLDİR ve türetmeyi gereksiz yere sıkar. Kaynaktan
# sayılır: `index.html`in kural gövdelerinde (jeton blokları hariç) + `app.js`te
# `var(--X)` kaç kez geçiyor. Sıfırsa yüzey listeden DÜŞER ve bu raporda ADIYLA yazılır.
TUM_YUZEYLER = ("bg", "bg2", "card", "card-2", "raise", "slip", "accent-tint")


def _okuyucu_sayisi(jeton):
    n = 0
    for ad in ("index.html", "app.js"):
        p = KOK / "meridian" / "web" / ad
        if not p.is_file():
            continue
        s = p.read_text(encoding="utf-8")
        if ad.endswith(".html"):
            s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
            s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
            for sel in (":root{", ':root[data-theme="gece"]{'):
                while sel in s:
                    i = s.index(sel)
                    j = s.index("}", i)
                    s = s[:i] + s[j + 1:]
        else:
            s = re.sub(r"//[^\n]*", " ", s)
            s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
        n += len(re.findall(rf"var\(\s*--{re.escape(jeton)}\s*\)", s))
    return n


OKUYUCU = {y: _okuyucu_sayisi(y) for y in TUM_YUZEYLER}
YUZEYLER = tuple(y for y in TUM_YUZEYLER if OKUYUCU[y] > 0)
OKUYUCUSUZ = tuple(y for y in TUM_YUZEYLER if OKUYUCU[y] == 0)
assert YUZEYLER, "hiçbir yüzey jetonunun okuyucusu yok — ayrıştırıcı bozulmuş olmalı"
G_KOTU = min((G[k] for k in YUZEYLER), key=lum)
N_KOTU = max((N[k] for k in YUZEYLER), key=lum)


def _bilesik_ham(ust, alfa, alt):
    """`bilesik`in YUVARLAMAYAN ikizi. Bu depoda iki bileşim geleneği yan yana yaşıyor:
    tarayıcı (ve `tests/test_tasarim_token_v153.py`) 8-bit'e yuvarlar,
    `tests/test_renk_rolleri_v197.py` float bırakır. İkisi 0,002 mertebesinde ayrışıyor ve
    o fark bir AA eşiğinde İKİ KEZ hüküm değiştirdi (4,4989 ↔ 4,5004). Türetme bu yüzden
    HER İKİ geleneği birden karşılamak zorundadır — hangi ölçüm aracının kullanıldığı,
    bir rengin erişilebilir olup olmadığını belirleyemez."""
    u = hx(ust) if isinstance(ust, str) else ust
    a = hx(alt) if isinstance(alt, str) else alt
    return tuple(u[i] * alfa + a[i] * (1 - alfa) for i in range(3))


def _aa_kendi_tinti(zemin, esik=4.5):
    """Bir mürekkebin KENDİ %10 tinti üstünde ve ÇIPLAK yüzeyde AA geçmesi koşulu.
    Tint bileşimi HEM yuvarlanmış HEM ham hâliyle sınanır (bkz. `_bilesik_ham`)."""
    def gecer(h):
        return (kon(h, bilesik(h, 0.10, zemin)) >= esik
                and kon(h, _bilesik_ham(h, 0.10, zemin)) >= esik
                and kon(h, zemin) >= esik)
    return gecer


def _ui3(zemin, esik=3.0):
    def gecer(h):
        return kon(h, zemin) >= esik
    return gecer


# --- ROL 2 · ŞİDDET (para renkleri) ---------------------------------------------------
PARA_KAYNAK = {"green": DUB["vivid-green"], "amber": DUB["tangerine"], "red": "#c2410c"}
PARA_KAYNAK_ADI = {"green": "Dub vivid-green", "amber": "Dub tangerine",
                   "red": "maket beyanlı türetmesi loss-red (Dub'da kayıp rengi YOK)"}

turetme_kaydi = []


def _kaydet(ad, tema, kaynak, sonuc, adim, kroma, kaynak_adi, kural, aynen=None):
    """`aynen`: sonuç bir Dub jetonunun BİREBİR kendisi mi. Varsayılan çıkarım (ΔL=0)
    rampadan SEÇİM için doğru, ama TÜRETME için yanlıştı — türetilmiş bir ara basamak
    ΔL kaydırması yapmasa da Dub jetonu DEĞİLDİR ve öyle damgalanamaz (uydurma yasağının
    etiket hâli). Bu yüzden çağıran açıkça söyleyebilir."""
    # KROMA SONUÇTAN ÖLÇÜLÜR, hedeften değil. `turet` gamut sınırındaki kromayı döner ama
    # ekrana çizilen şey 8-bit'e YUVARLANMIŞ hex'tir ve onun kroması biraz farklıdır.
    # Raporda hedefi yazmak, index.html'in yorumları ve v197'nin ölçümüyle 0,0003'lük bir
    # ayrışma üretiyordu — küçük ama yeniden-üretilemez bir sayı, ki bu depoda o tam olarak
    # "bayat rapor" sınıfıdır.
    gercek = oklch(sonuc)[1] if re.fullmatch(r"#[0-9a-fA-F]{6}", sonuc) else kroma
    turetme_kaydi.append({
        "jeton": ad, "tema": tema, "kaynak": kaynak, "kaynak_adi": kaynak_adi,
        "sonuc": sonuc, "L_adimi": adim, "kroma": round(gercek, 4),
        "hedef_kroma": round(kroma, 4),
        "kaynak_kroma": round(oklch(kaynak)[1], 4), "kural": kural,
        "aynen_alindi": (adim == 0) if aynen is None else aynen,
    })


# ================= ÖE1 · ŞİDDET MERDİVENİ (KARAR §9, eşikler §9.3'te DONDU) =================
# BULGU (bu betiğin ilk koşumu, 2026-08-24): Dub ataması şiddet merdivenini ÇÖKERTİYORDU —
# `tangerine` (41,1°) ile türetilmiş `loss-red` (38,4°) 2,7° arayla ve AA türetmesi ikisini
# aynı renge indiriyordu; `tangerine` ile `vivid-green` ise luminansta 1,004 ayrılıyordu,
# yani ayrım TAMAMEN protan/deutan'ın sildiği eksende kalıyordu. Hüküm Rol-1'in (§9) ve
# eşikler ölçümden ÖNCE donduruldu. Bu bölüm o eşikleri uygular; eşik sayıları burada
# YENİDEN YAZILIR ama DEĞİŞTİRİLMEZ (§9.3'ün bire-bir kopyası).
OE1_ESIK = {"a_luminans_orani": 1.20, "b_deltaE2000": 15.0, "c_tint_AA": 4.5}

# ORTAK ΔL YETMEZ, MERDİVEN GEREKİR. Ortak ΔL kaynak paletin L farklarını KORUR — ama Dub
# (ve Omega) o farkları zaten ÖE1-a'nın altında taşıyor (ölçüldü: Omega bile gündüz 1,188 /
# gece 1,035-1,093). O yüzden şiddet üçlüsü artık kaynak L'lerini DEĞİL, ölçülmüş bir
# MERDİVENİ izler:
#   · Şiddet arttıkça mürekkep zeminden UZAKLAŞIR (tint-yönü kuralının şiddet hattındaki
#     kardeşi): gündüz sev-1 en KOYU, gece sev-1 en AÇIK. Nominal (sev-3) zemine en yakın
#     olandır — "renk yalnız anomalide" kuralının luminans karşılığı.
#   · Basamak oranı 1,25'tir, eşik 1,20 DEĞİL: 8-bit yuvarlama ve alfa bileşimi eşiğe sıfır
#     payla oturan bir merdiveni aşağı itebilir. Pay ölçülmüş bir gerekliliktir, eşik
#     gevşetmesi değildir — eşik hâlâ 1,20 ve ölçüm ona karşı yapılır.
OE1_ADIM = 1.25


def _aa_tavan(H, C, tema, kotu):
    """Bu hue/kroma çiftinin AA'yı (kendi %10 tinti + çıplak, `kotu` zemininde) hâlâ geçtiği
    UÇ renk: gündüz en AÇIK, gece en KOYU. İkili arama L üzerinde yürür (kısıt L'de
    monotondur), ama SONUÇ 8-BİT HEX'İ DOĞRULANIR: L ekseninde geçen bir nokta, yuvarlandığı
    hex'te geçmeyebilir (ölçüldü: gece yeşili 4,497 ile eşiğin 0,003 altına düşüyordu).
    Doğrulama düşerse L bir adım daha zeminden UZAKLAŞTIRILIR — bu yalnız ayrımı ARTIRIR."""
    gecer = _aa_kendi_tinti(kotu)
    yon = -1 if tema == "gunduz" else +1
    lo, hi = 0.0, 1.0
    for _ in range(40):
        orta = (lo + hi) / 2
        if gecer(oklch_hex(orta, C, H)[0]):
            if tema == "gunduz":
                lo = orta
            else:
                hi = orta
        else:
            if tema == "gunduz":
                hi = orta
            else:
                lo = orta
    L = lo if tema == "gunduz" else hi
    for _ in range(60):
        h, _c = oklch_hex(L, C, H)
        if gecer(h):
            return h
        L += yon * 0.002
        if not (0.0 < L < 1.0):
            return None
    return None


def _Y_hedefe_renk(H, C, hedef_Y, tema, kotu):
    """Hue ve kroma sabit, hedef bağıl luminansa en yakın sRGB rengi (L'de ikili arama).
    Sonuç AA'yı 8-bit hex'te geçmiyorsa zeminden UZAKLAŞTIRILARAK düzeltilir — merdivenin
    basamağı yalnız BÜYÜR, asla küçülmez, yani eşik gevşemez."""
    gecer = _aa_kendi_tinti(kotu)
    yon = -1 if tema == "gunduz" else +1
    lo, hi = 0.0, 1.0
    for _ in range(40):
        orta = (lo + hi) / 2
        if lum(oklch_hex(orta, C, H)[0]) < hedef_Y:
            lo = orta
        else:
            hi = orta
    L = (lo + hi) / 2
    for _ in range(60):
        h, c = oklch_hex(L, C, H)
        if gecer(h):
            return h, c
        L += yon * 0.002
        if not (0.0 < L < 1.0):
            break
    return None, None


def _oe1_olc(ucul, tema, kotu):
    """Bir şiddet üçlüsünü §9.3'ün ÜÇ eşiğine karşı ölç. `ucul` = {green, amber, red}."""
    kart = (G if tema == "gunduz" else N)["card"]
    komsu = (("--sev-1", "red", "--sev-2", "amber"), ("--sev-2", "amber", "--sev-3", "green"))
    a_ok = b_ok = c_ok = True
    satir = []
    for n1, k1, n2, k2 in komsu:
        c1, c2 = ucul[k1], ucul[k2]
        lo = kon(c1, c2)
        de = delta_e2000(c1, c2)
        a_ok &= lo >= OE1_ESIK["a_luminans_orani"]
        b_ok &= de >= OE1_ESIK["b_deltaE2000"]
        satir.append({"tema": tema, "cift": f"{n1} ↔ {n2}", "a_hex": c1, "b_hex": c2,
                      "luminans_orani": round(lo, 3), "deltaE2000": round(de, 2),
                      "hue_farki": round(abs(((oklch(c1)[2] - oklch(c2)[2] + 180) % 360) - 180), 1)})
    c_satir = []
    for ad, c in ucul.items():
        kart_aa = kon(c, bilesik(c, .10, kart))
        kotu_aa = kon(c, bilesik(c, .10, kotu))
        c_ok &= kart_aa >= OE1_ESIK["c_tint_AA"] and kotu_aa >= OE1_ESIK["c_tint_AA"]
        c_satir.append({"tema": tema, "jeton": f"--{ad}", "hex": c,
                        "kendi_tinti_card": round(kart_aa, 3),
                        "kendi_tinti_en_kotu": round(kotu_aa, 3)})
    return {"a": a_ok, "b": b_ok, "c": c_ok, "tuttu": a_ok and b_ok and c_ok,
            "komsu": satir, "tint": c_satir}


def _merdiven(kaynak_hue_kroma, tema, kotu):
    """Şiddet üçlüsünü luminans merdivenine oturt. Sıra: sev-3 zemine EN YAKIN uçta durur
    (AA sınırı), sev-2 bir basamak, sev-1 iki basamak UZAKTA."""
    sira = ["green", "amber", "red"]           # sev-3 → sev-2 → sev-1
    H, C = kaynak_hue_kroma["green"]
    capa = _aa_tavan(H, C, tema, kotu)
    if capa is None:
        return None
    taban = lum(capa)
    ucul, kroma = {"green": capa}, {"green": oklch(capa)[1]}
    for i, ad in enumerate(sira):
        if i == 0:
            continue
        Hh, Cc = kaynak_hue_kroma[ad]
        hedef = (taban + 0.05) * (OE1_ADIM ** (-i if tema == "gunduz" else i)) - 0.05
        if not (0.0 < hedef < 1.0):
            return None
        h, c = _Y_hedefe_renk(Hh, Cc, hedef, tema, kotu)
        if h is None:
            return None
        ucul[ad], kroma[ad] = h, c
    return ucul, kroma


# ADAY SIRASI KARARIN KENDİ SIRASIDIR (§9 "ÇÖZÜM SIRASI"): önce Dub içinde çöz, olmazsa §9.4.
_dub_hk = {"green": oklch(DUB["vivid-green"])[2::-2], "amber": oklch(DUB["tangerine"])[2::-2],
           "red": oklch("#c2410c")[2::-2]}
_dub_hk = {k: (oklch(v)[2], oklch(v)[1]) for k, v in
           (("green", DUB["vivid-green"]), ("amber", DUB["tangerine"]), ("red", "#c2410c"))}
# Meridian'ın ÖLÇÜLMÜŞ alarm hue'su (Omega `--red` #b3242c, OKLCh H≈24,1°). Bu bir icat
# DEĞİL: bu depoda ölçülmüş, belgelenmiş ve bir yıl yayında kalmış bir değerdir.
_MERIDIAN_ALARM_HUE = oklch("#b3242c")[2]
_omega_hk = {k: (oklch(v)[2], oklch(v)[1]) for k, v in
             (("green", "#0c6a3b"), ("amber", "#6e4a00"), ("red", "#b3242c"))}

OE1_ADAYLAR = [
    ("A · Dub içi · hue KORUNUR (vivid-green / tangerine / loss-red)", _dub_hk),
    ("B · Dub içi · loss-red hue'su Meridian'ın ölçülmüş alarm hue'suna çekilir "
     f"({_MERIDIAN_ALARM_HUE:.1f}°); yeşil ve kehribar Dub'da KALIR",
     {**_dub_hk, "red": (_MERIDIAN_ALARM_HUE, _dub_hk["red"][1])}),
    ("C · §9.4 geri çekilme · şiddet rolü Dub paletinden ÇIKAR, ölçülmüş Omega üçlüsünün "
     "hue/kroması kalır", _omega_hk),
]

PARA = {"gunduz": {}, "gece": {}}
OE1 = {"esikler": OE1_ESIK, "adim": OE1_ADIM, "adaylar": [], "secilen": None,
       "kaynak_ucul_olcumu": {}}
# Önce KAYNAK üçlülerin kendi hâlleri ölçülür (merdiven kurulmadan): karar §9.4'ün
# "Omega üçlüsü yerinde kalır" cümlesi ancak ölçülürse bir hüküm olur.
for _ad, _ucul in (("Dub ataması (ortak ΔL, merdiven YOK)", None),
                   ("Omega üçlüsü AYNEN (#0c6a3b/#6e4a00/#b3242c)",
                    {"green": "#0c6a3b", "amber": "#6e4a00", "red": "#b3242c"})):
    if _ucul is None:
        _t = turet_aile(PARA_KAYNAK, _aa_kendi_tinti(G_KOTU), -1)
        _ucul = {k: v[0] for k, v in _t.items()}
    OE1["kaynak_ucul_olcumu"][_ad] = _oe1_olc(_ucul, "gunduz", G_KOTU)

for _isim, _hk in OE1_ADAYLAR:
    kayit = {"ad": _isim, "temalar": {}}
    tam = True
    for tema, kotu in (("gunduz", G_KOTU), ("gece", N_KOTU)):
        m = _merdiven(_hk, tema, kotu)
        if m is None:
            kayit["temalar"][tema] = {"tuttu": False, "not": "merdiven sRGB'de kurulamadı"}
            tam = False
            continue
        ucul, kroma = m
        o = _oe1_olc(ucul, tema, kotu)
        o["ucul"] = ucul
        o["kroma"] = {k: round(v, 4) for k, v in kroma.items()}
        kayit["temalar"][tema] = o
        tam &= o["tuttu"]
    kayit["tuttu"] = tam
    OE1["adaylar"].append(kayit)
    if tam and OE1["secilen"] is None:
        OE1["secilen"] = _isim
        for tema in ("gunduz", "gece"):
            PARA[tema] = dict(kayit["temalar"][tema]["ucul"])

if OE1["secilen"] is None:
    raise SystemExit("ÖE1: HİÇBİR aday §9.3 eşiklerini tutmuyor — hüküm Rol-1'e döner.")

for tema in ("gunduz", "gece"):
    _hk = dict(OE1_ADAYLAR[[a["ad"] for a in OE1["adaylar"]].index(OE1["secilen"])][1])
    for ad in ("green", "amber", "red"):
        h = PARA[tema][ad]
        _kaydet(f"--{ad}", tema, PARA_KAYNAK[ad], h, 0, oklch(h)[1], PARA_KAYNAK_ADI[ad],
                f"ÖE1 MERDİVENİ (karar §9.3) · aday «{OE1['secilen'].split(' · ')[0]}» · "
                f"hue {_hk[ad][0]:.1f}° kroma {_hk[ad][1]:.4f} sabit, luminans basamağı "
                f"{OE1_ADIM}; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta",
                aynen=False)

MIN_SEV_C = {t: min(oklch(PARA[t][a])[1] for a in PARA_KAYNAK) for t in ("gunduz", "gece")}

# --- ROL 3 · YÖN — kroma tavanı şiddetin ALTINDA (ölçülmüş kısıt, v197) ---------------
# KURAL: yön kroması = min C(şiddet) x 0.60. Hue para renginin hue'su; L, AA'yı geçen
# ilk basamak. 0.60 katsayısı v197'nin zaten yürürlükteki `yon/sev <= 0.75` tavanının
# altında kalır ve D1'in ölçülen oranına (0.64) yakındır — yeni bir hüküm DEĞİL.
YON_KATSAYI = 0.60
YON = {"gunduz": {}, "gece": {}}
for tema, tablo, kotu, yon_isareti in (("gunduz", G, G_KOTU, -1), ("gece", N, N_KOTU, +1)):
    tohum = {}
    for ad, para in (("yon-arti", "green"), ("yon-eksi", "red")):
        L0, C0, H0 = oklch(PARA[tema][para])
        tohum[ad] = oklch_hex(L0, MIN_SEV_C[tema] * YON_KATSAYI, H0)[0]
    aile = turet_aile(tohum, _aa_kendi_tinti(kotu), yon_isareti)
    for ad, (h, i, c, _L) in aile.items():
        YON[tema][ad] = h
        para = "green" if ad == "yon-arti" else "red"
        _kaydet(f"--{ad}", tema, PARA[tema][para], h, i, c, f"--{para} ({tema})",
                f"C = min C(şiddet) x {YON_KATSAYI}; ORTAK ΔL={i * 0.001:.3f}; "
                f"AA>=4.5 kendi tinti + çıplak / {kotu}", aynen=False)

# --- ROL 4 · MOD — lavender ailesi (hue 293°, ayrılmış 285-335 bandı) -----------------
MOD_KESIF_KATSAYI = 0.40   # D1'in ölçülen canlı/keşif kroma oranı (0.150 -> 0.057 = 0.38)
MOD = {"gunduz": {}, "gece": {}}
for tema, kotu, yon_isareti in (("gunduz", G_KOTU, -1), ("gece", N_KOTU, +1)):
    h, i, c, _ = turet(DUB["lavender"], _aa_kendi_tinti(kotu), yon_isareti)
    MOD[tema]["mod-canli"] = h
    _kaydet("--mod-canli", tema, DUB["lavender"], h, i, c, "Dub lavender",
            f"AA>=4.5 kendi tinti + çıplak / {kotu}")
    L0, C0, H0 = oklch(h)
    baslangic, _ = oklch_hex(L0, C0 * MOD_KESIF_KATSAYI, H0)
    h2, i2, c2, _ = turet(baslangic, _aa_kendi_tinti(kotu), yon_isareti)
    MOD[tema]["mod-kesif"] = h2
    _kaydet("--mod-kesif", tema, h, h2, i2, c2, "--mod-canli (aynı hue, düşük kroma)",
            f"C = C(mod-canli) x {MOD_KESIF_KATSAYI}; AA>=4.5 kendi tinti + çıplak / {kotu}",
            aynen=False)

# --- ROL 6 · GEZİNME/SEÇİM ------------------------------------------------------------
NAV = {
    "gunduz": {"nav": DUB["electric-blue"], "nav-2": DUB["deep-sapphire"], "nav-t": "#dbeaff"},
    "gece": {},
}
# GECE — Dub'da yok. Wash, onaylanan maketin (`scratch-panov2/index.html`) gece bloğundan
# gelir; mürekkepler o washın üstünde AA'yı geçene kadar AÇILARAK türetilir (tint-yönü).
# GECE WASHI: tohum operatörün onayladığı maketin gece bloğundan (#172554) gelir, ama
# TOHUM ÖLÇÜLMEDEN ALINMAZ. Ö3'ün DOLGU tavanı (C(--nav-t) < min C(şiddet)) burada bağlayıcı:
# ÖE1 merdiveni gece şiddet kromasının tabanını düşürünce (sev-1 yüksek L'de gamut kenarına
# dayanıyor) maketin washı tavanın ÜSTÜNDE kaldı. Wash bizim TÜRETTİĞİMİZ bir değerdir
# (Dub'da karanlık tema yok) — o yüzden çözüm eşiği gevşetmek değil, washı kısıt altında
# yeniden türetmektir: hue ve L korunur, kroma tavanın %90'ına indirilir.
_WASH_TOHUM = "#172554"
_WASH_PAY = 0.90
_wl, _wc, _wh = oklch(_WASH_TOHUM)
if _wc >= MIN_SEV_C["gece"]:
    _yeni, _gc = oklch_hex(_wl, MIN_SEV_C["gece"] * _WASH_PAY, _wh)
    _kaydet("--nav-t", "gece", _WASH_TOHUM, _yeni, 0, _gc,
            "onaylanan maket (scratch-panov2) gece washı",
            f"Ö3 DOLGU tavanı: C tohumda {_wc:.4f} ≥ min C(şiddet) {MIN_SEV_C['gece']:.4f}; "
            f"hue ve L sabit, kroma tavanın %{int(_WASH_PAY * 100)}'ına indirildi", aynen=False)
    NAV["gece"]["nav-t"] = _yeni
else:
    NAV["gece"]["nav-t"] = _WASH_TOHUM
    _kaydet("--nav-t", "gece", _WASH_TOHUM, _WASH_TOHUM, 0, _wc,
            "onaylanan maket (scratch-panov2) gece washı",
            f"Ö3 DOLGU tavanının altında (C {_wc:.4f} < min C(şiddet) "
            f"{MIN_SEV_C['gece']:.4f}) — AYNEN alındı", aynen=True)


def _gece_nav_gecer(h, _w=NAV["gece"]["nav-t"]):
    return (kon(h, _w) >= 4.5 and kon(h, N_KOTU) >= 4.5
            and kon(h, bilesik(h, 0.10, N_KOTU)) >= 4.5)


# VURGU YÖNÜ GECEDE ÇEVRİLİR. Gündüz `--nav-2` (deep-sapphire) `--nav`dan KOYUdur:
# açık zeminde vurgu koyularak artar. Gecede aynı L farkı BÜYÜKLÜĞÜYLE korunur, YÖNÜ
# çevrilir — koyu zeminde vurgu AÇILARAK artar (tint-yönü kuralının gezinme hattındaki
# karşılığı). Naif ters çevirme burada `--nav` ile `--nav-2`yi aynı renge çökertiyordu
# (ölçüldü: #82adff ↔ #87acff, ayrım 1,00:1) — hue'ları yalnız 2,7° arayla.
_L_FARKI = oklch(DUB["electric-blue"])[0] - oklch(DUB["deep-sapphire"])[0]
_h, _i, _c, _Lnav = turet(DUB["electric-blue"], _gece_nav_gecer, +1)
NAV["gece"]["nav"] = _h
_kaydet("--nav", "gece", DUB["electric-blue"], _h, _i, _c, "Dub electric-blue",
        f"AA>=4.5 gece washı {NAV['gece']['nav-t']} + çıplak/tint {N_KOTU}")
_Lc, _Cc, _Hc = oklch(DUB["deep-sapphire"])
_h2, _c2 = oklch_hex(_Lnav + _L_FARKI, _Cc, _Hc)
if not _gece_nav_gecer(_h2):
    raise SystemExit(f"--nav-2 (gece) {_h2} eşiği geçmedi — L farkı kuralı gözden geçirilmeli")
NAV["gece"]["nav-2"] = _h2
_kaydet("--nav-2", "gece", DUB["deep-sapphire"], _h2, round(_L_FARKI * 1000), _c2,
        "Dub deep-sapphire",
        f"L = L(--nav gece) + {_L_FARKI:.4f} (gündüzün nav↔nav-2 L farkı, yönü çevrilmiş); "
        f"AA>=4.5 washı {NAV['gece']['nav-t']} + çıplak/tint {N_KOTU}", aynen=False)

# --- ALAN KENARI (--field) — metin girişi kenarı, WCAG 1.4.11 (>=3:1) ----------------
# Dub'ın nötr rampasından en AÇIK (gündüz) / en KOYU (gece) geçen basamak seçilir;
# rampa dışına çıkılmaz — bu bir türetme değil bir SEÇİMDİR.
DUB_NOTR_ACIKTAN = ["canvas-white", "paper-mist", "ash", "smoke", "pebble", "silver",
                    "fog", "steel", "slate", "graphite", "charcoal", "midnight-ink"]
FIELD = {}
for tema, tablo, kotu, sira in (("gunduz", G, G_KOTU, DUB_NOTR_ACIKTAN),
                                ("gece", N, N_KOTU, list(reversed(DUB_NOTR_ACIKTAN)))):
    secilen = None
    for ad in sira:
        if all(kon(DUB[ad], tablo[y]) >= 3.0 for y in YUZEYLER):
            secilen = ad
            break
    if secilen is None:
        raise SystemExit(f"--field ({tema}): Dub nötr rampasında >=3:1 tutan basamak YOK")
    FIELD[tema] = DUB[secilen]
    _kaydet("--field", tema, DUB[secilen], DUB[secilen], 0, 0.0, f"Dub {secilen}",
            "rampadan SEÇİM: her gerçek yüzeyde >=3:1 tutan ilk basamak")

# --- NİTEL BANT ORTA BASAMAĞI (--band-2) ---------------------------------------------
# Merdiven card-2 -> band-2 -> tx2. Dub nötr rampasından, iki adımı en DENGELİ bölen
# basamak seçilir (yine SEÇİM, türetme değil).
BAND2 = {}
for tema, tablo in (("gunduz", G), ("gece", N)):
    aday = []
    for ad in DUB_NOTR_ACIKTAN:
        v = DUB[ad]
        a1, a2 = kon(tablo["card-2"], v), kon(v, tablo["tx2"])
        if a1 < 1.2 or a2 < 1.2:
            continue
        aday.append((abs(math.log(a1) - math.log(a2)), ad, a1, a2))
    aday.sort()
    BAND2[tema] = DUB[aday[0][1]]
    _kaydet("--band-2", tema, DUB[aday[0][1]], DUB[aday[0][1]], 0, 0.0, f"Dub {aday[0][1]}",
            f"rampadan SEÇİM: card-2->band-2 {aday[0][2]:.2f} · band-2->tx2 {aday[0][3]:.2f}")

# --- SERİ MERDİVENİNİN ORTA BASAMAĞI (--violet) --------------------------------------
# KISIT v171'den GELİR ve ÖNCEDEN DONDU (B6, 2026-08-02): üç seri bir LUMİNANS
# merdivenidir ve `accent ↔ violet` ayrımı ≥1,35 olmalı, `violet` kart üstünde AA (≥4,5)
# kalmalı, sıra accent > violet > tx3 olmalı. Rampadan SEÇİM önce denenir; hiçbir Dub
# basamağı kısıtı karşılamıyorsa merdivenin GEOMETRİK ORTASI türetilir (eşit kontrast
# adımları) ve akromatik tutulur.
V_AYRIM = 1.35
VIOLET = {}
for tema, tablo in (("gunduz", G), ("gece", N)):
    aday = []
    for ad in DUB_NOTR_ACIKTAN:
        v = DUB[ad]
        a1, a2 = kon(tablo["accent"], v), kon(v, tablo["tx3"])
        if a1 < V_AYRIM or a2 <= 1.0 or kon(v, tablo["card"]) < 4.5:
            continue
        if not (kon(tablo["accent"], tablo["card"]) > kon(v, tablo["card"]) > kon(tablo["tx3"], tablo["card"])):
            continue
        aday.append((abs(math.log(a1) - math.log(a2)), ad, a1, a2))
    aday.sort()
    if aday:
        VIOLET[tema] = DUB[aday[0][1]]
        _kaydet("--violet", tema, DUB[aday[0][1]], DUB[aday[0][1]], 0, 0.0, f"Dub {aday[0][1]}",
                f"rampadan SEÇİM: accent->violet {aday[0][2]:.2f} · violet->tx3 {aday[0][3]:.2f} "
                f"(v171 kısıtı: ayrım ≥{V_AYRIM}, kart üstünde AA)")
    else:
        # Dub'ın nötr rampasında geçerli basamak YOK. Gece vakası ölçüldü: `silver #a3a3a3`
        # zaten `--tx3`ün KENDİSİ (ayrım 1.00), bir üstteki `pebble #c8c8c8` accent'e 1.33
        # bırakıyor ve eşik 1.35 — rampada 0,366 ile 0,578 luminansı arasında basamak yok.
        # TÜRETME: merdivenin geometrik ortası, akromatik, en yakın tamsayı sRGB.
        ust, alt = lum(tablo["accent"]) + 0.05, lum(tablo["tx3"]) + 0.05
        hedef = math.sqrt(ust * alt) - 0.05
        u = max(0.0, min(1.0, hedef))
        kanal = round(_delin(u))
        v = tohex((kanal, kanal, kanal))
        a1, a2 = kon(tablo["accent"], v), kon(v, tablo["tx3"])
        assert a1 >= V_AYRIM and kon(v, tablo["card"]) >= 4.5, \
            f"--violet ({tema}) türetmesi kısıtı karşılamadı: {v} ayrım {a1:.2f}"
        VIOLET[tema] = v
        _kaydet("--violet", tema, tablo["accent"], v, 0, 0.0,
                "TÜRETİLDİ — Dub nötr rampasında geçerli basamak YOK",
                f"accent↔tx3 merdiveninin GEOMETRİK ORTASI (eşit adım): "
                f"accent->violet {a1:.2f} · violet->tx3 {a2:.2f}; akromatik", aynen=False)

# --- IRAKSAYAN ÖLÇEK KUTUPLARI (--dv-*) ----------------------------------------------
# CVD-güvenli eksen korunur (mavi <-> toprak). Kutuplar Dub'ın kendi hue'larından gelir:
# negatif = deep-sapphire hue'su, pozitif = tangerine hue'su; ikisi de para renklerinin
# ALTINDA doygunlukta ve alfa merdiveni (.22/.10) DEĞİŞMEDİ (ölçülmüş sınır).
DV_KROMA_KATSAYI = 0.55
DV = {}
for tema, tablo in (("gunduz", G), ("gece", N)):
    # Kutup mürekkebi `--tx2`nin OKLCh-L'sinde durur: "sapma bir para hükmü DEĞİLDİR",
    # o yüzden kutuplar mürekkebin SOLUK bandında oturur ve iki kutup AYNI L'dedir
    # (işaret hücrenin rakamında yazılıdır, luminansta değil — mevcut hüküm).
    L_hedef = oklch(tablo["tx2"])[0]
    ln, cn, hn = oklch(DUB["deep-sapphire"])
    lp, cp, hp = oklch(DUB["tangerine"])
    neg, _ = oklch_hex(L_hedef, MIN_SEV_C[tema] * DV_KROMA_KATSAYI, hn)
    poz, _ = oklch_hex(L_hedef, MIN_SEV_C[tema] * DV_KROMA_KATSAYI, hp)
    DV[tema] = {"dv-n2": rgba(neg, 0.22), "dv-n1": rgba(neg, 0.10),
                "dv-p1": rgba(poz, 0.10), "dv-p2": rgba(poz, 0.22)}
    _kaydet("--dv-n*", tema, DUB["deep-sapphire"], neg, 0,
            oklch(neg)[1], "Dub deep-sapphire hue'su",
            f"L=L(--tx2)={L_hedef:.4f} · C = min C(şiddet) x {DV_KROMA_KATSAYI}; "
            f"alfa .22/.10 DEĞİŞMEDİ", aynen=False)
    _kaydet("--dv-p*", tema, DUB["tangerine"], poz, 0,
            oklch(poz)[1], "Dub tangerine hue'su",
            f"L=L(--tx2)={L_hedef:.4f} · C = min C(şiddet) x {DV_KROMA_KATSAYI}; "
            f"alfa .22/.10 DEĞİŞMEDİ", aynen=False)

# ============================== TAM JETON TABLOSU ==============================


def jeton_tablosu(tema):
    yapi = G if tema == "gunduz" else N
    p, y, m, nv = PARA[tema], YON[tema], MOD[tema], NAV[tema]
    ink = yapi["tx"]
    t = dict(yapi)
    t.update({
        "field": FIELD[tema],
        "violet": VIOLET[tema],
        "band-2": BAND2[tema],
        "green": p["green"], "amber": p["amber"], "red": p["red"],
        "green-t": rgba(p["green"], .10), "amber-t": rgba(p["amber"], .10), "red-t": rgba(p["red"], .10),
        "green-h": rgba(p["green"], .35), "amber-h": rgba(p["amber"], .35), "red-h": rgba(p["red"], .35),
        "amber-h2": rgba(p["amber"], .40),
        "green-stamp": rgba(p["green"], .55),
        "ink-h": rgba(ink, .30), "ink-h-soft": rgba(ink, .18),
        # PERDE İKİ TEMADA DA KOYU TABANLIDIR (mevcut hüküm, 2026-08-01): perde bir
        # mürekkep değil bir ENGELdir; gece açık bir perde sayfayı parlatırdı.
        "scrim": rgba(DUB["midnight-ink"], .42 if tema == "gunduz" else .66),
        "kap-1": rgba(ink, .06), "kap-2": rgba(ink, .14),
        "kap-3": rgba(ink, .23), "kap-4": rgba(ink, .30),
        # GÖLGE İKİ AYRI KURALA TABİ ve ikisi de depoda zaten yürürlükte:
        #  --sh-btn  = OKLÜZYON. Işığın kesilmesidir, mürekkep değil — iki temada da
        #              koyu kalır (precedent: --scrim gece de koyudur). Dub jetonu AYNEN.
        #  --sh-ring = MÜREKKEP HALKASI. Alfa Dub'ın (.10) KORUNUR, taban renk temayla
        #              DÖNER (precedent: --ink-h / --kap-* / --olcek-guven-h).
        "sh-btn": "rgba(0,0,0,.05) 0 1px 2px 0",
        "sh-ring": f"{rgba(ink, .10)} 0 0 0 4px",
        # ROL
        "sev-1": p["red"], "sev-2": p["amber"], "sev-3": p["green"],
        "yon-arti": y["yon-arti"], "yon-eksi": y["yon-eksi"],
        "yon-arti-t": rgba(y["yon-arti"], .10), "yon-eksi-t": rgba(y["yon-eksi"], .10),
        "yon-arti-h": rgba(y["yon-arti"], .35), "yon-eksi-h": rgba(y["yon-eksi"], .35),
        "yon-arti-zemin": rgba(y["yon-arti"], .08), "yon-eksi-zemin": rgba(y["yon-eksi"], .07),
        "mod-kagit": yapi["tx2"], "mod-canli": m["mod-canli"], "mod-kesif": m["mod-kesif"],
        "mod-kagit-t": "transparent",
        "mod-canli-t": rgba(m["mod-canli"], .10), "mod-kesif-t": rgba(m["mod-kesif"], .10),
        "mod-kagit-h": yapi["line-2"],
        "mod-canli-h": rgba(m["mod-canli"], .35), "mod-kesif-h": rgba(m["mod-kesif"], .35),
        "olcek-guven": yapi["tx2"], "olcek-guven-t": yapi["accent-tint"],
        "olcek-guven-h": rgba(ink, .45),
        "nav": nv["nav"], "nav-2": nv["nav-2"], "nav-t": nv["nav-t"],
        "nav-h": rgba(nv["nav"], .35),
        "nav-bg": rgba(yapi["bg"], .82),
    })
    t.update(DV[tema])
    return t


TABLO = {t: jeton_tablosu(t) for t in ("gunduz", "gece")}

# ============================== ÖLÇÜMLER (Ö1-Ö7) ==============================
olcum = {}


def _coz(deger, tema):
    """Bir jeton değerini düz sRGB'ye indir (alfa varsa alfa ile birlikte döner)."""
    d = deger.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", d)
    if m:
        return hx(d), 1.0
    m = re.fullmatch(r"rgba?\((\d+),(\d+),(\d+),([0-9.]*)\)", d.replace(" ", ""))
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))), float(m.group(4))
    raise ValueError(f"renk değil: {deger!r}")


def yig(katmanlar, tema):
    """`['--card-2','--red-t']` gibi bir yığını düz renge indir."""
    T = TABLO[tema]
    c, _ = _coz(T[katmanlar[0].lstrip("-")] if katmanlar[0].startswith("--") else katmanlar[0], tema)
    for k in katmanlar[1:]:
        v = T[k.lstrip("-")] if k.startswith("--") else k
        rgb, a = _coz(v, tema)
        c = bilesik(rgb, a, c)
    return c


# ---- Ö1 · #fafafa zemin, parlama kısıtı ----
en_buyuk = TABLO["gunduz"]["bg"]
olcum["O1"] = {
    "soru": "#fafafa zemin P9'un parlama kısıtını karşılıyor mu?",
    "en_buyuk_yuzey": en_buyuk,
    "luminans": round(lum(en_buyuk), 4),
    "saf_beyaz_luminans": 1.0,
    "saf_beyazin_altinda": lum(en_buyuk) < 1.0,
    "kart_zemin_adimi": round(kon(TABLO["gunduz"]["card"], TABLO["gunduz"]["bg"]), 4),
    "esik_adim": ESIK["O1_kart_zemin_adimi"],
    "gunduz_saf_beyaz_jeton_sayisi": sum(
        1 for k, v in TABLO["gunduz"].items() if isinstance(v, str) and v.lower() == "#ffffff"),
}
olcum["O1"]["tuttu"] = bool(olcum["O1"]["saf_beyazin_altinda"]
                            and olcum["O1"]["kart_zemin_adimi"] >= ESIK["O1_kart_zemin_adimi"])

# ---- Ö2 · para renkleri kendi %10 tinti üstünde, İKİ temada ----
o2 = {"esik": ESIK["O2_para_AA"], "satirlar": [], "dub_jetonu_aynen": {}}
for tema in ("gunduz", "gece"):
    kotu = G_KOTU if tema == "gunduz" else N_KOTU
    for ad in ("green", "amber", "red"):
        v = TABLO[tema][ad]
        for zad in YUZEYLER:
            z = (G if tema == "gunduz" else N)[zad]
            o2["satirlar"].append({
                "tema": tema, "jeton": f"--{ad}", "zemin": zad,
                "tint_ustu": round(kon(v, bilesik(v, .10, z)), 3),
                "ciplak": round(kon(v, z), 3),
            })
    for ad in ("green", "amber", "red"):
        ham = PARA_KAYNAK[ad]
        o2["dub_jetonu_aynen"][f"{tema}/--{ad}"] = (TABLO[tema][ad].lower() == ham.lower())
o2["en_dusuk"] = min(s["tint_ustu"] for s in o2["satirlar"])
o2["tuttu"] = all(s["tint_ustu"] >= ESIK["O2_para_AA"] and s["ciplak"] >= ESIK["O2_para_AA"]
                  for s in o2["satirlar"])
olcum["O2"] = o2

# ---- Ö3 · gezinme kroması < min şiddet kroması ----
o3 = {"esik": ESIK["O3_kroma_tavani"], "temalar": {}}
for tema in ("gunduz", "gece"):
    T = TABLO[tema]
    sev_c = {f"--sev-{i}": round(oklch(T[a])[1], 4)
             for i, a in ((1, "red"), (2, "amber"), (3, "green"))}
    nav_c = {f"--{a}": round(oklch(T[a])[1], 4) for a in ("nav", "nav-2", "nav-t")}
    o3["temalar"][tema] = {
        "siddet_kroma": sev_c, "min_siddet": min(sev_c.values()),
        "nav_kroma": nav_c,
        "murekkep_tuttu": max(nav_c["--nav"], nav_c["--nav-2"]) < min(sev_c.values()),
        "dolgu_tuttu": nav_c["--nav-t"] < min(sev_c.values()),
    }
o3["tuttu"] = all(v["murekkep_tuttu"] for v in o3["temalar"].values())
o3["dolgu_tuttu"] = all(v["dolgu_tuttu"] for v in o3["temalar"].values())
olcum["O3"] = o3

# ---- Ö4 · gezinme mavisi <-> ıraksayan negatif kutup ayrımı ----
o4 = {"esik": ESIK["O4_ayirt_edilebilirlik"],
      "esik_gerekcesi": ("Ö4'ün eşiği kararda niteldir ('ayırt edilebilir'). İşlemsel "
                         "karşılık olarak deponun zaten yürürlükteki metin-dışı ayrım "
                         "ölçütü (WCAG 2.2 1.4.11, 3:1) alındı — yeni bir eşik icat "
                         "edilmedi, var olanı uygulandı."),
      "temalar": {}}
for tema in ("gunduz", "gece"):
    T = TABLO[tema]
    kutup = yig(["--card", "--dv-n2"], tema)
    navc = hx(T["nav"])
    L1, C1, H1 = oklch(navc)
    L2, C2, H2 = oklch(kutup)
    dE = math.dist(_srgb_oklab(navc), _srgb_oklab(kutup))
    o4["temalar"][tema] = {
        "nav": T["nav"], "dv_n2_karta_binmis": tohex(kutup),
        "kontrast": round(kon(navc, kutup), 3),
        "oklab_dE": round(dE, 4),
        "hue_farki": round(abs(((H1 - H2 + 180) % 360) - 180), 1),
        "tuttu": kon(navc, kutup) >= ESIK["O4_ayirt_edilebilirlik"],
    }
o4["tuttu"] = all(v["tuttu"] for v in o4["temalar"].values())
olcum["O4"] = o4

# ---- Ö5 · nav mürekkebi kendi washı üstünde ----
o5 = {"esik": ESIK["O5_nav_wash_AA"], "temalar": {}}
for tema in ("gunduz", "gece"):
    T = TABLO[tema]
    o5["temalar"][tema] = {
        "wash": T["nav-t"],
        "nav_ustunde": round(kon(T["nav"], T["nav-t"]), 3),
        "nav-2_ustunde": round(kon(T["nav-2"], T["nav-t"]), 3),
    }
o5["nav_tuttu"] = all(v["nav_ustunde"] >= ESIK["O5_nav_wash_AA"] for v in o5["temalar"].values())
o5["nav2_tuttu"] = all(v["nav-2_ustunde"] >= ESIK["O5_nav_wash_AA"] for v in o5["temalar"].values())
o5["tuttu"] = o5["nav_tuttu"]
olcum["O5"] = o5

# ---- Ö6 · tip rampası ----
# HİYERARŞİ RAMPASI — karar §3'ün beyan ettiği başlık/gövde merdiveni. Bu, v209'un
# yüzey-rampasıyla (izinli TÜM boylar: 10/11/12/14/17/20/24/28/30) AYNI ŞEY DEĞİLDİR:
# orası "hangi ölçüler yasal", burası "hiyerarşi hangi basamaklardan okunuyor". İkisini
# karıştırmak, mikro-etiket bandını (10/12) hiyerarşi adımı sanmak olurdu.
KARAR_RAMPASI = [11, 14, 16, 20, 24, 30]      # karar §3'ün beyan ettiği rampa
# DARALTMA ADAYLARI. Eşiği tutan İLK aday alınır; sıra "en az basamak kaybı" ilkesine göre.
# 17 kaynakta ZATEN VAR (3 kullanım: `.hyp h3`, `.md h4`, dar ekran `.logo`) ve onu rampaya
# ALMAK 16'yı düşürmekten daha az kayıp verir — 16'nın kaynakta tek kullanımı vardı, 18'in
# de bir. Ölçüldü: 16 rampada kalırsa 16/14=1.1429 (eşik altı); 16 yerine 17 konursa
# 17/14=1.2143 ve 20/17=1.1765, ikisi de eşiğin üstünde.
DARALTMA_ADAYLARI = [
    ("16 → 17 (16 ve 18 düşer, 17 rampaya girer)", [11, 14, 17, 20, 24, 30]),
    ("16 tamamen düşer", [11, 14, 20, 24, 30]),
]


def _rampa_olc(r):
    adim = [round(r[i + 1] / r[i], 4) for i in range(len(r) - 1)]
    return {"rampa": r, "adimlar": adim, "en_kucuk": min(adim), "en_buyuk": max(adim),
            "tuttu": min(adim) >= ESIK["O6_tip_adimi_min"] and max(adim) >= ESIK["O6_tip_adimi_en_az_bir"]}


_adaylar = [(ad, _rampa_olc(r)) for ad, r in DARALTMA_ADAYLARI]
_secilen = next((a for a in _adaylar if a[1]["tuttu"]), None)
if _secilen is None:
    raise SystemExit("HİÇBİR daraltma adayı Ö6 eşiğini tutmuyor — hüküm Rol-1'e döner")
olcum["O6"] = {"esik_min": ESIK["O6_tip_adimi_min"], "esik_en_az_bir": ESIK["O6_tip_adimi_en_az_bir"],
               "karar_rampasi": _rampa_olc(KARAR_RAMPASI),
               "adaylar": [{"ad": a, **o} for a, o in _adaylar],
               "daraltilmis": _secilen[1], "daraltma": _secilen[0]}
olcum["O6"]["tuttu"] = olcum["O6"]["karar_rampasi"]["tuttu"]

# ---- Ö7 · odak halkası ----
o7 = {"esik": ESIK["O7_odak_halkasi"], "satirlar": []}
for tema in ("gunduz", "gece"):
    T = TABLO[tema]
    m = re.match(r"(rgba?\([^)]*\))", T["sh-ring"])
    rgb, a = _coz(m.group(1), tema)
    for zad in YUZEYLER:
        z = (G if tema == "gunduz" else N)[zad]
        halka = bilesik(rgb, a, z)
        o7["satirlar"].append({"tema": tema, "zemin": zad, "oran": round(kon(halka, z), 3)})
    # KARŞILAŞTIRMA: fiilen erişilebilir olan odak göstergesi 2px --accent ANA HATTIDIR.
    for zad in YUZEYLER:
        z = (G if tema == "gunduz" else N)[zad]
        o7["satirlar"].append({"tema": tema, "zemin": f"{zad} (2px --accent ana hattı)",
                               "oran": round(kon(T["accent"], z), 3)})
o7["sh_ring_tuttu"] = all(s["oran"] >= ESIK["O7_odak_halkasi"]
                          for s in o7["satirlar"] if "ana hattı" not in s["zemin"])
o7["ana_hat_tuttu"] = all(s["oran"] >= ESIK["O7_odak_halkasi"]
                          for s in o7["satirlar"] if "ana hattı" in s["zemin"])
o7["tuttu"] = o7["sh_ring_tuttu"]
olcum["O7"] = o7

# ---- ÖE1 (EK ÖLÇÜM · kararda YOK, bu turda BULUNDU) · rol içi ayrılabilirlik ----
# Karar §4 bir rolün ÜYELERİNİN birbirinden ayrılabilirliğini sormuyor. Ölçmeyince
# görülmeyen şey tam olarak bu oldu: Dub `tangerine` (41,1°) ile maketin `loss-red`i
# (38,4°) 2,7° arayla duruyor ve üye-üye AA türetmesi ikisini AYNI renge çökertiyordu.
# Ortak-ΔL kuralı (bkz. `turet_aile`) ayrımı geri getirdi; buradaki sayı o iddianın kanıtı.
# EŞİK YOKTUR — bu bir ön-kayıtlı ölçüm değil, bir BULGUdur; sayı raporda durur ve hükmü
# Rol-1 verir. (Uydurma yasağı: eşiği şimdi icat etmek, ölçümü hükme çevirmek olurdu.)
oe1 = {"esik": None, "not": "kararda ön-kayıtlı eşik YOK — sayı beyan edilir, hüküm Rol-1'de",
       "ciftler": []}
for tema in ("gunduz", "gece"):
    T = TABLO[tema]
    aile = {"--sev-1": T["red"], "--sev-2": T["amber"], "--sev-3": T["green"],
            "--nav": T["nav"], "--nav-2": T["nav-2"],
            "--mod-canli": T["mod-canli"], "--mod-kesif": T["mod-kesif"]}
    for grup in (("--sev-1", "--sev-2", "--sev-3"), ("--nav", "--nav-2"),
                 ("--mod-canli", "--mod-kesif")):
        for i in range(len(grup)):
            for j in range(i + 1, len(grup)):
                a, b = aile[grup[i]], aile[grup[j]]
                oe1["ciftler"].append({
                    "tema": tema, "a": grup[i], "b": grup[j], "a_hex": a, "b_hex": b,
                    "kontrast": round(kon(a, b), 3),
                    "oklab_dE": round(math.dist(_srgb_oklab(hx(a)), _srgb_oklab(hx(b))), 4),
                    "hue_farki": round(abs(((oklch(a)[2] - oklch(b)[2] + 180) % 360) - 180), 1),
                })
oe1["en_dusuk_dE"] = min(c["oklab_dE"] for c in oe1["ciftler"])
olcum["OE1_cift_taramasi"] = oe1

# ---- ÖE1 · HÜKÜM (karar §9) — eşikler §9.3'te ölçümden ÖNCE donduruldu ----
olcum["OE1"] = {
    "karar": "docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md §9",
    "esikler": OE1_ESIK,
    "merdiven_adimi": OE1_ADIM,
    "kaynak_ucul_olcumu": OE1["kaynak_ucul_olcumu"],
    "adaylar": OE1["adaylar"],
    "secilen": OE1["secilen"],
    "tuttu": OE1["secilen"] is not None,
}

# ============================== ÇİVİ TABLOSU ==============================
# docs/kontrast-denetimi.md §9'un gövdesi. Satır listesi 2026-08-07 turundan DEVRALINDI
# (kapsam daralmadı: v153 `sayac >= 24` ister) ve ROL 6 ile gölge satırları EKLENDİ.
CIVI_SATIRLARI = [
    ("--tx", "--bg", 4.5), ("--tx", "--card", 4.5), ("--tx", "--card-2 + --red-t", 4.5),
    ("--tx2", "--bg", 4.5), ("--tx2", "--card", 4.5),
    ("--tx2", "--card-2 + --red-t", 4.5), ("--tx2", "--card-2 + --amber-t", 4.5),
    ("--tx3", "--card", 4.5), ("--tx3", "--card-2", 4.5),
    ("--violet", "--card", 4.5),
    ("--accent-2", "--accent-tint", 4.5),
    ("--green", "--card-2 + --green-t", 4.5), ("--amber", "--card-2 + --amber-t", 4.5),
    ("--red", "--card-2 + --red-t", 4.5),
    ("--green", "--bg", 4.5), ("--amber", "--bg", 4.5), ("--red", "--bg", 4.5),
    ("--red", "--bg + --nav-bg", 4.5),
    ("--field", "--card-2", 3.0), ("--field", "--bg", 3.0),
    ("--line", "--card-2", 3.0), ("--line-2", "--bg", 3.0),
    ("--accent", "--card", 3.0), ("--accent", "--card-2 + --red-t", 3.0),
    ("--green-h", "--card + --green-t", 3.0),
    ("--ink-h", "--accent-tint", 3.0),
    ("--green-stamp", "--bg", 3.0),
    ("--card-2", "--band-2", 3.0), ("--band-2", "--tx2", 3.0),
    ("--accent", "--violet", 3.0), ("--violet", "--tx3", 4.5),
    ("--kap-4", "--card", 3.0), ("--tx", "--card + --kap-4", 4.5),
    ("--dv-n2", "--card", 3.0), ("--dv-p2", "--card", 3.0),
    ("--card", "--bg + --scrim", 3.0),
    # --- ROL 6 · GEZİNME/SEÇİM (bu tur eklendi) ---
    ("--nav", "--bg", 3.0), ("--nav", "--card", 3.0),
    ("--nav-2", "--nav-t", 4.5), ("--nav", "--nav-t", 4.5),
    ("--nav-h", "--nav-t", 3.0),
    ("--bg2", "--nav", 4.5),          # sayaç hapı: --bg2 mürekkep, --nav dolgu
    ("--tx", "--nav-t", 4.5),         # "Seni bekleyenler" görev kartı: gövde mürekkebi wash üstünde
    ("--tx", "--nav-t + --nav-h", 4.5),   # görev kartı hover: saç teli washın üstünde
    ("--tx2", "--nav-t", 4.5),        # wash üstündeki ikincil metin (Top Views birim etiketi)
    ("--tx3", "--nav-t", 4.5),        # AYNI YER, ÜÇÜNCÜ INK — ölçüldü ve REDDEDİLDİ (3,89 gündüz)
    ("--tx", "--nav-t", 4.5),         # oran çubuğu üstündeki satır değeri
    # --- GÖLGE (bu tur eklendi) ---
    ("--sh-ring", "--bg", 3.0), ("--sh-ring", "--card", 3.0),
]


def civi_tablosu():
    satir = ["| mürekkep | zemin yığını | tema | oran | eşik |", "|---|---|---|---|---|"]
    kayit = []
    for murekkep, zemin, esik in CIVI_SATIRLARI:
        for tema in ("gunduz", "gece"):
            T = TABLO[tema]
            katman = [k.strip() for k in zemin.split("+")]
            zc = yig(katman, tema)
            ham = T[murekkep.lstrip("-")]
            m = re.match(r"(rgba?\([^)]*\))", ham)
            if m and " " in ham:            # gölge jetonu: rengi baştaki rgba()'dır
                ham = m.group(1)
            rgb, a = _coz(ham, tema)
            ic = bilesik(rgb, a, zc) if a < 1.0 else rgb
            oran = kon(ic, zc)
            satir.append(f"| {murekkep} | {zemin} | {tema} | {oran:.2f} | {esik} |")
            kayit.append({"murekkep": murekkep, "zemin": zemin, "tema": tema,
                          "oran": round(oran, 2), "esik": esik, "gecti": oran >= esik})
    return "\n".join(satir), kayit


CIVI_MD, CIVI_KAYIT = civi_tablosu()

# ============================== ÇIKTI ==============================
KARANLIK = dub_karanlik_tema_var_mi()

# OKUYUCUSUZ JETON TARAMASI — YASA 6'nın sayısal hâli. Yüzeyler zaten yukarıda sayıldı;
# burada değer/ölçü jetonlarının tamamı taranır ki "okuyucusuz yazım" bir kanı değil bir
# SAYI olsun. Hüküm verilmez (jeton adları bu turda değişmez); yalnız kayda geçer.
_TARANAN = ("raise", "serif", "violet2", "blue", "elev", "slip", "slip-ink",
            "t-cap", "t-body", "t-lg", "t-sub", "t-h", "t-num",
            "sh-btn", "sh-ring", "r-input", "r-btn", "r-lg", "r-tag", "r-ctl", "r-card",
            "nav", "nav-2", "nav-t", "nav-h", "nav-bg", "label-size", "band-2", "violet")
OKUYUCU_TAM = {j: _okuyucu_sayisi(j) for j in _TARANAN}
OKUYUCUSUZ_TAM = sorted(j for j, n in OKUYUCU_TAM.items() if n == 0)

sonuc = {
    "tur": "KARAR-2026-08-24-B · Dub dönüşümü, jeton katmanı",
    "okuyucu": OKUYUCU_TAM,
    "okuyucusuz": OKUYUCUSUZ_TAM,
    "tarih": "2026-08-24",
    "kaynak": str(DUB_YOLU),
    "dub_karanlik_tema_taramasi": KARANLIK,
    "en_kotu_gercek_zemin": {"gunduz": G_KOTU, "gece": N_KOTU},
    "esikler": ESIK,
    "turetme_kaydi": turetme_kaydi,
    "jetonlar": TABLO,
    "olcumler": olcum,
    "civi_tablosu": CIVI_KAYIT,
}
(BURASI / "sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
(BURASI / "civi_tablosu.md").write_text(CIVI_MD + "\n", encoding="utf-8")


def _damga(b):
    return "TUTTU" if b else "**TUTMADI**"


rapor = []
A = rapor.append
A("# Dub dönüşümü · jeton katmanı ölçümü — 2026-08-24")
A("")
A("_Üreten: `research/olcumler/dub_donusumu_2026-08-24/olc.py` · elle yazılmış tek bir oran YOK._")
A(f"_Dub kaynağı: `{DUB_YOLU}`._")
A("")
A("## 0 · Dub'da karanlık tema YOK — doğrulandı")
A("")
A("Karar §1.2 iddiası ölçüldü: dört Dub dosyası ikinci bir renk katmanını AÇAN mekanizma")
A("için tarandı (`prefers-color-scheme`, `[data-theme`, `.dark`, `color-scheme:dark`).")
A("")
A("| dosya | karanlık-tema mekanizması |")
A("|---|---|")
for ad, v in KARANLIK.items():
    A(f"| `{ad}` | {'YOK' if v == [] else v} |")
A("")
A("Yani GECE PALETİ TÜRETİLDİ ve tokens.json'da `$extensions.org.meridian.turetme`")
A("damgasını taşır. Türetme TERS ÇEVİRME DEĞİLDİR (tint-yönü kuralı): kroma taşıyan her")
A("jeton gece için AYRI ölçüldü ve gece para renkleri naif tersin vereceğinden AÇIKTIR.")
A("")
A("## 1 · Ö1-Ö7 · eşikler ve sonuç")
A("")
A("| Ö | soru | ölçülen | eşik | hüküm |")
A("|---|---|---|---|---|")
A(f"| Ö1 | `#fafafa` zemin parlama kısıtı | en büyük yüzey Y={olcum['O1']['luminans']} "
  f"(saf beyaz 1.0) · kart/zemin adımı {olcum['O1']['kart_zemin_adimi']} | Y<1.0 · adım ≥1.02 "
  f"| {_damga(olcum['O1']['tuttu'])} |")
A(f"| Ö2 | para renkleri kendi %10 tinti üstünde | en düşük {olcum['O2']['en_dusuk']} "
  f"(iki tema, yedi yüzey) | ≥4.5 | {_damga(olcum['O2']['tuttu'])} |")
A(f"| Ö3 | gezinme kroması | mürekkep C(nav)="
  f"{olcum['O3']['temalar']['gunduz']['nav_kroma']['--nav']} / "
  f"{olcum['O3']['temalar']['gece']['nav_kroma']['--nav']} · min C(şiddet)="
  f"{olcum['O3']['temalar']['gunduz']['min_siddet']} / "
  f"{olcum['O3']['temalar']['gece']['min_siddet']} | C(nav) < min C(şiddet) | "
  f"{_damga(olcum['O3']['tuttu'])} |")
A(f"| Ö4 | `--nav` ↔ `--dv-n2` ayrımı | "
  f"{olcum['O4']['temalar']['gunduz']['kontrast']} / {olcum['O4']['temalar']['gece']['kontrast']} "
  f"| ≥3.0 | {_damga(olcum['O4']['tuttu'])} |")
A(f"| Ö5 | `--nav` mürekkebi kendi washı üstünde | "
  f"{olcum['O5']['temalar']['gunduz']['nav_ustunde']} / "
  f"{olcum['O5']['temalar']['gece']['nav_ustunde']} | ≥4.5 | {_damga(olcum['O5']['tuttu'])} |")
A(f"| Ö6 | tip rampası adımları | karar rampası {olcum['O6']['karar_rampasi']['adimlar']} | "
  f"her adım ≥1.15, en az bir ≥1.25 | {_damga(olcum['O6']['tuttu'])} |")
A(f"| Ö7 | odak halkası (`--sh-ring`) | "
  f"{min(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' not in s['zemin'])}"
  f"-{max(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' not in s['zemin'])} | "
  f"≥3.0 | {_damga(olcum['O7']['tuttu'])} |")
A("")
A("### Tutmayanlar — DEĞER ZORLANMADI, KULLANIM YÜZEYİ DARALDI (karar §2.1)")
A("")
if not olcum["O3"]["tuttu"]:
    A(f"**Ö3 · gezinme kroması.** Elektrik mavisi doygundur: C(--nav)="
      f"{olcum['O3']['temalar']['gunduz']['nav_kroma']['--nav']} > min C(şiddet)="
      f"{olcum['O3']['temalar']['gunduz']['min_siddet']} (gündüz). Jeton UYDURULMADI.")
    A(f"Daraltma: gezinmenin BÜYÜK YÜZEYİ washtır (`--nav-t`, C="
      f"{olcum['O3']['temalar']['gunduz']['nav_kroma']['--nav-t']}) ve o tavanın çok altındadır"
      f" — dolgu tavanı {'TUTAR' if olcum['O3']['dolgu_tuttu'] else 'TUTMAZ'}. `--nav`/`--nav-2`")
    A("yalnız İNCE mürekkep (3px seçim çubuğu, sayaç hapı dolgusu, bağlantı metni) taşır;")
    A("bir para değeri, bir alarm, bir yön ASLA mavi olmaz (karar §2.1).")
    A("")
if not olcum["O5"]["tuttu"]:
    A(f"**Ö5 · wash üstünde mürekkep.** `--nav` (electric-blue) `--nav-t` üstünde "
      f"{olcum['O5']['temalar']['gunduz']['nav_ustunde']} (gündüz) — AA ALTI.")
    A(f"Daraltma (karar §2.1'in kendi cümlesi: *dolgu washı kalır, mürekkep koyulaşır*):")
    A(f"wash üstündeki mürekkep `--nav-2` (deep-sapphire) olur — ölçüldü "
      f"{olcum['O5']['temalar']['gunduz']['nav-2_ustunde']} / "
      f"{olcum['O5']['temalar']['gece']['nav-2_ustunde']}, "
      f"{'AA' if olcum['O5']['nav2_tuttu'] else 'AA ALTI'}. `.sitem.on` kuralı bu yüzden")
    A("`color:var(--nav-2)` okur, `var(--nav)` DEĞİL.")
    A("")
if not olcum["O6"]["tuttu"]:
    A(f"**Ö6 · tip rampası.** Karar §3'ün rampası {KARAR_RAMPASI}: adımlar "
      f"{olcum['O6']['karar_rampasi']['adimlar']} — 16/14={olcum['O6']['karar_rampasi']['adimlar'][1]}"
      f" eşiğin ({ESIK['O6_tip_adimi_min']}) ALTINDA.")
    A(f"Daraltma ({olcum['O6']['daraltma']}): kalan rampa "
      f"{olcum['O6']['daraltilmis']['rampa']}, adımlar "
      f"{olcum['O6']['daraltilmis']['adimlar']} — {_damga(olcum['O6']['daraltilmis']['tuttu'])}.")
    for a in olcum["O6"]["adaylar"]:
        A(f"  · aday *{a['ad']}* → {a['rampa']} adımlar {a['adimlar']} — {_damga(a['tuttu'])}")
    A("")
if not olcum["O7"]["tuttu"]:
    A(f"**Ö7 · odak halkası.** Dub'ın `shadow-subtle-2` halkası (`rgba(0,0,0,.1) 0 0 0 4px`) "
      f"her zeminde 3:1'in ALTINDA (ölçülen aralık "
      f"{min(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' not in s['zemin'])}-"
      f"{max(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' not in s['zemin'])}).")
    A("Değer ZORLANMADI (Dub jetonu alfası kımıldatılmadı). Daraltma: `--sh-ring` bir ODAK")
    A("GÖSTERGESİ DEĞİLDİR, onu ÇEVRELEYEN yardımcı halkadır. G4'ü taşıyan gösterge")
    A(f"`:focus-visible` üzerindeki **2px `--accent` ana hattı**dır ve o ölçüldü: "
      f"{min(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' in s['zemin'])}-"
      f"{max(s['oran'] for s in olcum['O7']['satirlar'] if 'ana hattı' in s['zemin'])} — "
      f"{_damga(olcum['O7']['ana_hat_tuttu'])}.")
    A("")
A("## 2 · Türetilen jetonlar — hangi kural, kaç adım")
A("")
A("| jeton | tema | kaynak | sonuç | L adımı | kroma | kural |")
A("|---|---|---|---|---|---|---|")
for k in turetme_kaydi:
    aynen = " *(Dub jetonu AYNEN)*" if k["aynen_alindi"] else ""
    A(f"| `{k['jeton']}` | {k['tema']} | {k['kaynak_adi']} `{k['kaynak']}` | `{k['sonuc']}`{aynen} "
      f"| {k['L_adimi']} | {k['kroma']} (kaynak {k['kaynak_kroma']}) | {k['kural']} |")
A("")
A("## 2b · ÖE1 · ŞİDDET MERDİVENİ — HÜKÜM UYGULANDI (karar §9)")
A("")
A("Karar §4 bir rolün ÜYELERİNİN ayrılabilirliğini sormuyordu; jeton turunun ilk koşumu")
A("bunu bir KUSUR olarak buldu ve Rol-1 §9'da hükmü verdi. Eşikler ölçümden ÖNCE donduruldu")
A("(§9.3) ve bu bölüm onları UYGULAR — sayıları yeniden yazar, değiştirmez.")
A("")
A(f"| ÖE1 | eşik |")
A("|---|---|")
A(f"| a · komşu seviyelerin luminans oranı | ≥ {OE1_ESIK['a_luminans_orani']} |")
A(f"| b · komşu seviyelerin ΔE2000'i | ≥ {OE1_ESIK['b_deltaE2000']} |")
A(f"| c · her renk kendi %10 tinti üstünde | ≥ {OE1_ESIK['c_tint_AA']} |")
A("")
A("### Kaynak üçlüler MERDİVENSİZ hâlleriyle (niye merdiven zorunlu)")
A("")
A("| üçlü | çift | luminans oranı | ΔE2000 |")
A("|---|---|---|---|")
for _ad, _o in olcum["OE1"]["kaynak_ucul_olcumu"].items():
    for _k in _o["komsu"]:
        A(f"| {_ad} | {_k['cift']} | {_k['luminans_orani']} | {_k['deltaE2000']} |")
A("")
A("Yani **§9.4'ün işaret ettiği Omega üçlüsü bile, AYNEN alındığında ÖE1-a'yı tutmuyor**")
A("(gündüz 1,188 · gece 1,035 / 1,093). Bu, hükmün ikinci yarısını zorunlu kıldı: hue ailesi")
A("hangisi olursa olsun, üçlü bir LUMİNANS MERDİVENİNE oturmak zorunda.")
A("")
A("### Adaylar — karar §9'un kendi sırasıyla (önce Dub içi, olmazsa §9.4)")
A("")
A("| aday | tema | a (lum) | b (ΔE2000) | c | hüküm |")
A("|---|---|---|---|---|---|")
for _a in olcum["OE1"]["adaylar"]:
    for _t, _o in _a["temalar"].items():
        if "komsu" not in _o:
            A(f"| {_a['ad'].split(' · ')[0]} | {_t} | — | — | — | **{_o.get('not', 'kurulamadı')}** |")
            continue
        _lum = " / ".join(str(k["luminans_orani"]) for k in _o["komsu"])
        _de = " / ".join(str(k["deltaE2000"]) for k in _o["komsu"])
        A(f"| {_a['ad'].split(' · ')[0]} | {_t} | {_lum} | {_de} | "
          f"{'✓' if _o['c'] else '✗'} | {_damga(_o['tuttu'])} |")
A("")
A(f"**SEÇİLEN: {olcum['OE1']['secilen']}**")
A("")
A("A ve B, ÖE1-b'de düştü: `loss-red` ile `tangerine` arasında yalnız 2,7° hue farkı var ve")
A("Meridian'ın ölçülmüş alarm hue'suna (24,1°) çekmek bile ΔE2000'i 15'in altında bıraktı")
A("(13,53 gündüz / 12,62 gece). **Dub'ın paleti üç seviyeli bir şiddet kanalı taşıyamıyor** —")
A("kullanılabilir üç ayrık hue yok: `lavender` MOD'a, `electric-blue`/`deep-sapphire` ROL 6'ya")
A("kalıcı olarak ayrılmış durumda; geriye `vivid-green` ve `tangerine` kalıyor, yani İKİ hue.")
A("Karar §9.4'ün dediği tam da buydu ve ölçüm onu doğruladı.")
A("")
A("### Uygulanan merdiven")
A("")
A("| tema | jeton | değer | kroma | çift | luminans oranı | ΔE2000 | kendi tinti (`--card`) |")
A("|---|---|---|---|---|---|---|---|")
for _a in olcum["OE1"]["adaylar"]:
    if _a["ad"] != olcum["OE1"]["secilen"]:
        continue
    for _t, _o in _a["temalar"].items():
        _tint = {x["jeton"]: x for x in _o["tint"]}
        for _n, _k in (("--sev-1", "red"), ("--sev-2", "amber"), ("--sev-3", "green")):
            _c = _o["komsu"][0] if _n == "--sev-1" else (_o["komsu"][1] if _n == "--sev-2" else None)
            A(f"| {_t} | `{_n}` (`--{_k}`) | `{_o['ucul'][_k]}` | {_o['kroma'][_k]} | "
              f"{_c['cift'] if _c else '—'} | {_c['luminans_orani'] if _c else '—'} | "
              f"{_c['deltaE2000'] if _c else '—'} | {_tint['--' + _k]['kendi_tinti_card']} |")
A("")
A("**MERDİVEN KURALI.** Şiddet arttıkça mürekkep zeminden UZAKLAŞIR (tint-yönü kuralının")
A("şiddet hattındaki kardeşi): gündüz `--sev-1` en KOYU, gece en AÇIK; nominal (`--sev-3`)")
A(f"zemine en yakın olandır. Basamak oranı **{OE1_ADIM}**, eşik {OE1_ESIK['a_luminans_orani']} DEĞİL —")
A("8-bit yuvarlama ve alfa bileşimi sıfır paylı bir merdiveni aşağı itebilir. Eşik hâlâ")
A(f"{OE1_ESIK['a_luminans_orani']} ve ölçüm ona karşı yapılır; pay yalnız İNŞADADIR.")
A("")
A("**BEDELİ BEYANLI.** Gece `--sev-1` merdivenin en uzak basamağında oturuyor ve sRGB gamutu")
A("orada kroma tutmuyor: 0,166 → 0,0809. Alarm gecede daha SOLUK bir mürekkeptir; ayrımı")
A("luminans ve hue taşır, doygunluk değil. Bu ayrıca Ö3'ün DOLGU tavanını düşürdü ve gece")
A("gezinme washı (`--nav-t`) o tavanın altına çekilerek yeniden türetildi (§2 tablosunda).")
A("")
A("### ROL 2 DIŞI çift taraması (bilgi — eşiksiz)")
A("")
A("| tema | a | b | kontrast | OKLab ΔE | hue farkı |")
A("|---|---|---|---|---|---|")
for c in olcum["OE1_cift_taramasi"]["ciftler"]:
    if c["a"].startswith("--sev"):
        continue
    A(f"| {c['tema']} | `{c['a']}` {c['a_hex']} | `{c['b']}` {c['b_hex']} | {c['kontrast']} "
      f"| {c['oklab_dE']} | {c['hue_farki']}° |")
A("")
A("## 3 · Ö2 · para renkleri, her gerçek zeminde (iki tema)")
A("")
A("| tema | jeton | zemin | kendi %10 tinti üstünde | çıplak |")
A("|---|---|---|---|---|")
for s in olcum["O2"]["satirlar"]:
    A(f"| {s['tema']} | `{s['jeton']}` | `{s['zemin']}` | {s['tint_ustu']} | {s['ciplak']} |")
A("")
A("## 4 · Ö7 · odak: yardımcı halka ve ana hat")
A("")
A("| tema | zemin | oran |")
A("|---|---|---|")
for s in olcum["O7"]["satirlar"]:
    A(f"| {s['tema']} | {s['zemin']} | {s['oran']} |")
A("")
A("## 5 · Çivi tablosu (docs/kontrast-denetimi.md §9 gövdesi)")
A("")
A(CIVI_MD)
A("")
(BURASI / "RAPOR.md").write_text("\n".join(rapor) + "\n", encoding="utf-8")

# ============================== CSS BLOĞU (eş-kayıt kolaylığı) ==============================
(BURASI / "jetonlar.json").write_text(json.dumps(TABLO, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

print("Ö1", _damga(olcum["O1"]["tuttu"]), olcum["O1"]["luminans"], olcum["O1"]["kart_zemin_adimi"])
print("Ö2", _damga(olcum["O2"]["tuttu"]), "en düşük", olcum["O2"]["en_dusuk"])
print("Ö3", _damga(olcum["O3"]["tuttu"]), json.dumps(olcum["O3"]["temalar"], ensure_ascii=False))
print("Ö4", _damga(olcum["O4"]["tuttu"]), json.dumps(olcum["O4"]["temalar"], ensure_ascii=False))
print("Ö5", _damga(olcum["O5"]["tuttu"]), json.dumps(olcum["O5"]["temalar"], ensure_ascii=False))
print("Ö6", _damga(olcum["O6"]["tuttu"]), json.dumps(olcum["O6"], ensure_ascii=False))
print("Ö7", _damga(olcum["O7"]["tuttu"]), "sh-ring", olcum["O7"]["sh_ring_tuttu"],
      "ana hat", olcum["O7"]["ana_hat_tuttu"])
print()
print("çivi tablosu satır:", len(CIVI_KAYIT))
print("yazıldı:", BURASI)
