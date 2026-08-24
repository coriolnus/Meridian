"""v229 · WP-UX D3-b — ÜÇ FIRSAT YÜZEYİ (F1 / F2 / F14).

docs/TASARIM-YONU-2026-08-07 §7'nin kalan on beş FIRSAT satırından üçü PANO bacağına indi
(veri bacakları wave-2'de inmişti). Üçü de MEVCUT sözleşmenin üstüne oturur: `.pm-*` hücre dili
(v192), kart sözleşmesi (v198), ÖLÇÜLEMEDİ≠0 (v191/v196), D1'in beş renk rolü — yeni jeton/renk/
bileşen YOK ve üçü de UÇTAN okur (uydurma rakam yasağı; landing-fabricated-figures dersi).

  F1 — Kâğıdın nerede yalan söylediği (③ saglik#veriboru).
    `/api/public/summary`nin ledgerstamp ayrımı (closed_trades_live/seed, live{n,mean_r}) İLK KEZ
    panoda: canlı defter ile replay TOHUMUNUN nerede ayrıştığı + hangi metriğin kâğıtta ŞİŞİK
    olduğu (ham toplam tohumla şişer, canlı satır paylaşmaz). L1'e geçişin ön-şartı.

  F2 — Canlı-backtest sapmasının kökü (④ ogrenme#bilesenic).
    E2 defterinin (`icra.slipaj`) ölçtüğü GERÇEK sapma = LİMİT bacağı (`fill_vs_limit_bps`); iç
    motorun `fill_vs_resmi_acilis_bps`i None (totoloji — dolum açılıştan sabit slippage ile türer)
    ve satır BEYAN taşır. Kart sapmanın KÖKÜNÜ adlandırır, 0 bps basmaz.

  F14 — İki kademeli eşik + NO_DATA (③ saglik#operasyon).
    `esikHal` panonun TEK üç-hâl dilini kurar: uyarı → --sev-2, alarm → --sev-1, ölçülemedi →
    sönük (0 DEĞİL). `firsatEsikPaneli` onu dört sağlık göstergesine aynı jetonlarla uygular.

TESTLER HEM DAVRANIŞA HEM KAYNAĞA BAKAR (repo deseni: v196/v198): saf fonksiyonlar Node'da
FİİLEN koşturulur — "kaynakta doğru görünen şablon çalışma zamanında başka şey basıyor" sınıfını
yakalar. Alt-düzey biçimleyiciler (trn/isr/pctf/kanitOrani) v198 emsaliyle harness'te SADIK
kopyadır; ölçülen fonksiyonların (esikHal + üç kart) KENDİ kaynağı çıkarılıp koşturulur.
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()

NODE = shutil.which("node")

# Yorumsuz gövde (v191/v196/v198 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o kuralın
# ihlali/beyanı sanılmamalı — bu turun her fonksiyonu kaldırdığı/eklediği deseni yorumda ADIYLA
# anlatıyor ("ozetSerit DEĞİL", "0 bps DEĞİL", "None — beyanlı").
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


# Türkçe İ TUZAĞI: Python `.lower()` "İ"yi "i̇" (birleşik nokta) yapar → `.lower()` üstünde alt-dize
# eşleşmesi Türkçe metinde SESSİZCE kayar. Bu dosya `.lower()` KULLANMAZ; çok-satır şablon metnini
# tek boşluğa indirir (`_flat`) ve TAM BÜYÜK/KÜÇÜK harfle eşler.
def _flat(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _fn(ad: str, kaynak: str = APPJS) -> str:
    """Fonksiyon/tek-satırlık-const dilimi (v198 `_fn` deseni)."""
    if f"function {ad}(" in kaynak:
        i = kaynak.index(f"function {ad}(")
        parcalar = []
        for ln in kaynak[i:].splitlines(keepends=True):
            parcalar.append(ln)
            if ln.rstrip("\n") == "}":
                break
        return "".join(parcalar)
    i = kaynak.index(f"const {ad} = ")
    return kaynak[i:kaynak.index("\n", i) + 1]


def _obj(ad: str) -> str:
    """Çok satırlı const nesne dilimi (`const AD = { … \\n};`)."""
    i = APPJS.index(f"const {ad} = {{")
    return APPJS[i:APPJS.index("\n};", i) + len("\n};")]


# Alt-düzey biçimleyiciler — SADIK kopya (v198 harness emsali: stabil plumbing inline'lanır, ölçülen
# fonksiyonların kendi kaynağı çıkarılır). Türkçe locale yerine "en-US" kullanılır ki `.` binlik
# ayırıcı testte kararlı olsun — biçim değil, DAL mantığı ölçülüyor.
_STUBS = """
const trn = (x, d = 0) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "\\u2014"
  : n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); };
