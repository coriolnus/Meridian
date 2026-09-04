"""v400 — TSK-117 S4: rol çiftleri deuteranopi/protanopi simülasyonunda ışıklılıkla ayrılıyor mu.
Simülasyon: Viénot-Brettel-Mollon (1999) LMS projeksiyonu (RGB→LMS Hunt-Pointer-Estevez, D65).
Eşik ön-kayıt: kontrast oranı ≥ 1,4:1 (WCAG bağıl ışıklılık). (TSK-117, 2026-09-03)

TSK-136 (2026-09-04, operatör kararı 10:10Z) HEDEFİ DEĞİŞTİRDİ: gece `yon-eksi`nin K-0
düzeltmesi VARSAYILAN tokens.json'dan preset'e taşındı — bu yüzden `_jeton` gece yon-eksi'yi
preset CSS'inden okuyordu (`ui/src/styles/presets/meridian-palet.css`), diğer jetonlar
tokens.json'dan geliyordu ve test xfail(strict) ile ÖLÇÜM KAYDI olarak duruyordu (12 kontrastın
9'u 1,4 eşiğinin altındaydı, min 1,0076 gece sev-2↔sev-3 protan — bkz. spec
`docs/TASARIM-PALET-REZERVE-HUE-2026-09-03.md` §6).

TSK-133 (2026-09-04) DÜZELTTİ: operatör kararı — düzeltme PRESET'TE (varsayılan temaya
DOKUNULMADI). `ui/src/styles/presets/meridian-palet.css` artık sev-1/2/3 + yon-arti/yon-eksi'nin
BEŞİNİN de ışıklılığını (OKLCH L; kroma SABİT) override ediyor — `_jeton` bu yüzden BEŞİNİ
DE preset'ten okur, tokens.json'dan DEĞİL (preset artık bu jetonların hakikat kaynağı; tokens.json'a
dokunulmadı — v396/v399'un "VARSAYILAN" testleri hâlâ tokens.json'u ölçer, bu ikisi ayrı sorular).
xfail(strict=True) KALKTI: aşağıdaki 12 kontrast artık ÖLÇÜLEN DEĞER (deutan/protan, gündüz/gece;
r1 DÜZELTMESİ aynı gün — sev-2↔sev-3 sütunu r1'de DEĞİŞTİ, aşağıdaki not):

  gündüz sev-1↔sev-2   deutan 1,4087  protan 1,5954
  gündüz sev-2↔sev-3   deutan 1,4046  protan 2,3116
  gündüz yon-eksi↔yon-arti  deutan 2,1633  protan 1,4053
  gece   sev-1↔sev-2   deutan 1,5123  protan 1,4066
  gece   sev-2↔sev-3   deutan 1,4048  protan 2,4064
  gece   yon-eksi↔yon-arti  deutan 1,4075  protan 2,0372

r1 İNCELEME DÜZELTMESİ (2026-09-04, aynı gün): ilk turda sev-3 yalnız OKLCH L ile taşınmıştı (hue
OKLCH'de sabit tutulmuştu) — bu depodaki hue ÖLÇÜTÜ HSL/colorsys'tir (v396/v399/v388, spec §1.3),
OKLCH hue DEĞİL; sev-3'ün HSL hue'su gündüzde 144,8°→134,5° (Δ10,3°), gecede 144,6°→132,4°
(Δ12,2°) kaymıştı — hiçbir çivi bunu yakalamıyordu (inceleme buldu). Düzeltme: sev-3 şimdi HEM
OKLCH L HEM küçük bir OKLCH H ofsetiyle yeniden türetildi — iki kısıt: HSL Δhue ≤3° VE
deutan+protan kontrastı ≥1,4 (ikili arama, EN KÜÇÜK sapma) — gündüz #4dc56a→#3bc774 (HSL hue
144,43°, Δ0,37°), gece #6ee286→#5ae593 (HSL hue 144,60°, Δ0,04°). Kroma SABİT kaldı (OKLCH C
değişmedi), yalnız L ve H. Yeni çivi `test_preset_hue_bantlarda_ve_varsayilandan_sapmiyor` bu
sınırı (spec §2 bandı + varsayılandan ±3°) HER BEŞ jeton için ölçer (aşağıda).

Hesap yöntemi + önce/sonra tablo: `.superpowers/sdd/2026-09-04-tsk133/report.md`. MUTASYON KANITI
(r1'de DÜZELTİLDİ — ilk turda YANLIŞ jeton/sayı yazılmıştı, bkz. rapor "r1" bölümü): preset'te
`--sev-3` (gündüz) eski değerine (#00963e) geri alınırsa (sev-2 #d6511a SABİT kalır) bu test
KIRMIZI olur — GERÇEKTEN KOŞULDU: sev-2(#d6511a)↔sev-3(#00963e) deutan=1,2624, protan=1,3087,
ikisi de <1,4 (ÖLÇÜLEN, uydurma değil) — çivinin gerçekten preset'i ısırdığının kanıtı. (İlk
turdaki YANLIŞ iddia — "sev-2'yi geri al → sev-2↔sev-3 deutan 1,07" — sev-2 ANCAK sev-1↔sev-2
çiftini kırar (1,19/1,33), sev-2↔sev-3'ü DEĞİL, çünkü sev-3 zaten YENİ değerine göre hesaplanmıştı;
1,07 spec §6'nın DÜZELTME ÖNCESİ tablosundan kopyalanmış stale bir sayıydı — SİLİNDİ.)"""
import colorsys, json, pathlib, re

