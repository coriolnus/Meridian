#!/usr/bin/env python3
"""INTER + GEIST MONO KESİT BORUSU — 2026-08-07 borusunun UYARLANMIŞ KOPYASI.

KAYNAK: `research/olcumler/yazi_tipi_2026-08-07/build_web_fonts.py` (DONMUŞ KANIT, dokunulmadı).
Boru mantığı — instance → rename → subset → kayıt — bire bir korundu. Aşağıdaki liste
ORİJİNALE GÖRE NE DEĞİŞTİĞİNİN TAM DÖKÜMÜDÜR; listede olmayan her şey aynıdır.

════════════════════════════════════════════════════════════════════════════════════════
DEĞİŞİKLİK DÖKÜMÜ (1-9)
════════════════════════════════════════════════════════════════════════════════════════

[1] KAYNAK TEK DEĞİL, İKİ. Orijinalde tek `Recursive-VF.ttf` vardı ve ondan iki kesit
    (MONO=0 / MONO=1) çıkıyordu; burada İKİ AYRI DOSYA var ve her birinden BİR kesit çıkıyor.
    Bu yüzden `KESITLER` her girdiye kendi `kaynak` yolunu taşıyor. Sonucu: `fontta_var` ve
    `fontta_yok` artık kaynak-BAŞINA ölçülüyor (iki fontun cmap'i farklı), tek bir üst
    düzey sayı olamaz — bkz. [7].

[2] HEDEF DİZİN `meridian/web/fonts` DEĞİL, `…/yazi_tipi_2026-08-24/woff2/`.
    Bu bir ÖLÇÜM turudur, bir dağıtım değil. Canlı yüzleri değiştirme yetkisi bu ajanda yok;
    hükmü operatör verir. Orijinal betik doğrudan dağıtım dizinine yazıyordu.

[3] EKSEN SABİTLEME kaynak-başına. Recursive'in MONO/CASL/slnt/CRSV eksenleri burada YOK.
    · Inter      → `opsz` SABİTLENİR = 14.0. Ölçüldü: Inter'in `opsz` ekseni 14..32 ve
      VARSAYILANI 14 — yani 14'te sabitlemek görünümü DEĞİŞTİRMEZ, sadece ekseni kaldırır.
      14 aynı zamanda panonun metin boyu aralığının (10-14px) üst ucudur; "optik olarak küçük
      metin" ucu zaten burasıdır. `font-optical-sizing: auto` ile eksen canlı bırakılabilirdi;
      bırakılmadı çünkü orijinal borunun kuralı "wght DIŞINDA her eksen sabitlenir"dir ve
      minimum uyarlama emri bu kuralı korumayı gerektirir.
    · Geist Mono → sabitlenecek eksen YOK (tek eksen: `wght`).

[4] `wght` ARALIĞI (400, 700) DEVRALINDI, YENİDEN ÖLÇÜLMEDİ. Orijinaldeki 400-700 kararı
    `meridian/web/*.{html,js}` içindeki 174 `font-weight` bildiriminin sayımına dayanıyordu.
    O sayım BU TURDA TEKRARLANMADI (o dosyalarda şu anda başka ajanlar çalışıyor; sayı
    hareketli hedef). Aralık devralınan bir PARAMETREDİR, bu turun bir ölçümü değildir.
    ÖNEMLİ FARK: Recursive'in `wght` VARSAYILANI 300'dü (orijinal yorumdaki "tuzak kalemi");
    Inter ve Geist Mono'nun ikisinin de varsayılanı zaten 400'dür (ölçüldü, fvar dökümü).

[5] AD VERME. `yeniden_adlandir()` gövdesi aynı; verilen adlar farklı:
    Inter → aile "Inter", ps "Inter-Regular" (kaynakta nameID1 "Inter Variable" idi),
    Geist Mono → aile "Geist Mono", ps "GeistMono-Regular" (kaynakla zaten aynı).
    LİSANS KONTROLÜ (ad değiştirmenin ön koşulu): her iki yüz de SIL OFL 1.1'dir ve
    telif kayıtlarında REZERVE FONT ADI YOKTUR — ölçüldü:
      Inter      nameID0 = "Copyright 2016 The Inter Project Authors"
      Geist Mono nameID0 = "Copyright 2024 The Geist Project Authors (…geist-font.git)"
    İkisinde de "with Reserved Font Name" ibaresi geçmiyor (lisans dosyalarındaki tek
    "Reserved Font Name" geçişi OFL şablonunun TANIMLAR bölümüdür, bir ad rezervasyonu değil).
    RFN olsaydı türetilmiş yüze aynı adı vermek ihlal olurdu. Satoshi turunun aksine
    (ITF FFL §02 subsetting'i ADIYLA yasaklıyor) burada lisans engeli YOKTUR.

[6] KOD NOKTASI KÜMESİ: `GUVENLIK_KUMESI` ve `olcum_kapsami()` BİREBİR aynı (tek karakter
    değişmedi). AMA SONUÇ AYNI DEĞİL — ölçüldü: 08-07'de istenen küme 347 kod noktasıydı,
    bugünkü taramada 350. Fark taranan kaynak dosyaların 08-07'den beri değişmesindendir
    (ve şu anda da değişiyor: paralel ajanlar `index.html`/`app.js`/`api.py` üzerinde).
    UYDURMA YASAĞI GEREĞİ 347'ye ZORLANMADI: 08-07'nin tam kod-noktası listesi kayda
    geçmemiş (kayıtta yalnız fontta BULUNAMAYAN 87 tanesi var) ve git ile geri okumak bu
    ajana YASAK, yani o kümeyi yeniden kurmanın ölçülebilir bir yolu yok. Onun yerine bu
    turun kümesi TAM olarak `kanit/istenen_kod_noktalari.json`a yazılır ve sha256'sı kayda
    girer — bu koşu böylece hash ile yeniden doğrulanabilir olur.

[7] KAYIT ŞEMASI. Eski kayıt TEK kaynaklıydı, dolayısıyla `kaynak`/`istenen_kod_noktasi`/
    `fontta_var`/`fontta_yok` üst düzeydeydi. İki kaynakla bu alanların tek bir değeri
    OLAMAZ (iki font, iki farklı cmap). Çözüm: kayıt `yuzler: [...]` listesi tutar ve
    LİSTEDEKİ HER GİRDİ eski şemanın BİREBİR AYNI alanlarını taşır
    (kaynak · istenen_kod_noktasi · fontta_var · fontta_yok · yalin_ozellikler · wght_aralik ·
     kesitler[dosya,bayt,kb,nameID1,nameID6,nameID16,fvar,glif,cmap,rakam_advance,
     usWeightClass,sxHeight,sCapHeight,unitsPerEm] · toplam_bayt · toplam_kb).
    Alan adı ya da tipi DEĞİŞTİRİLMEDİ; yalnız bir sarmalayıcı eklendi.

[8] EKLENEN ALANLAR (eskisinden fazlası, hiçbiri eskisinin yerine geçmiyor):
    · her kesitte `sha256` — görevin açıkça istediği alan (eski kayıtta yoktu).
    · üst düzeyde `istenen_kume_sha256`, `taban_08_07` (karşılaştırma için), `butce` bloğu.

[9] KAYIT DOSYASI ADI aynı (`web_fonts_build.json`), yeri bu turun dizini.

════════════════════════════════════════════════════════════════════════════════════════
KOŞTURMA (fontTools 4.63 + brotli; depo .venv'inde YOK — tek kullanımlık ortam):
    uv venv /tmp/fontenv --python 3.12
    uv pip install --python /tmp/fontenv/bin/python "fonttools[woff]==4.63.0"
    /tmp/fontenv/bin/python research/olcumler/yazi_tipi_2026-08-24/kesit_uret.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BURASI = pathlib.Path(__file__).resolve().parent
DEPO = BURASI.parents[2]
KAYNAK_DIZIN = BURASI / "fonts"
HEDEF = BURASI / "woff2"           # [2] ASLA meridian/web/fonts DEĞİL
KANIT = BURASI / "kanit"

# [4] Devralınan parametre — bu turda yeniden ölçülmedi.
WGHT_ARALIK = (400, 700)

# [1][3][5] İki kaynak, her biri tek kesit.
KESITLER = [
    {
        "kaynak": KAYNAK_DIZIN / "Inter-VF.ttf",
        "cikti": "inter-vf.woff2",
        "sabit": {"opsz": 14.0},       # [3] varsayılan = eksen minimumu = 14, görünüm değişmez
        "aile": "Inter",
        "ps": "Inter-Regular",
    },
    {
        "kaynak": KAYNAK_DIZIN / "GeistMono-VF.ttf",
        "cikti": "geist-mono-vf.woff2",
        "sabit": {},                   # [3] tek eksen (wght) — sabitlenecek başka eksen yok
        "aile": "Geist Mono",
        "ps": "GeistMono-Regular",
    },
]

# ---------------------------------------------------------------------------------------------
# [6] KOD NOKTALARI — 08-07 borusundan BİREBİR kopyalandı, tek karakter değişmedi.
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

YALIN_OZELLIKLER = "ccmp,locl,kern,mark,mkmk,rlig,calt,tnum,zero,case"

# Türkçe çivisi — `tests/test_yazitipi_v201.py::test_TURKCE_glif_civisi` ile aynı 12 karakter.
TURKCE = {
    0x00C7: "Ç", 0x00E7: "ç", 0x011E: "Ğ", 0x011F: "ğ", 0x0130: "İ", 0x0131: "ı",
    0x00D6: "Ö", 0x00F6: "ö", 0x015E: "Ş", 0x015F: "ş", 0x00DC: "Ü", 0x00FC: "ü",
}

BUTCE_BAYT = 120 * 1024   # tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE
TABAN_08_07_BAYT = 81168  # Recursive Sans + Mono çifti (donmuş kayıt)


def olcum_kapsami() -> set[int]:
    """Panonun GERÇEKTEN yazdığı karakter kümesi — 08-07 borusundan BİREBİR."""
    hedefler = sorted((DEPO / "meridian" / "web").glob("*.html"))
    hedefler += sorted((DEPO / "meridian" / "web").glob("*.js"))
    hedefler += [DEPO / "meridian" / "api.py"]
    cps: set[int] = set()
    for p in hedefler:
        if p.is_file():
            cps |= {ord(ch) for ch in p.read_text(encoding="utf-8", errors="replace")}
    return cps


def yeniden_adlandir(font: TTFont, aile: str, ps: str, surum: str) -> None:
    """08-07 borusundan BİREBİR — nameID 1/2/3/4/6 yazılır, 16/17/18/20/21/22/25 silinir."""
    name = font["name"]
    for nid, deger in ((1, aile), (2, "Regular"), (3, f"{surum};MRDN;{ps}"),
                       (4, aile), (6, ps)):
        name.setName(deger, nid, 3, 1, 0x409)   # Windows / Unicode BMP / en-US
        name.setName(deger, nid, 1, 0, 0)       # Macintosh / Roman / English
    for nid in (16, 17, 18, 20, 21, 22, 25):
        name.removeNames(nameID=nid)


def gvar_tam_doldur(font: TTFont) -> None:
    """08-07 borusundan BİREBİR — `gvar.variations` tembel sözlüğü tam glif düzeniyle doldurur."""
    if "gvar" not in font:
        return
    gvar = font["gvar"]
    mevcut = dict(gvar.variations)
    gvar.variations = {g: mevcut.get(g, []) for g in font.getGlyphOrder()}


def kesit_uret(kaynak: pathlib.Path, sabit: dict, aile: str, ps: str) -> TTFont:
    font = TTFont(str(kaynak))
    surum = font["name"].getDebugName(5) or "Version 0.000"
    surum = surum.replace("Version ", "")
    yer = dict(sabit)
    yer["wght"] = WGHT_ARALIK
    font = instancer.instantiateVariableFont(font, yer, inplace=False, updateFontNames=False)
    gvar_tam_doldur(font)
    yeniden_adlandir(font, aile, ps, surum)
    return font


def sha256_dosya(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    eksik = [str(k["kaynak"]) for k in KESITLER if not k["kaynak"].is_file()]
    if eksik:
        print(f"KAYNAK YOK: {eksik}", file=sys.stderr)
        return 1
    HEDEF.mkdir(parents=True, exist_ok=True)
    KANIT.mkdir(parents=True, exist_ok=True)

    istenen = set(GUVENLIK_KUMESI) | {c for c in olcum_kapsami() if c >= 0x20}
    istenen_sirali = sorted(istenen)
    kume_metni = ",".join(f"{c:04X}" for c in istenen_sirali)
    kume_sha = hashlib.sha256(kume_metni.encode("utf-8")).hexdigest()
    # [6] Kümenin TAMAMI kayda geçer — 08-07'de geçmediği için o tur yeniden üretilemiyor.
    (KANIT / "istenen_kod_noktalari.json").write_text(
        json.dumps({"adet": len(istenen_sirali),
                    "sha256": kume_sha,
                    "kod_noktalari": [f"U+{c:04X}" for c in istenen_sirali]},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    yuzler = []
    for k in KESITLER:
        kaynak_cmap = set(TTFont(str(k["kaynak"])).getBestCmap())
        kapsanan = sorted(istenen & kaynak_cmap)
        kapsanmayan = sorted(istenen - kaynak_cmap)

        font = kesit_uret(k["kaynak"], k["sabit"], k["aile"], k["ps"])
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
        kkmap = kontrol.getBestCmap()
        kesit_kaydi = {
            "dosya": k["cikti"],
            "bayt": boyut,
            "kb": round(boyut / 1024, 1),
            "sha256": sha256_dosya(p),                     # [8] eski kayıtta YOKTU
            "nameID1": kontrol["name"].getDebugName(1),
            "nameID6": kontrol["name"].getDebugName(6),
            "nameID16": kontrol["name"].getDebugName(16),  # None OLMALI
            "fvar": {a.axisTag: [a.minValue, a.defaultValue, a.maxValue]
                     for a in kontrol["fvar"].axes} if "fvar" in kontrol else None,
            "glif": kontrol["maxp"].numGlyphs,
            "cmap": len(kkmap),
            "rakam_advance": sorted({kontrol["hmtx"][kkmap[0x30 + d]][0] for d in range(10)}),
            "usWeightClass": kontrol["OS/2"].usWeightClass,
            "sxHeight": getattr(kontrol["OS/2"], "sxHeight", None),
            "sCapHeight": getattr(kontrol["OS/2"], "sCapHeight", None),
            "unitsPerEm": kontrol["head"].unitsPerEm,
            # Türkçe civisi kesitin KENDİSİNDE doğrulanır (kaynak cmap'inde değil):
            "turkce_kesitte_eksik": [f"U+{cp:04X} {ch}" for cp, ch in TURKCE.items()
                                     if cp not in kkmap],
        }
        yuzler.append({
            "kaynak": k["kaynak"].name,
            "kaynak_sha256": sha256_dosya(k["kaynak"]),
            "sabitlenen_eksenler": {a: v for a, v in k["sabit"].items()},
            "istenen_kod_noktasi": len(istenen),
            "fontta_var": len(kapsanan),
            "fontta_yok": [f"U+{c:04X}" for c in kapsanmayan],
            "yalin_ozellikler": YALIN_OZELLIKLER.split(","),
            "wght_aralik": list(WGHT_ARALIK),
            "kesitler": [kesit_kaydi],
            "toplam_bayt": boyut,
            "toplam_kb": round(boyut / 1024, 1),
        })
        print(f"{k['cikti']}: {boyut} bayt ({boyut/1024:.1f} KB), "
              f"aile={kontrol['name'].getDebugName(1)!r}, "
              f"ps={kontrol['name'].getDebugName(6)!r}, "
              f"cmap={len(kkmap)}, TR-eksik={kesit_kaydi['turkce_kesitte_eksik'] or 'YOK'}")

    toplam = sum(y["toplam_bayt"] for y in yuzler)
    rapor = {
        "sema_notu": "[7] Eski kayıt TEK kaynaklıydı; her `yuzler` girdisi eski şemanın "
                     "BİREBİR aynı alanlarını taşır. Sarmalayıcı eklendi, alan değişmedi.",
        "istenen_kod_noktasi": len(istenen),
        "istenen_kume_sha256": kume_sha,
        "istenen_kume_dosyasi": "kanit/istenen_kod_noktalari.json",
        "kod_noktasi_kaymasi": {
            "08_07_kaydi": 347,
            "bu_tur": len(istenen),
            "not": "Aynı GUVENLIK_KUMESI + aynı olcum_kapsami(); fark taranan kaynak "
                   "dosyaların 08-07'den beri değişmesinden. 347'ye ZORLANMADI (uydurma "
                   "yasağı) — 08-07'nin tam listesi kayda geçmemiş, git bu ajana yasak.",
        },
        "yuzler": yuzler,
        "toplam_bayt": toplam,
        "toplam_kb": round(toplam / 1024, 1),
        "butce": {
            "kaynak": "tests/test_yazitipi_v201.py::test_dagitim_boyutu_BUTCEDE",
            "esik_bayt": BUTCE_BAYT,
            "esik_kb": round(BUTCE_BAYT / 1024, 1),
            "sigiyor_mu": toplam < BUTCE_BAYT,
            "bosluk_bayt": BUTCE_BAYT - toplam,
            "bosluk_kb": round((BUTCE_BAYT - toplam) / 1024, 1),
            "taban_08_07_recursive_cifti_bayt": TABAN_08_07_BAYT,
            "tabana_gore_fark_bayt": toplam - TABAN_08_07_BAYT,
        },
    }
    (BURASI / "web_fonts_build.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"TOPLAM {toplam} bayt ({toplam/1024:.1f} KB) → {HEDEF}")
    print(f"BÜTÇE {BUTCE_BAYT} bayt (120.0 KB) → "
          f"{'SIĞIYOR' if toplam < BUTCE_BAYT else 'SIĞMIYOR'} "
          f"(boşluk {(BUTCE_BAYT - toplam)/1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
