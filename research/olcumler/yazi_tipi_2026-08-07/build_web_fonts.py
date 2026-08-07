#!/usr/bin/env python3
"""D4 — Recursive'i DAĞITILABİLİR iki woff2'ye indirger. Tek çalıştırmayla yeniden üretilebilir.

NEDEN BU DOSYA VAR (ve neden ölçüm turunun `instance_recursive.py`si yetmedi): ölçüm turu
kesitleri `updateFontNames=False` ile üretti, yani iki dosya da `name` tablosunda
`Recursive Sans Linear Light` yazıyordu (nameID 1/3/4/6 birebir aynı, postscript adı dahil).
Bir yüz kendini YANLIŞ tanıtıyordu: `MONO=1` ile sabitlenmiş kesit kendine "Sans" diyordu.
`@font-face` ailesi CSS'te açıkça verildiği için tarayıcı çözümü bundan ETKİLENMİYOR (D4'te
tarayıcıda ölçüldü, `tarayici/isim_cakismasi.json`), ama ikili kendi hakkında yanlış beyan
taşıdığı sürece hata "işe yaramayan bir yerde" bekler: `local()` yedeği, sistem kurulumu,
devtools, font-manager. Bu betik adları AYRIŞTIRIR ve kaydı ölçülebilir bırakır.

ÜÇ ADIM
  1. INSTANCE — `Recursive-VF.ttf`ten MONO/CASL/slnt/CRSV sabitlenir, `wght` CANLI kalır.
  2. RENAME   — iki kesit ayrı ailelere: "Recursive Sans" / "Recursive Mono".
  3. SUBSET   — ölçülmüş kod-noktası kümesi + YALIN özellik kümesi → woff2.

LİSANS: Recursive SIL OFL 1.1'dir ve telif kaydında REZERVE FONT ADI YOKTUR (ölçüldü:
nameID 0 = "Copyright 2019 The Recursive Project Authors (github.com/arrowtype/recursive)" —
"with Reserved Font Name" ibaresi geçmiyor). RFN olsaydı türetilmiş yüze "Recursive" adını
vermek lisans ihlali olurdu; olmadığı için ad korunuyor ve türetme `meridian/web/fonts/OFL.txt`
ile birlikte dağıtılıyor.

KOŞTURMA (fontTools 4.63 + brotli gerekir; depo .venv'inde YOK, tek kullanımlık ortam):
    uv venv /tmp/fontenv --python 3.12
    uv pip install --python /tmp/fontenv/bin/python "fonttools[woff]==4.63.0"
    /tmp/fontenv/bin/python research/olcumler/yazi_tipi_2026-08-07/build_web_fonts.py
"""
from __future__ import annotations

import json
import pathlib
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BURASI = pathlib.Path(__file__).resolve().parent
DEPO = BURASI.parents[2]
KAYNAK = BURASI / "fonts" / "Recursive-VF.ttf"
HEDEF = DEPO / "meridian" / "web" / "fonts"

# ---------------------------------------------------------------------------------------------
# KESİTLER. `MONO` ekseni 0 = sans, 1 = mono — kardeş aile değil, AYNI dosyanın iki kesiti
# (ölçüm raporu §3.5). `CASL 0` = Linear (nötr, "Casual" değil), `slnt 0` = dik, `CRSV 0` = dik
# italik-olmayan `a`/`g`. `wght` SABİTLENMEZ: değişken kalır, CSS ağırlığı eksene sürer.
# ---------------------------------------------------------------------------------------------
# AĞIRLIK EKSENİ 400-700'E DARALTILDI — ÖLÇÜMLE, TAHMİNLE DEĞİL.
# `meridian/web/*.{html,js}` içindeki 174 `font-weight` bildiriminin tamamı dört değerden biri:
# 400 (63), 700 (43), 600 (38), 500 (30). 300 ya da 800+ isteyen TEK bir kural yok, ve
# DESIGN.md'nin ağırlık disiplini zaten "başlık 500, rakam 400, etiket 700" diyor.
# ÖLÇÜLEN BEDEL/KAZANÇ (aynı kod-noktası kümesiyle, woff2):
#     wght 300-1000 →  117,9 KB        wght 400-700 →  79,4 KB        fark −38,5 KB
# Daraltmanın bozulma biçimi güvenlidir: aralık dışı bir `font-weight` KIRPILIR (300 → 400),
# yani yanlış yüz değil, en yakın ağırlık çizilir. Yan kazanç: Recursive'in `wght` VARSAYILANI
# 300'dür (ölçüm raporu §7 madde 5, bir tuzak kalemi olarak devredilmişti) — 400 tabanlı bir
# eksende varsayılan 400'e oturur, yani `@font-face` bildirimi unutulsa bile yüz ince açılmaz.
WGHT_ARALIK = (400, 700)