from meridian import config
from tests.test_hafiza_genel_bakis_v388 import ROL_BANTLARI, _bantta

TOKENS = pathlib.Path(config.ROOT) / "meridian" / "web" / "tokens.json"
PRESET = pathlib.Path(config.ROOT) / "ui" / "src" / "styles" / "presets" / "meridian-palet.css"
ESIK = 1.4
CIFTLER = [("siddet", "sev-2", "siddet", "sev-3"), ("yon", "yon-eksi", "yon", "yon-arti"), ("siddet", "sev-1", "siddet", "sev-2")]


# sRGB → linear
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(hexstr):
    return [_lin(int(hexstr[i:i + 2], 16)) for i in (1, 3, 5)]


# RGB→LMS (Hunt-Pointer-Estevez, D65) ve deuteranopi/protanopi projeksiyonları (Viénot 1999)
RGB2LMS = [[0.31399022, 0.63951294, 0.04649755], [0.15537241, 0.75789446, 0.08670142], [0.01775239, 0.10944209, 0.87256922]]
LMS2RGB = [[5.47221206, -4.6419601, 0.16963708], [-1.1252419, 2.29317094, -0.1678952], [0.02980165, -0.19318073, 1.16364789]]
DEUTAN = [[1, 0, 0], [0.9513092, 0, 0.04866992], [0, 0, 1]]
PROTAN = [[0, 1.05118294, -0.05116099], [0, 1, 0], [0, 0, 1]]


def _mm(M, v):
    return [sum(M[i][j] * v[j] for j in range(3)) for i in range(3)]


def _sim(rgb, P):
    return _mm(LMS2RGB, _mm(P, _mm(RGB2LMS, rgb)))