const money = x => x == null ? "\\u2014" : "$" + trn(x, 2);
const pctf = (x, d = 2) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "\\u2014"
  : "%" + (n * 100).toFixed(d); };
const cls = x => x == null ? "" : (x > 0 ? "pos" : (x < 0 ? "neg" : ""));
const isr = (x, metin) => { const n = Number(x); if (x == null || !Number.isFinite(n) || n <= 0) return metin;
  const s = String(metin); return (s[0] === "%" || s[0] === "$") ? s[0] + "+" + s.slice(1) : "+" + s; };
const KANIT_TAVAN_N = 61;
const kanitOrani = n => (!n || !Number.isFinite(Number(n))) ? null
  : Math.min(1, Math.log10(Number(n) + 1) / Math.log10(KANIT_TAVAN_N));
const AZ_ORNEK_N = 10;
const azOrnek = n => n != null && Number.isFinite(Number(n)) && Number(n) < AZ_ORNEK_N;
"""

_GERCEK = ["esc", "hucreCubuk", "hucreGovde", "kartOzeti", "firsatBos", "belirsiz", "katKart",
           "esikHal", "esikSatiri", "firsatKagitCanli", "firsatSapmaKoku", "firsatEsikPaneli"]


def _harness_govde() -> str:
    return _STUBS + "\n" + _obj("KART_KAYDI") + "\n" + "\n".join(_fn(f) for f in _GERCEK)


# ---- FİKSTÜRLER ------------------------------------------------------------------------------
_F1 = {
    # canlı 1 « tohum 95 → kâğıt ŞİŞİK (canlı manşetin çok altında)
    "sisik": {"live": {"n": 1, "mean_r": 0.512}, "seed": {"n": 95},
              "closed_trades_live": 1, "closed_trades_seed": 95, "closed_trades": 96,
              "closed_trades_belirsiz": 0},
    # canlı ≥ tohum → şişik değil (rozet yok)
    "denge": {"live": {"n": 50, "mean_r": 0.2}, "seed": {"n": 40},
              "closed_trades_live": 50, "closed_trades_seed": 40, "closed_trades": 90,
              "closed_trades_belirsiz": 0},
    # canlı sayısı ölçülemedi (None) — 0 basılmamalı
    "live_yok": {"live": {"n": None, "mean_r": None}, "seed": {"n": 95},
                 "closed_trades_live": None, "closed_trades_seed": 95, "closed_trades": 95,
                 "closed_trades_belirsiz": 0},
    "yok": None,     # uç düştü
}

_F2 = {
    # dolu defter: limit-bacağı ORTALAMA -3,2 bps (gerçek sapma), iç motor açılış-bacağı None+beyan
    "dolu": {"durum": "dolu",
             "ayna": {"dolum": {"n_dolan": 40,
                                "fill_vs_limit_bps": {"n": 40, "n_olculemeyen": 0, "ort": -3.2,
                                                      "medyan": -2.0, "p90": -8.0},
                                "fill_vs_resmi_acilis_bps": {"n": 40, "n_olculemeyen": 0, "ort": 5.1,
                                                             "medyan": 4.0, "p90": 12.0},
                                "yorum": "fill_vs_limit_bps belirgin NEGATİF → yasa para bıraktı"}},
             "ic_motor": {"n_dolan": 40,
                          "fill_vs_resmi_acilis_bps": {"n": 0, "n_olculemeyen": 40, "ort": None},
                          "fill_vs_resmi_acilis_beyan":
                              "totoloji: dolum resmî açılıştan SABİT slippage ile türer"}},
    # defter boş (n_dolan 0) — ÖLÇÜLEMEDİ, 0 bps DEĞİL
    "bos": {"durum": "defter boş — ilk satır ilk ayna döngüsünde düşer (BROKER=alpaca_paper)",
            "ayna": {"dolum": {"n_dolan": 0,
                               "fill_vs_limit_bps": {"n": 0, "n_olculemeyen": 0, "ort": None}}},
            "ic_motor": {}},
    "yok": None,     # uç düştü
}

_F14 = {
    # geciken 3 (ALARM) · veri-yok 1 (UYARI) · evren sapması 0 (iyi) · EOD 2/8 (iyi)
    "karisik": {"watchdog": {"stale": ["a", "b", "c"], "never": []},
                "pipeline": {"symbol_no_data": {"confirmed_no_data": ["XYZ"]},
                             "universe_drift": {"n_stale": 0, "status": "ok"},
                             "refetch_attempts": 2, "refetch_max": 8}},
    # sapan ÖLÇÜLMEDİ (ud yok) · EOD sayacı ölçülemedi (attempts yok) → iki ÖLÇÜLEMEDİ hâli
    "olcumsuz": {"watchdog": {}, "pipeline": {"universe_drift": {"status": "unknown"}}},
    "yok": None,     # uç düştü
}

# esikHal doğrudan sınama: [deger, opts, beklenen_durum]
_ESIK = [
    [None, {"uyari": 1, "alarm": 3}, "olculemedi"],
    ["", {"uyari": 1, "alarm": 3}, "olculemedi"],
    [0, {"uyari": 1, "alarm": 3}, "iyi"],            # SIFIR BİR ÖLÇÜMDÜR — olculemedi DEĞİL
    [1, {"uyari": 1, "alarm": 3}, "uyari"],          # sınırda (>=) uyarı doğar
    [2, {"uyari": 1, "alarm": 3}, "uyari"],
    [3, {"uyari": 1, "alarm": 3}, "alarm"],          # alarm eşiği uyarıyı EZER
    [9, {"uyari": 1, "alarm": 3}, "alarm"],
    # yön "dusuk": küçük değer kötü
    [2, {"uyari": 10, "alarm": 3, "yon": "dusuk"}, "alarm"],
    [8, {"uyari": 10, "alarm": 3, "yon": "dusuk"}, "uyari"],
    [15, {"uyari": 10, "alarm": 3, "yon": "dusuk"}, "iyi"],
    # eşik tanımsız (mx null) → hiç tetiklemez ama değer ÖLÇÜLDÜ → iyi
    [5, {"uyari": None, "alarm": None}, "iyi"],
]

_DRIVER = """
const F1 = %(f1)s, F2 = %(f2)s, F14 = %(f14)s, ESIK = %(esik)s;
const out = { f1: {}, f2: {}, f14: {}, esik: [] };
for (const [k, v] of Object.entries(F1)) out.f1[k] = firsatKagitCanli(v);
for (const [k, v] of Object.entries(F2)) out.f2[k] = firsatSapmaKoku(v);
for (const [k, v] of Object.entries(F14)) out.f14[k] = firsatEsikPaneli(v);
for (const c of ESIK) out.esik.push(esikHal(c[0], c[1]));
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def ciktilar():
    if NODE is None:
        pytest.skip("node yok")
    betik = _harness_govde() + _DRIVER % {
        "f1": json.dumps(_F1, ensure_ascii=False), "f2": json.dumps(_F2, ensure_ascii=False),
        "f14": json.dumps(_F14, ensure_ascii=False),
        "esik": json.dumps([[c[0], c[1]] for c in _ESIK], ensure_ascii=False),
    }
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"D3-b dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