KESITLER = [
    {
        "cikti": "recursive-sans-vf.woff2",
        "yer": {"MONO": 0.0, "CASL": 0.0, "slnt": 0.0, "CRSV": 0.0, "wght": WGHT_ARALIK},
        "aile": "Recursive Sans",
        "ps": "RecursiveSans-Regular",
    },
    {
        "cikti": "recursive-mono-vf.woff2",
        "yer": {"MONO": 1.0, "CASL": 0.0, "slnt": 0.0, "CRSV": 0.0, "wght": WGHT_ARALIK},
        "aile": "Recursive Mono",
        "ps": "RecursiveMono-Regular",
    },
]

# ---------------------------------------------------------------------------------------------
# KOD NOKTALARI. Varsayılmadı — üç yüzey + `app.js`/`landing.js`/`workflow.js`/`palette.js` +
# `meridian/api.py` taranıp kullanılan her karakter toplandı (bkz. `olcum_kapsami()` altta),
# sonra ÜÇ güvenlik kümesiyle birleştirildi:
#   * Latin-1 (U+0020-00FF)     — panoya dışarıdan düşen isim/metin (broker, sembol, hata metni)
#   * Türkçe + Batı Avrupa      — Latin Extended-A'nın kullanılan kesiti
#   * birleşen aksan işaretleri — `mark`/`mkmk` özelliklerinin bağlanacağı işaretler
# EMOJİ BİLEREK DIŞARIDA: Recursive'de yok, sistem emoji yüzüne düşer (ÖLÇÜLEMEDİ ≠ 0 değil —
# ölçüldü: `cmap`te yoklar, subset'e sokmak dosyayı büyütmez ama listeyi yalan söyler).
# ---------------------------------------------------------------------------------------------
GUVENLIK_KUMESI = (
    list(range(0x0020, 0x0100))                        # Latin-1 (ASCII + ek)
    + [0x0131, 0x0130, 0x011E, 0x011F, 0x015E, 0x015F]  # ı İ Ğ ğ Ş ş  — TÜRKÇE ÇEKİRDEK
    + [0x0152, 0x0153, 0x0160, 0x0161, 0x0178, 0x017D, 0x017E]  # Œ œ Š š Ÿ Ž ž (Batı Avrupa)
    + [0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306,  # birleşen aksanlar (mark/mkmk)
       0x0307, 0x0308, 0x030A, 0x030B, 0x030C, 0x0327, 0x0328]
    + [0x0394, 0x03A3, 0x03C3, 0x03C4]                 # Δ Σ σ τ — panoda sembol olarak geçiyor
    + [0x2010, 0x2011, 0x2013, 0x2014, 0x2018, 0x2019,  # tipografik noktalama
       0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021,
       0x2022, 0x2026, 0x2030, 0x2039, 0x203A, 0x2044]
    + [0x20AC, 0x20BA]                                 # € ₺
    + [0x2190, 0x2191, 0x2192, 0x2193, 0x2194, 0x2197, 0x21D2]  # oklar
    + [0x2212, 0x221A, 0x222A, 0x2248, 0x2260, 0x2264, 0x2265]  # matematik
    + [0x2303, 0x2304, 0x2318, 0x21E7, 0x2325, 0x23CE]          # klavye (⌘ ⇧ ⌥ ⏎ …)
    + [0x25A0, 0x25A1, 0x25AA, 0x25AB, 0x25B2, 0x25B3, 0x25B6,  # geometrik işaretler
       0x25B8, 0x25BC, 0x25BE, 0x25C6, 0x25C7, 0x25C8, 0x25CB,
       0x25CF, 0x25D0]
    + [0x2713, 0x2715, 0x2717, 0x27E8, 0x27E9]         # ✓ ✕ ✗ ⟨ ⟩
)