def _Y(rgb):
    # gamut kırpması BEYANLI: simülasyon projeksiyonu [0,1] dışına taşabilir (Viénot matrisleri
    # tam-gamut korumaz), WCAG bağıl ışıklılık [0,1] varsayar — clamp burada.
    r, g, b = (max(0, min(1, x)) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _kontrast(a, b):
    ya, yb = _Y(a), _Y(b)
    hi, lo = max(ya, yb), min(ya, yb)
    return (hi + 0.05) / (lo + 0.05)


def _jeton(tema, grup, ad):
    # TSK-133, 2026-09-04: preset artık sev-1/2/3 + yon-arti/yon-eksi'nin BEŞİNİN de ışıklılık
    # düzeltmesini taşıyor (D1, docstring) — CIFTLER'daki beş jetonun hepsi burada PRESET'ten
    # okunur, tokens.json'dan DEĞİL (preset bu jetonların şu anki hakikat kaynağı). `grup`
    # parametresi tokens.json JSON-yolu için tutulur (imza uyumu) ama CSS okumasında kullanılmaz
    # — preset'te değişken adı doğrudan `--{ad}` (grup öneki yok).
    css = PRESET.read_text(encoding="utf-8")
    sec = r'\.dark:root\[data-theme-preset="meridian-palet"\]' if tema == "gece" \
        else r'(?<!\.dark):root\[data-theme-preset="meridian-palet"\]'
    m = re.search(rf'{sec}\s*\{{([^}}]*)\}}', css, re.S)
    assert m, f"preset'te {tema} bloğu bulunamadı: {PRESET}"
    m2 = re.search(rf'--{re.escape(ad)}:\s*(#[0-9a-fA-F]{{6}})', m.group(1))
    assert m2, f"preset {tema} bloğunda --{ad} bulunamadı: {PRESET}"
    return m2.group(1)


def test_rol_ciftleri_renk_korlugunde_isiklilikla_ayrilir():
    ihlal = []
    for tema in ("gunduz", "gece"):
        for g1, a1, g2, a2 in CIFTLER:
            x, y = _rgb(_jeton(tema, g1, a1)), _rgb(_jeton(tema, g2, a2))
            for adi, P in (("deutan", DEUTAN), ("protan", PROTAN)):
                k = _kontrast(_sim(x, P), _sim(y, P))
                if k < ESIK:
                    ihlal.append((tema, a1, a2, adi, round(k, 2)))
    assert not ihlal, f"renk körlüğünde ayrışmayan rol çiftleri (kontrast<{ESIK}): {ihlal}"


# r1 (2026-09-04, inceleme): bu depodaki hue ÖLÇÜTÜ HSL/colorsys'tir (v396/v399/v388/spec §1.3),
# OKLCH hue DEĞİL — TSK-133'ün ilk turu ışıklılığı OKLCH'de hue SABİT tutarak ayarlamıştı ve bu,
# sev-3'ün HSL hue'sunu 10-12° kaydırdı, hiçbir çivi bunu yakalamadı. Bant tablosu v388'in
# ROL_BANTLARI'ndan İTHAL edilir (tek kaynak — v399 aynı deseni kullanır).
GRUP = {"sev-1": "siddet", "sev-2": "siddet", "sev-3": "siddet", "yon-arti": "yon", "yon-eksi": "yon"}
BEKLENEN_BANT = {
    "sev-1": "KRİTİK", "sev-2": "UYARI+YÖN-EKSİ", "sev-3": "BAŞARI+YÖN-ARTI",
    "yon-arti": "BAŞARI+YÖN-ARTI", "yon-eksi": "UYARI+YÖN-EKSİ",
}
HSL_TOLERANS = 3.0  # derece; r1 ruling (2026-09-04)


def _hsl_hue(hexstr):
    r, g, b = (int(hexstr[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    return h * 360


def _dairesel(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _tokens_default_hex(tema, ad):
    d = json.loads(TOKENS.read_text(encoding="utf-8"))
    return d["rol"][tema][GRUP[ad]][ad]["$value"]


def test_preset_hue_bantlarda_ve_varsayilandan_sapmiyor():
    """r1: preset'in ışıklılık düzeltmesi (TSK-133) hue'yu (HSL, bu depodaki ölçüt) BOZMAMALI —
    her beş jeton, iki temada: (a) spec §2 bandında (v388'in ROL_BANTLARI'ndan İTHAL, kendi
    sözlük kopyası YOK) VE (b) jetonlar.css/tokens.json varsayılanından (AYNI tema) ≤3° sapıyor.
    TEK İSTİSNA: gece `yon-eksi` — K-0 (TSK-117/TSK-136) BİLİNÇLİ olarak gece varsayılanından
    (#f98080, 0°) 17°'lik yön-eksi AİLESİNE taşındı (spec §4 K-0); bu sapma zaten
    `tests/test_gece_rol_hue_ayrimi_v396.py`nin İKİ çivisiyle (kritikten ayrım + gündüz ailesiyle
    eşleşme) ölçülüyor — burada gece yon-eksi'nin karşılaştırma tabanı GÜNDÜZ varsayılanıdır
    (aynı aile, farklı tema DEĞİL farklı K-0 durumu)."""
    ihlal = []
    for tema in ("gunduz", "gece"):
        for ad in BEKLENEN_BANT:
            preset_hex = _jeton(tema, GRUP[ad], ad)
            h = _hsl_hue(preset_hex)
            bant = _bantta(h)
            if bant != BEKLENEN_BANT[ad]:
                ihlal.append((tema, ad, "bant", preset_hex, round(h, 1), bant, BEKLENEN_BANT[ad]))
            taban_tema = "gunduz" if (tema == "gece" and ad == "yon-eksi") else tema
            taban_h = _hsl_hue(_tokens_default_hex(taban_tema, ad))
            sapma = _dairesel(h, taban_h)
            if sapma > HSL_TOLERANS:
                ihlal.append((tema, ad, "sapma", preset_hex, round(h, 1), round(sapma, 2)))
    assert not ihlal, f"preset hue kapısı ihlalleri (bant/varsayılan-sapma): {ihlal}"