# =============================================================================================
# F1 — KÂĞIT-CANLI AYRIŞMASI
# =============================================================================================
def test_f1_canli_ve_tohum_ayrisimini_gosterir(ciktilar):
    """Üç sayı da ekranda ve KAYNAĞA bağlı (uydurma değil): canlı 1 · tohum 95 · ham 96."""
    h = ciktilar["f1"]["sisik"]
    assert 'data-kart="veriboru:kagitcanli"' in h
    assert ">1<" in h or ">1 " in h or "Canlı işlem" in h        # canlı satır var
    assert "95" in h and "96" in h                               # tohum + ham toplam
    assert "TOHUM" in h.upper() and ("CANLI" in h.upper() or "canlı" in h)
    assert "KÂĞIT ŞİŞİK" in h, "canlı « tohum iken 'kâğıt şişik' rozeti doğmuyor"


def test_f1_hangi_metrik_sisik_adlandiriliyor(ciktilar):
    """İş emrinin çivisi: 'hangi metrik kâğıtta şişik' — ham toplam tohumla şişer, canlı paylaşmaz."""
    fl = _flat(ciktilar["f1"]["sisik"])
    assert "kâğıdın şiştiği sayı budur" in fl, "ham toplamın şiştiği söylenmiyor"
    assert "ŞİŞİK" in fl and "kâğıtta ŞİŞİKtir" in fl
    assert "L1'e geçiş" in fl, "L1'e geçişin ön-şartı olduğu ekranda yazmıyor"