# YALIN ÖZELLİK KÜMESİ — ölçüm raporu §3.7. Bunun dışındaki her şey (ss01…, afrc, pnum
# varyantları, dlig kod-ligatürleri) dosyayı İKİ KATINA çıkarıyor ve panoda hiç okunmuyor.
# `tnum`/`zero` Recursive'de ATIL (rapor §3.3/§3.4) ama listede kalıyorlar: maliyeti sıfır
# (özellik yoksa subset onları düşürür) ve `ui-monospace` yedeğine düşüldüğünde CSS bildirimi
# hâlâ iş görüyor.
YALIN_OZELLIKLER = "ccmp,locl,kern,mark,mkmk,rlig,calt,tnum,zero,case"


def olcum_kapsami() -> set[int]:
    """Panonun GERÇEKTEN yazdığı karakter kümesi — kaynak dosyalardan okunur, varsayılmaz."""
    hedefler = sorted((DEPO / "meridian" / "web").glob("*.html"))
    hedefler += sorted((DEPO / "meridian" / "web").glob("*.js"))
    hedefler += [DEPO / "meridian" / "api.py"]
    cps: set[int] = set()
    for p in hedefler:
        if p.is_file():
            cps |= {ord(ch) for ch in p.read_text(encoding="utf-8", errors="replace")}
    return cps


def yeniden_adlandir(font: TTFont, aile: str, ps: str, surum: str) -> None:
    """`name` tablosunu TEK bir aileye sabitler.

    nameID 16/17 (typographic family/subfamily) SİLİNİR: OpenType, 16 == 1 ve 17 == 2 olduğunda
    ikisinin de yazılmamasını ister. Bırakılsalardı iki kesit `Recursive` altında yeniden
    BİRLEŞİRDİ — düzeltilen çakışmanın ta kendisi, bir alt kayıttan geri gelmiş hâli."""
    name = font["name"]
    for nid, deger in ((1, aile), (2, "Regular"), (3, f"{surum};MRDN;{ps}"),
                       (4, aile), (6, ps)):
        name.setName(deger, nid, 3, 1, 0x409)   # Windows / Unicode BMP / en-US
        name.setName(deger, nid, 1, 0, 0)       # Macintosh / Roman / English
    for nid in (16, 17, 18, 20, 21, 22, 25):
        name.removeNames(nameID=nid)


def gvar_tam_doldur(font: TTFont) -> None:
    """`gvar.variations` TEMBEL sözlüktür ve deltası olmayan glifi (ör. `space`) HİÇ taşımaz.

    fontTools 4.63'ün subset yolu (`_dict_subset`) her glif için anahtar bekler ve eksik
    anahtarda `KeyError: 'space'` ile düşer — ölçüldü, bu betiğin ilk koşusunda. Sözlük burada
    tam glif düzeniyle materyalize edilir; eksik olanlar BOŞ delta listesi alır, yani hiçbir
    şey uydurulmaz: "deltası yok" zaten boş listenin anlamıdır."""
    if "gvar" not in font:
        return
    gvar = font["gvar"]
    mevcut = dict(gvar.variations)
    gvar.variations = {g: mevcut.get(g, []) for g in font.getGlyphOrder()}


def kesit_uret(yer: dict, aile: str, ps: str) -> TTFont:
    font = TTFont(str(KAYNAK))
    surum = font["name"].getDebugName(5) or "Version 1.085"
    surum = surum.replace("Version ", "")
    font = instancer.instantiateVariableFont(font, yer, inplace=False, updateFontNames=False)
    gvar_tam_doldur(font)
    yeniden_adlandir(font, aile, ps, surum)
    return font