def test_f1_payda_BEYANLI_ve_dort_kirilim_denetli(ciktilar):
    """DÖRT KIRILIMIN PAYDA DENETİMİ (iş emrinin zorunlu koordinasyonu). CANLI + TOHUM + BELİRSİZ
    ham toplama göre PAY taşır (payda başlıkta + alt hintte ADIYLA); HAM TOPLAM paydanın KENDİSİdir
    → PAYSIZ ('—'). Dört satırın PAY hücresi TEK TEK denetlenir."""
    fl = _flat(ciktilar["f1"]["sisik"])
    # Kapalı özet çubuğu payda beyanlı (v192 kuralı özette de geçerli).
    assert 'data-payda="kapanmış işlem (96)"' in fl, "özet çubuğunun paydası beyan edilmemiş"
    # Payda İKİ yerde ADIYLA: sütun başlığı + alt hint.
    assert "PAY (ham)" in fl and "AYNI paydadan (ham toplam 96)" in fl
    # DÖRT satırın PAY hücresi (parçalar payını, ham toplam '—' taşır):
    assert '>Canlı işlem</span> <span class="mono-num">1</span> <span class="mono-num mut">%1<' in fl
    assert '>Tohum (replay)</span> <span class="mono-num">95</span> <span class="mono-num mut">%99<' in fl
    assert '>Belirsiz</span> <span class="mono-num">0</span> <span class="mono-num mut">%0<' in fl
    assert '>Ham toplam</span> <span class="mono-num">96</span> <span class="mono-num mut">—<' in fl, \
        "HAM TOPLAM paydanın kendisi olduğu hâlde bir orana bölünmüş (paysız olmalı)"


def test_f1_olculemedi_UYDURMA_SIFIR_basmaz(ciktilar):
    """UÇ DÜŞTÜ ve CANLI ÖLÇÜLEMEDİ dalları: 0 DEĞİL, bir CÜMLE. `?? 0`/`|| 0` ile çökme YOK."""
    yok = ciktilar["f1"]["yok"]
    assert "ÖLÇÜLEMEDİ" in yok and "public/summary" in yok
    assert ">0<" not in yok, "uç düştüğünde uydurma sıfır basılmış"
    lyok = ciktilar["f1"]["live_yok"]
    # Canlı sayısı None → özet 'veri yok' der, kırılımda '—'; hiçbir yerde canlı için '0' uydurulmaz.
    assert "ÖLÇÜLEMEDİ" in lyok
    assert "veri yok" in lyok


def test_f1_rozet_KOSULLU_dengede_sismis_demez(ciktilar):
    """Rozet bir uyarıdır, süs değil: canlı ≥ tohum iken 'KÂĞIT ŞİŞİK' basılmaz."""
    assert "KÂĞIT ŞİŞİK" not in ciktilar["f1"]["denge"]


# =============================================================================================
# F2 — CANLI-BACKTEST SAPMASININ KÖKÜ
# =============================================================================================
def test_f2_GERCEK_sapma_limit_bacagi(ciktilar):
    """E2'nin ölçtüğü gerçek sapma LİMİT bacağıdır — değeri (−3,2 bps) ve dağılımı ekranda; kök
    NİTELİKSEL adlandırılır (giriş-limitinin ATR bacağı → kâğıt kâr), sayı ŞİŞİRİLMEZ."""
    h = ciktilar["f2"]["dolu"]
    assert 'data-kart="bilesenic:sapma"' in h
    assert "Limit-bacağı" in h and "GERÇEK sapma" in h
    assert "-3.2 bps" in h, "limit-bacağı ortalaması ekranda değil"
    assert "n=40" in h                                          # payda (dolum) beyanlı
    assert "ATR baca" in h and "kâğıt kâr" in h.lower(), "sapmanın KÖKÜ niteliksel adlandırılmıyor"
    # GERÇEK sapma bir CANLI ölçümdür, hardcode edilmiş tarihsel bir sayı DEĞİL (uydurma yasağı).
    assert "CANLI ölçüm" in h


def test_f2_ic_motor_TOTOLOJI_None_beyanli_sifir_degil(ciktilar):
    """Totoloji-beyanı: iç motorun açılış-bacağı None (0 bps DEĞİL) ve yazarın BEYANI'nı taşır."""
    fl = _flat(ciktilar["f2"]["dolu"])
    assert "totoloji" in fl or "TOTOLOJİK" in fl
    assert "None" in fl and "0 bps DEĞİL" in fl
    # Yazarın beyanı kesik-çizgili şerhte (belirsiz() title'ı) — SURFACE ediliyor, uydurulmuyor.
    assert "dolum resmî açılıştan SABİT slippage ile türer" in fl, "iç-motor totoloji beyanı ekranda yok"


def test_f2_defter_bos_OLCULEMEDI_degil_sifir(ciktilar):
    """`n=0` bir KUSUR değil bir DURUMdur: 'DEFTER BOŞ' der, 0 bps ORTALAMA UYDURMAZ."""
    h = ciktilar["f2"]["bos"]
    assert "DEFTER BOŞ" in h and "0 bps DEĞİL" in h
    assert "-3.2" not in h and "bps</span> <span" not in h, "boş defterde dağılım uydurulmuş"


def test_f2_uc_dustu_OLCULEMEDI(ciktilar):
    h = ciktilar["f2"]["yok"]
    assert "ÖLÇÜLEMEDİ" in h and "icra.slipaj" in h
    assert ">0<" not in h


def test_f2_mutabakat_kartindan_AYRI_soru(ciktilar):
    """F2 öğrenme yüzeyindedir (geri-test neden yalan söyledi), mutabakat masasının icra kartı
    ise operasyon (ayna gönderdi mi/doldu mu) — aynı defter, ayrı soru; başlıklar ayrışır."""
    fl = _flat(ciktilar["f2"]["dolu"])
    assert "canlı ödeme neden geri-testten sapıyor" in fl
    assert "E1/E2 hattı" in fl


# =============================================================================================
# F14 — İKİ KADEMELİ EŞİK + NO_DATA (esikHal + firsatEsikPaneli)
# =============================================================================================
def test_f14_esikHal_UC_HALI_ve_kademeler(ciktilar):
    """`esikHal` üç hâli + iki kademeyi doğru ayırır (yön dahil)."""
    beklenen = [c[2] for c in _ESIK]
    olculen = [h["durum"] for h in ciktilar["esik"]]
    assert olculen == beklenen, f"esikHal hâlleri: {list(zip(olculen, beklenen))}"


def test_f14_esikHal_SIFIR_olculemedi_DEGIL_jetonlar_ROL_katmani(ciktilar):
    """SIFIR ölçümdür (iyi), None ölçülemezliktir. Renk ROL katmanından: uyarı→sev-2, alarm→sev-1
    (ham hue DEĞİL — D1). 'iyi' ve 'ölçülemedi' RENKSİZ (sev boş)."""
    hh = ciktilar["esik"]
    d = {i: hh[i] for i in range(len(hh))}
    assert d[2]["durum"] == "iyi" and d[2]["sev"] == "", "0 değeri renk/alarm taşıyor"
    assert d[0]["durum"] == "olculemedi" and d[0]["sev"] == "" and d[0]["etiket"] == "ÖLÇÜLEMEDİ"
    # uyarı → sev-2, alarm → sev-1 (rol jetonu adları; hue değil)
    uyari = next(h for h in hh if h["durum"] == "uyari")
    alarm = next(h for h in hh if h["durum"] == "alarm")
    assert uyari["sev"] == "sev-2" and uyari["etiket"] == "UYARI"
    assert alarm["sev"] == "sev-1" and alarm["etiket"] == "ALARM"