def main() -> int:
    if not KAYNAK.is_file():
        print(f"KAYNAK YOK: {KAYNAK}", file=sys.stderr)
        return 1
    HEDEF.mkdir(parents=True, exist_ok=True)

    kaynak_cmap = set(TTFont(str(KAYNAK)).getBestCmap())
    istenen = set(GUVENLIK_KUMESI) | {c for c in olcum_kapsami() if c >= 0x20}
    kapsanan = sorted(istenen & kaynak_cmap)
    kapsanmayan = sorted(istenen - kaynak_cmap)

    rapor: dict[str, object] = {
        "kaynak": KAYNAK.name,
        "istenen_kod_noktasi": len(istenen),
        "fontta_var": len(kapsanan),
        # UYDURMA YASAĞI: "hepsi var" yazmak yerine olmayanlar TEK TEK sayılır. Beklenen
        # kalıntı emoji + fontun taşımadığı birkaç teknik işarettir; liste kayda geçer.
        "fontta_yok": [f"U+{c:04X}" for c in kapsanmayan],
        "yalin_ozellikler": YALIN_OZELLIKLER.split(","),
        "wght_aralik": list(WGHT_ARALIK),
        "kesitler": [],
    }

    for k in KESITLER:
        font = kesit_uret(k["yer"], k["aile"], k["ps"])
        opts = subset.Options()
        opts.layout_features = YALIN_OZELLIKLER.split(",")
        opts.flavor = "woff2"
        opts.desubroutinize = False
        opts.hinting = True
        opts.legacy_kern = False
        opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]   # telif + lisans BEYANI ikilide KALIR
        opts.name_legacy = True
        opts.notdef_outline = True
        opts.recalc_bounds = True
        opts.drop_tables += ["DSIG"]
        subsetter = subset.Subsetter(options=opts)
        subsetter.populate(unicodes=kapsanan)
        subsetter.subset(font)

        p = HEDEF / k["cikti"]
        font.flavor = "woff2"
        font.save(str(p))
        boyut = p.stat().st_size

        kontrol = TTFont(str(p))
        rapor["kesitler"].append({
            "dosya": k["cikti"],
            "bayt": boyut,
            "kb": round(boyut / 1024, 1),
            "nameID1": kontrol["name"].getDebugName(1),
            "nameID6": kontrol["name"].getDebugName(6),
            "nameID16": kontrol["name"].getDebugName(16),      # None OLMALI
            "fvar": {a.axisTag: [a.minValue, a.defaultValue, a.maxValue]
                     for a in kontrol["fvar"].axes} if "fvar" in kontrol else None,
            "glif": kontrol["maxp"].numGlyphs,
            "cmap": len(kontrol.getBestCmap()),
            "rakam_advance": sorted({kontrol["hmtx"][kontrol.getBestCmap()[0x30 + d]][0]
                                     for d in range(10)}),
            "usWeightClass": kontrol["OS/2"].usWeightClass,
            "sxHeight": kontrol["OS/2"].sxHeight,
            "sCapHeight": kontrol["OS/2"].sCapHeight,
            "unitsPerEm": kontrol["head"].unitsPerEm,
        })
        print(f"{k['cikti']}: {boyut} bayt ({boyut/1024:.1f} KB), "
              f"aile={kontrol['name'].getDebugName(1)!r}, ps={kontrol['name'].getDebugName(6)!r}")

    toplam = sum(x["bayt"] for x in rapor["kesitler"])
    rapor["toplam_bayt"] = toplam
    rapor["toplam_kb"] = round(toplam / 1024, 1)
    (BURASI / "web_fonts_build.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"TOPLAM {toplam} bayt ({toplam/1024:.1f} KB) → {HEDEF}")
    print(f"fontta olmayan istenen kod noktası: {len(kapsanmayan)} "
          f"(ilk 10: {[f'U+{c:04X}' for c in kapsanmayan[:10]]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