def test_f14_panel_TEK_dil_uc_hal_birlikte(ciktilar):
    """`firsatEsikPaneli` dört göstergeyi AYNI üç-hâl diliyle basar: alarm(sev-1)+uyarı(sev-2) var,
    özet 'N/4' + rozet taşır ve kartın kimliği kayıtlı."""
    h = ciktilar["f14"]["karisik"]
    assert 'data-kart="operasyon:esik"' in h
    assert "ALARM" in h and "UYARI" in h
    assert "sev-1" in h and "sev-2" in h, "rol jetonları panelde yok"
    assert "1 ALARM" in h, "alarm rozeti özet başlığa taşınmıyor"
    assert "1 alarm" in h and "1 uyarı" in h                    # özet sayımı


def test_f14_panel_NO_DATA_uydurma_sifir_basmaz(ciktilar):
    """Ölçülemeyen gösterge 'ölçülemedi' der (0 DEĞİL); ÖLÇÜLEN sıfır ise '0' DOĞRUdur — panel
    ikisini ayırır ve bir hüküm UYDURMAZ."""
    fl = _flat(ciktilar["f14"]["olcumsuz"])
    assert "sapma sayısı ÖLÇÜLMEDİ" in fl and "liste temiz" in fl   # evren sapması None → 'liste temiz' DEMEZ
    assert "deneme sayacı ölçülemedi (0 deneme DEĞİL)" in fl        # EOD sayacı None
    assert "ÖLÇÜLEMEDİ" in fl                                        # sönük üç-hâl etiketi
    # ÖLÇÜLEN sıfır (geciken/veri-yok = 0) ile ÖLÇÜLEMEYEN (sapan/EOD None) ayrı sayılır:
    assert "0 alarm · 0 uyarı · 2 iyi · 2 ölçülemedi" in fl


def test_f14_panel_uc_dustu_OLCULEMEDI(ciktilar):
    fl = _flat(ciktilar["f14"]["yok"])
    assert "ÖLÇÜLEMEDİ" in fl and "diagnostics" in fl
    assert "'hepsi iyi' DEĞİL" in fl          # 'ölçülemedi ≠ hepsi iyi' beyanı


# =============================================================================================
# KAYNAK / SÖZLEŞME — kayıt, bağ, jeton, CSP, uydurma, node --check
# =============================================================================================
def test_uc_kartin_KAYDI_ve_BOLUMU_dogru():
    """Üç kart da KART_KAYDI'da doğru yüzey/bölümle kayıtlı (F1/F14 ③, F2 ④)."""
    kayit = _obj("KART_KAYDI")
    assert '"veriboru:kagitcanli":{ alan: "saglik",  bolum: "veriboru" }' in kayit
    assert '"bilesenic:sapma":    { alan: "ogrenme", bolum: "bilesenic" }' in kayit
    assert '"operasyon:esik":     { alan: "saglik",  bolum: "operasyon" }' in kayit


def test_uc_kart_BOLUMUNE_baglandi_YASA6():
    """YASA 6: her kartın bir çağıranı var (aksi hâlde çizilmez). F1→veriboru, F2→bilesenic,
    F14→operasyon; F1 ayrıca `/api/public/summary` okuyucusudur (wave-2 alanlarının pano tüketicisi)."""
    veri = KOD[KOD.index("RENDER.veriboru = "):KOD.index("RENDER.bilesenic = ")]
    assert "firsatKagitCanli(ps)" in veri and 'j("/api/public/summary")' in veri
    bil = KOD[KOD.index("RENDER.bilesenic = "):KOD.index("RENDER.golge = ")]
    assert "firsatSapmaKoku(" in bil and "icra" in bil and "slipaj" in bil
    op = KOD[KOD.index("RENDER.operasyon = "):KOD.index("RENDER.cizelge = ")]
    assert "firsatEsikPaneli(_DIAG)" in op


def test_public_summary_wave2_alanlarinin_OKUYUCUSU_var():
    """wave-2 (v223) `/api/public/summary`ye canlı/tohum ayrımını indirdi; F1 onların İLK pano
    okuyucusudur (YASA 6, iki yön)."""
    fn = _fn("firsatKagitCanli")
    for alan in ("closed_trades_live", "closed_trades_seed", "closed_trades", "live"):
        assert alan in fn, f"{alan} F1'de okunmuyor"
    assert "mean_r" in fn


def test_yeni_ozetSerit_serit_ACILMADI():
    """F1 `.trow` tablosuyla çizer (ozetSerit DEĞİL) → yeni bir şerit BEYAN etmek gerekmedi;
    ozetSerit çağrı sayısı v207/v219/v226 tabanında (6) kalır."""
    # 2026-08-24 (operatör turu): ALTI → YEDİ. Artış bir EKLEME değil bir BÖLÜNMEDİR:
    # «bir sonraki açılış» kartı Bugün'e taşınırken şeridini yanında götürdü, Adaylar
    # bölümü de kendi şeridini geri aldı — ve ikisinin PAYDASI FARKLI (son seans ↔
    # pencerenin tamamı). İki payda iki şerit demektir; aynı etiketi iki farklı paydayla
    # basmak v192'nin kapattığı kusurdu. Beyan: v191 `_SERIT_BOLGELERI` (yedi bölge).
    assert APPJS.count("ozetSerit([") == 7, "ozetSerit sayısı değişti — v191 _SERIT_BOLGELERI + v226 güncellenmeli"


def test_yeni_kod_UYDURMA_SIFIR_getirmedi():
    """`?? 0`/`|| 0` tavanı (v196) 192'de sabit — üç yüzey de ölçülemedi≠0'ı EXPLICIT null
    denetimiyle kurar, tek bir null-sıfır katlaması eklemez."""
    nf = re.compile(r"(\?\?|\|\|)\s*0(?![\d.])")
    for f in ("esikHal", "esikSatiri", "firsatKagitCanli", "firsatSapmaKoku", "firsatEsikPaneli"):
        g = _fn(f)
        assert not nf.search("\n".join(l for l in g.splitlines() if not l.lstrip().startswith("//"))), \
            f"{f} `?? 0`/`|| 0` içeriyor — ÖLÇÜLEMEDİ≠0 explicit kurulmalı"


def test_yeni_kod_YENI_RENK_JETONU_ACMAZ():
    """D1 rol katmanı + CSP: yeni fonksiyonlar `--sev-1`/`--sev-2` ROL jetonlarını sınıf olarak
    kullanır (ham hue --red/--amber DEĞİL) ve dört yüzey jeton birliğini (v208) BOZMAZ — index'e
    yeni bir `--*` tanımı eklenmedi."""
    for f in ("esikHal", "esikSatiri", "firsatEsikPaneli"):
        g = _fn(f)
        for hue in ("--red", "--amber", "--green"):
            assert hue not in g, f"{f} ham hue okuyor: {hue}"
    # esikHal'in ürettiği sınıflar rol katmanından.
    assert '"sev-1"' in _fn("esikHal") and '"sev-2"' in _fn("esikHal")
    # index.html'de yeni bir token tanımı DOĞMADI (v208 dört-yüzey birliği): sev/yon/mod aynen.
    assert INDEX.count("--sev-1:var(--red);") == 2      # gündüz + gece bloğu (v208 emsali)


def test_CSP_satir_ici_olay_ozniteligi_YOK():
    """CSP script-src 'self': üç kart da salt-okumadır, satır içi `onclick`/`on*` YOK."""
    for f in ("firsatKagitCanli", "firsatSapmaKoku", "firsatEsikPaneli", "esikSatiri"):
        g = _fn(f)
        assert not re.search(r'\son[a-z]+="', g), f"{f} satır içi olay özniteliği taşıyor (CSP)"
        assert "http://" not in g and "https://" not in g


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_node_check_gecer():
    r = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
