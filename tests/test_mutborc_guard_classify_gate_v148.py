"""test_mutborc_guard_classify_gate_v148.py — H5 TEST-BORCU: guard.classify_gate mutasyon kümesi.

NEDEN BU DOSYA VAR
  `meridian/guard.py::classify_gate` SERT RİSK ZARFININ TEK KAYNAĞI (docstring'in kendi beyanı).
  Mutasyon taraması bu fonksiyonda 567 mutanttan 357'sini HAYATTA bıraktı: yani kapının sabitleri,
  karşılaştırma yönleri, eşik eşitlikleri, hüküm dizgileri ve karar-ağacı (`detail_out`) alanları
  değiştirilse suite YEŞİL kalıyordu. Bir kapı için bu, "test var" ile "test koruyor" arasındaki
  farktır: NO_GO'yu REVIEW'a çeviren tek harflik bir sapma (severity "hard"→"HARD") sessizce canlıya
  girebilirdi.

ÖLDÜRÜLEN MUTASYON SINIFLARI (mutant numaraları `mutants/meridian/guard.py`
`x_classify_gate__mutmut_N` gövdelerine göre)
  S1  kontrol ADI (`_chk` 1. argümanı): None / "XXadXX" / "AD"        → 48,60,61,83,95,96,120,132,133,
      167,179,180,214,226,227,254,266,267,295,307,308,317,329,330,363,375,376,385,397,398,441,453,454,
      470,480,481,488,500,501,523,535,536
  S2  ŞİDDET (`sev`): "hard"→None/"XXhardXX"/"HARD" HÜKMÜ NO_GO'dan REVIEW'a düşürür → 51,73,74,86,
      109,110,123,156,157,170,196,197,217,243,244,257,271,272; "soft" varyantları hükmü değiştirmez
      ama karar ağacına YALAN yazar → 320,338,339,366,378,379,388,416,417,444,462,463,473,486,487,
      491,505,506,526,548,549
  S3  karar-ağacı SÖZLÜK ANAHTARLARI ve `passed` tersine çevrimi → 30,31,32,33,34,35,36,37,38,39,40,
      41,42,43
  S4  `value=`/`threshold=` argümanları (None / düşürülmüş / yanlış sözlük anahtarı / yanlış
      varsayılan / yanlış yuvarlama basamağı) → 52,53,58,59,75,76,77,78,79,80,81,82,87,88,93,94,111,
      112,113,114,115,116,117,124,125,130,131,158,159,163,164,171,172,177,178,199,200,201,202,203,204,
      206,207,208,209,210,211,218,219,224,225,245,246,247,248,249,250,251,258,259,264,265,274,275,276,
      277,299,300,305,306,313,314,315,316,321,322,327,328,340,341,342,343,344,345,367,368,373,374,381,
      382,383,384,389,390,395,396,419,420,421,423,427,428,429,430,445,446,451,452,465,466,467,474,479,
      492,493,498,499,508,509,510,511,512,527,528,533,534,550,551,552,553
  S5  KOŞUL yönü/sınırı (eşitlik dahil) → 63,65,68,69,70,97,98,100,101,102,103,104,121,135,136,140,
      141,146,149,150,153,181,182,184,185,186,187,188,189,193,228,229,231,232,233,234,268,269,270,286,
      289,291,294,309,331,335,336,337,354,357,359,362,377,406,407,468,469,502,503,504,516,517,519,520,
      521,522,537,538,540,541,542,543,544,545
  S6  `failed` argümanı None/False → 49,84,168,215,255,318,471,482,489,524
  S7  HÜKÜM DİZGİSİ (None / "XX...XX" / büyük-küçük harf) → 50,71,72,85,122,169,216,238,239,240,256,
      319,409,413,414,459,461,472,483,484,485,490,525,546,547
  S8  argüman DÜŞÜRME (imza kayması → TypeError) → 475,476,477,478
  S9  `plan`/`portfolio`/`rr`/`sec`/`sc` okuma varsayılanları → 7,9,12,14,15,17,18,19,22,23,25,26,27,28
  S10 `_y3_portfolio_caps` çağrı argümanları → 554,555,556,557

ÖLÇÜLEN SONUÇ (iddia değil, ölçüm — 2026-08-01)
  357 hayatta-kalan mutantın gövdeleri `mutants/meridian/guard.py`ten tek tek yüklenip
  `guard.classify_gate`e bağlandı ve bu dosyanın 54 vakası her mutant için yeniden koşuldu:
  **356 öldü, 1 kaldı** — kalan TEK mutant aşağıda eşdeğer ilan edilen 415'tir. Yani "kapsam
  tahmini" diye bir sayı yok; kalan tek mutantın adı var.

EŞDEĞER — ÖLDÜRÜLEMEZ (YASA 4: sessiz yutulmuyor, gerekçesiyle kayda geçiyor)
  * mutant 415 — `f"...(ρ≈{float(portfolio.get('max_corr', 1.0)):.2f})..."` (korelasyon soft
    hükmünün METNİ içindeki VARSAYILAN). Bu f-string argüman olarak HER TURDA hesaplanır ama
    `_chk` onu yalnız `failed` doğruyken `note`a yazar. Varsayılanın okunması için `max_corr`
    anahtarının EKSİK olması gerekir; anahtar eksikken gerçek kod 0.0 okur ve 0.0 > 0.85 asla
    doğru olmadığından hüküm ATEŞLENMEZ, üretilen metin de atılır. Yani "anahtar eksik" ile
    "metin görünür" koşulları AYNI ANDA sağlanamaz → gözlemlenebilir davranış farkı YOKTUR.
    (Aynı satırdaki 409/413/414 anahtar-mutantları eşdeğer DEĞİL: anahtar mevcutken 0.0'a düşerler
    ve metin görünürken ölçülürler — `test_s7_correlation_mesaji_gercek_rho_yazar` onları öldürür.)

Fikstürler tamamen SENTETİK: `config.goal()` OKUNMAZ (canlı goal.yaml sürüklenirse bu dosyanın
sınır değerleri anlamını yitirirdi), disk yok, ağ yok, state yazımı yok. classify_gate saf bir
fonksiyondur ve burada saf olarak sınanır.
"""
from __future__ import annotations

import pytest

from meridian import guard


# --------------------------------------------------------------------------------------------
# Fikstürler — hepsi sentetik ve SINIR DEĞERLERİ SEÇİLEBİLİR olsun diye elle yazıldı.
# --------------------------------------------------------------------------------------------
LIMITS = {"autonomy_level": 1, "max_position_r": 1.0, "max_open_positions": 5,
          "max_daily_loss_pct": 3, "max_sector_exposure_pct": 60,
          "no_trade_before_bars": 2, "kill_switch_file": "state/HALT"}

# Temiz GO planı: her sayı BİLEREK ondalıklı — yuvarlama basamağı mutantları (round(x,2)→round(x,3)
# / round(x) / round(2)) ancak 2. basamaktan sonra anlamlı hane varsa ölür.
PLAN = {"ticker": "AAA", "sector": "tech", "size_r": 0.55555,
        "r_multiple_expected": 3.14159, "score": 90}
PORT = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": -0.012345,
        "open_risk_r": 1.11111, "max_corr": 0.12345}
REG = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}

KEYS = {"check", "passed", "severity", "value", "threshold", "note"}

HARD_CHECKS = ("exposure_budget", "max_open_positions", "sector_cap", "daily_loss_breaker",
               "position_size", "rr_floor", "heat_hard")
SOFT_CHECKS = ("sector_stacking", "heat_review", "correlation", "leading_sector")


def _goal(**over):
    return {"limits": {**LIMITS, **over}}


def _run(plan=None, port=None, reg=None, goal=None, params=None):
    """(verdict, reasons, detail) — detail_out HER ZAMAN verilir; karar ağacı da sözleşmenin parçası."""
    detail: list = []
    verdict, reasons = guard.classify_gate(PLAN if plan is None else plan,
                                           PORT if port is None else port,
                                           REG if reg is None else reg,
                                           _goal() if goal is None else goal,
                                           params, detail_out=detail)
    return verdict, reasons, detail


def _names(detail):
    return [d["check"] for d in detail]


def _by(detail, name):
    hit = [d for d in detail if d["check"] == name]
    assert len(hit) == 1, f"{name} karar ağacında tam olarak bir kez olmalı, {len(hit)} bulundu"
    return hit[0]


# ============================================================================================
# S1 + S3: karar ağacının ADLARI, SIRASI, ALAN KÜMESİ ve `passed` yönü
# ============================================================================================
def test_s1_temiz_plan_go_verir_ve_karar_agaci_tam_ad_listesini_sirayla_yazar():
    """Kapının 'neden GO?' cevabı GEÇEN kontrolleri de gerektirir: ad listesi sözleşmedir.

    Ad mutantları (None / "XXadXX" / "AD") yalnız burada ölür — hüküm listesi onları görmez."""
    verdict, reasons, detail = _run()
    assert (verdict, reasons) == ("GO", [])
    assert _names(detail) == [
        "exposure_budget", "max_open_positions", "sector_cap", "daily_loss_breaker",
        "position_size", "rr_floor", "heat_hard",
        "sector_stacking", "heat_review", "correlation", "leading_sector", "rr_marginal"]


def test_s3_her_karar_dugumu_tam_alan_kumesini_tasir_ve_gecen_kontrol_passed_true_note_none():
    """Sözlük ANAHTARLARI ("check"/"passed"/"severity"/"value"/"threshold"/"note") ve `passed`
    yönü. `detail_out.append(None)` de burada düşer (dict olmayan düğüm)."""
    _, _, detail = _run()
    assert len(detail) == 12
    for d in detail:
        assert isinstance(d, dict), "karar düğümü sözlük olmalı"
        assert set(d) == KEYS, f"alan kümesi bozuldu: {sorted(d)}"
        assert d["passed"] is True, f"{d['check']} temiz planda geçmeliydi"
        assert d["note"] is None, "geçen kontrol not YAZMAZ"


def test_s2_severity_alani_sert_ve_yumusak_kontrolleri_dogru_etiketler():
    """"hard"/"soft" etiketi hem hükmü yönlendirir hem karar ağacına yazılır. Etiketin
    büyük-küçük harf / None varyantları sert kuralı sessizce yumuşatır."""
    _, _, detail = _run()
    for name in HARD_CHECKS:
        assert _by(detail, name)["severity"] == "hard", name
    for name in SOFT_CHECKS + ("rr_marginal",):
        assert _by(detail, name)["severity"] == "soft", name


# ============================================================================================
# S4: value/threshold — karar ağacının SAYILARI (yanlış anahtar, yanlış varsayılan, yanlış
#     yuvarlama, düşürülmüş argüman)
# ============================================================================================
def test_s4_temiz_planda_her_dugumun_value_ve_threshold_degeri_birebir_sabittir():
    _, _, detail = _run()
    beklenen = {
        "exposure_budget":    (60, ">0"),
        "max_open_positions": (0, "<5"),
        "sector_cap":         (1, "%60"),
        "daily_loss_breaker": (-1.23, ">-%3"),       # round(-0.012345*100, 2)
        "position_size":      (0.55555, "<=1.0R"),
        "rr_floor":           (3.14, ">=2.0"),       # round(3.14159, 2)
        "heat_hard":          (1.67, "<=5.0R"),      # round(1.11111+0.55555, 2)
        "sector_stacking":    (0, "0"),
        "heat_review":        (1.67, "<=3.5R"),
        "correlation":        (0.12, "<=0.85"),      # round(0.12345, 2)
        "leading_sector":     ("tech", "tech"),
        "rr_marginal":        (3.14, ">=2.3"),       # DISCIPLINE_MIN_RR + REVIEW_RR_BAND
    }
    for name, (v, th) in beklenen.items():
        d = _by(detail, name)
        assert d["value"] == v and type(d["value"]) is type(v), f"{name}.value → {d['value']!r}"
        assert d["threshold"] == th, f"{name}.threshold → {d['threshold']!r}"


def test_s4_yuvarlama_basamagi_ikidir_ne_bir_ne_uc_ne_de_sabit():
    """round(x, 2) → round(x, 3) / round(x) / round(2) mutantları. Fikstür sayıları 4+ ondalıklı
    olduğu için üç varyant da farklı sayı üretir."""
    _, _, detail = _run()
    for name, tam in (("daily_loss_breaker", -1.2345), ("rr_floor", 3.14159),
                      ("heat_hard", 1.66666), ("heat_review", 1.66666),
                      ("correlation", 0.12345), ("rr_marginal", 3.14159)):
        v = _by(detail, name)["value"]
        assert v == round(tam, 2), name
        assert v != round(tam, 3) and v != round(tam) and v != 2, f"{name} basamağı kaydı: {v!r}"


# ============================================================================================
# S5 + S7: exposure_budget — sıfır bütçe SERT vetodur
# ============================================================================================
def test_s5_exposure_budget_sifirken_no_go_ve_hukum_dizgisi_birebir():
    v, r, detail = _run(reg={"exposure_budget_pct": 0, "leading_sectors": ["tech"]})
    assert v == "NO_GO"
    assert r == ["exposure_budget %0 — bugün yeni risk yok"]
    d = _by(detail, "exposure_budget")
    assert d["passed"] is False and d["severity"] == "hard"
    assert d["note"] == "exposure_budget %0 — bugün yeni risk yok"
    assert d["value"] == 0 and d["threshold"] == ">0"


def test_s5_exposure_budget_bir_iken_gecer_esik_sifirdir():
    """`<= 0` → `<= 1` mutantı: bütçe %1 iken kapı KAPANMAZ."""
    v, r, _ = _run(reg={"exposure_budget_pct": 1, "leading_sectors": ["tech"]})
    assert (v, r) == ("GO", [])


def test_s5_exposure_budget_anahtari_yokken_varsayilan_sifirdir_yani_no_go():
    """Rejim ölçülemediyse kapı AÇIK varsayılmaz: `regime` sözlüğünün `.get(..., 0)` varsayılanı vetodur."""
    v, r, detail = _run(reg={})
    assert v == "NO_GO" and r == ["exposure_budget %0 — bugün yeni risk yok"]
    d = _by(detail, "exposure_budget")
    assert d["value"] == 0 and d["threshold"] == ">0"


# ============================================================================================
# S5: max_open_positions — EŞİTLİK dolu demektir
# ============================================================================================
def test_s5_pozisyon_sayisi_tavana_esitken_no_go_verir():
    port = {**PORT, "open_positions": 5}
    v, r, detail = _run(port=port)
    assert v == "NO_GO" and r == ["max 5 pozisyon dolu"]
    d = _by(detail, "max_open_positions")
    assert d["passed"] is False and d["severity"] == "hard" and d["value"] == 5
    assert d["threshold"] == "<5"


def test_s5_pozisyon_sayisi_okunamadiginda_sifir_sayilir_bir_degil():
    """`portfolio.get("open_positions", 0)` varsayılanı: tavan 1 iken 'bilinmiyor' DOLU sayılmaz."""
    goal = _goal(max_open_positions=1, max_sector_exposure_pct=150)
    port = {"sector_counts": {}, "day_pnl_pct": 0.0, "open_risk_r": 0.0, "max_corr": 0.0}
    v, r, _ = _run(port=port, goal=goal)
    assert (v, r) == ("GO", [])


# ============================================================================================
# S5: sector_cap — pay/tavan aritmetiği ve sınırın YÖNÜ
# ============================================================================================
def test_s5_sektor_tavani_payi_asinca_no_go_ve_dizge_birebir():
    port = {**PORT, "sector_counts": {"tech": 3}}          # (3+1)/5 = 0.80 > 0.60
    v, r, detail = _run(port=port)
    assert v == "NO_GO" and r == ["'tech' sektör tavanı %60 aşılıyor"]
    d = _by(detail, "sector_cap")
    assert d["passed"] is False and d["severity"] == "hard"
    assert d["note"] == "'tech' sektör tavanı %60 aşılıyor"
    assert d["value"] == 4 and d["threshold"] == "%60"


def test_s5_sektor_tavani_tam_esitlikte_gecer_kural_kesin_buyuktur():
    """(2+1)/5 = 0.600 ve tavan 0.600 → SERT kural ATEŞLEMEZ; yalnız yumuşak yığılma bayrağı kalır.
    `>` → `>=` ve `/100.0` → `/101.0` mutantlarını aynı anda düşürür."""
    port = {**PORT, "sector_counts": {"tech": 2}}
    v, r, _ = _run(port=port)
    assert v == "REVIEW" and r == ["'tech' sektöründe korelasyon yığılması"]


def test_s5_sektor_tavani_sayaci_yokken_bir_degil_sifirdan_baslar():
    """`sc.get(sec, 0)` varsayılanı: tavan 2 pozisyonken boş sayaç kapıyı kapatmaz."""
    goal = _goal(max_open_positions=2)
    port = {**PORT, "sector_counts": {}, "open_positions": 0}
    v, r, _ = _run(port=port, goal=goal)
    assert (v, r) == ("GO", [])


def test_s5_sektor_tavani_paydasi_tavanin_kendisidir_max_bir_yalnizca_taban():
    """`max(1, max_open_positions)` → `max(2, ...)`: tavan 1 iken payda 1 kalmalı, 2 olmamalı."""
    goal = _goal(max_open_positions=1)
    port = {**PORT, "sector_counts": {}, "open_positions": 0}
    v, r, _ = _run(port=port, goal=goal)              # (0+1)/1 = 1.00 > 0.60
    assert v == "NO_GO" and r == ["'tech' sektör tavanı %60 aşılıyor"]


# ============================================================================================
# S5: daily_loss_breaker — işaret, ölçek ve EŞİTLİK
# ============================================================================================
def test_s5_gunluk_kayip_tam_esikte_devreyi_keser():
    """`<=` → `<` ve `/100.0` → `*100.0` mutantları: eşiğe TAM oturan gün de kesilir."""
    port = {**PORT, "day_pnl_pct": -3 / 100.0}
    v, r, detail = _run(port=port)
    assert v == "NO_GO" and r == ["günlük kayıp devre kesici %3"]
    d = _by(detail, "daily_loss_breaker")
    assert d["passed"] is False and d["severity"] == "hard"
    assert d["note"] == "günlük kayıp devre kesici %3"
    assert d["value"] == -3.0 and d["threshold"] == ">-%3"


def test_s5_gunluk_kayip_esigin_bir_tik_altinda_kesmez_bolen_yuzdur():
    """`/100.0` → `/101.0`: %2.99 kayıp %3 devre kesicisini TETİKLEMEZ."""
    v, r, _ = _run(port={**PORT, "day_pnl_pct": -0.0299})
    assert (v, r) == ("GO", [])


def test_s5_gunluk_kayip_okunamadiginda_sifir_sayilir_bir_degil():
    """`portfolio.get("day_pnl_pct", 0.0)` varsayılanı. Tavan %0 iken 0.0 kesicidir, 1.0 değil."""
    goal = _goal(max_daily_loss_pct=0)
    port = {"open_positions": 0, "sector_counts": {}, "open_risk_r": 0.0, "max_corr": 0.0}
    v, r, _ = _run(port=port, goal=goal)
    assert v == "NO_GO" and r == ["günlük kayıp devre kesici %0"]


def test_s4_gunluk_kayip_value_yuzdeye_cevrilir_bolunmez():
    """`* 100` → `/ 100` ve `* 101`: karar ağacındaki sayı YÜZDE cinsinden olmak zorunda."""
    _, _, detail = _run()
    assert _by(detail, "daily_loss_breaker")["value"] == -1.23


# ============================================================================================
# S5 + S7: position_size
# ============================================================================================
def test_s5_boyut_tavani_asilinca_no_go_ve_mesaj_gercek_boyutu_yazar():
    plan = {**PLAN, "size_r": 1.5}
    v, r, detail = _run(plan=plan)
    assert v == "NO_GO" and r == ["boyut 1.5R > max 1.0R"]
    d = _by(detail, "position_size")
    assert d["passed"] is False and d["severity"] == "hard"
    assert d["note"] == "boyut 1.5R > max 1.0R"
    assert d["value"] == 1.5 and d["threshold"] == "<=1.0R"


def test_s5_boyut_tam_tavanda_gecer_kural_kesin_buyuktur():
    v, r, _ = _run(plan={**PLAN, "size_r": 1.0})
    assert (v, r) == ("GO", [])


# ============================================================================================
# S5: rr_floor — üç ayrı sınır (0 alt ucu, 2.0 üst ucu, ikisinin eşitlik yönü)
# ============================================================================================
def test_s5_rr_sifirin_ustunde_ama_tabanin_altindaysa_sert_veto():
    """`0.0 < rr` → `1.0 < rr` mutantı: 0.5 R:R hâlâ SERT vetodur."""
    v, r, detail = _run(plan={**PLAN, "r_multiple_expected": 0.5})
    assert v == "NO_GO" and r == ["R:R 0.5 < 2.0 (yetersiz ödül/risk)"]
    d = _by(detail, "rr_floor")
    assert d["severity"] == "hard" and d["value"] == 0.5 and d["threshold"] == ">=2.0"


def test_s5_rr_tam_tabanda_sert_veto_degil_marjinal_bayraktir():
    """`rr < 2.0` → `rr <= 2.0` (sert taraf) ve `2.0 <= rr` → `2.0 < rr` (yumuşak taraf) ile
    `MIN + BAND` → `MIN - BAND` mutantlarını aynı sınırda düşürür."""
    v, r, detail = _run(plan={**PLAN, "r_multiple_expected": 2.0})
    assert v == "REVIEW" and r == ["R:R 2.0 marjinal"]
    assert _by(detail, "rr_floor")["passed"] is True
    d = _by(detail, "rr_marginal")
    assert d["passed"] is False and d["severity"] == "soft"
    assert d["note"] == "R:R 2.0 marjinal" and d["value"] == 2.0 and d["threshold"] == ">=2.3"


def test_s5_rr_marjinal_bandinin_ust_ucu_disaridadir():
    """`rr < 2.3` → `rr <= 2.3`: bandın TAM ucu artık marjinal değildir."""
    v, r, _ = _run(plan={**PLAN, "r_multiple_expected": 2.0 + 0.3})
    assert (v, r) == ("GO", [])


def test_s5_rr_sifirken_sert_veto_yok_yumusak_belirsizlik_bayragi_var():
    """`0.0 < rr` → `0.0 <= rr` (sert) ve `rr <= 0.0` → `rr < 0.0` (dal seçimi) mutantları.
    Ayrıca rr_defined düğümünün TÜM alanları: ad, sabit True, dizge, şiddet, value."""
    v, r, detail = _run(plan={**PLAN, "r_multiple_expected": 0.0})
    assert v == "REVIEW" and r == ["R:R belirsiz/sıfır"]
    assert "rr_marginal" not in _names(detail)
    d = _by(detail, "rr_defined")
    assert d["passed"] is False and d["severity"] == "soft"
    assert d["note"] == "R:R belirsiz/sıfır"
    assert d["value"] == 0.0 and d["threshold"] is None


def test_s5_rr_bir_iken_belirsiz_degil_marjinal_dalina_girer():
    """`rr <= 0.0` → `rr <= 1.0`: hüküm ikisinde de NO_GO kaldığı için fark YALNIZ karar
    ağacında görünür — dal adı sözleşmenin parçasıdır."""
    v, _, detail = _run(plan={**PLAN, "r_multiple_expected": 1.0})
    assert v == "NO_GO"
    assert "rr_marginal" in _names(detail) and "rr_defined" not in _names(detail)


# ============================================================================================
# S5: portföy ısısı — iki tavan, iki ayrı eşitlik sınırı
# SINIR DEĞERLERİ 5,0R'DE: OPERATÖR KARARI 2026-08-03 (d01ccb5) heat_hard_r'yi 4,5→5,0R taşıdı;
# LIMITS fikstüründe `heat_hard_r` YOKTUR, yani bu vakalar guard'ın FAIL-SAFE varsayılanını
# (HEAT_HARD_R) sınar ve sınır ancak o sayının üstünde/üstünde-değil olarak anlamlıdır.
# ============================================================================================
def test_s5_isi_sert_tavanina_tam_esitken_sert_veto_yok():
    """`open_heat > 5.0` → `>=`: 5.0R tam tavan SERT değil, yalnız yumuşak bayraktır."""
    port = {**PORT, "open_risk_r": 4.5}
    plan = {**PLAN, "size_r": 0.5}
    v, r, detail = _run(plan=plan, port=port)
    assert v == "REVIEW" and r == ["portföy ısısı yüksek (~5.0R açık risk)"]
    assert _by(detail, "heat_hard")["passed"] is True
    assert _by(detail, "heat_hard")["value"] == 5.0


def test_s5_isi_sert_tavanini_asinca_no_go():
    port = {**PORT, "open_risk_r": 4.6}
    plan = {**PLAN, "size_r": 0.5}
    v, r, detail = _run(plan=plan, port=port)
    assert v == "NO_GO" and r == ["portföy ısısı sert tavanı %5.0R aşıyor (~5.1R açık risk)"]
    assert _by(detail, "heat_hard")["severity"] == "hard"


def test_s5_isi_inceleme_esigine_tam_esitken_bayrak_yok():
    """`heat > 3.5` → `>=`: 3.5R tam eşik REVIEW üretmez."""
    port = {**PORT, "open_risk_r": 3.0}
    plan = {**PLAN, "size_r": 0.5}
    v, r, detail = _run(plan=plan, port=port)
    assert (v, r) == ("GO", [])
    assert _by(detail, "heat_review")["value"] == 3.5


def test_s5_isi_esigin_ustunde_bayrak_kaldirir():
    port = {**PORT, "open_risk_r": 3.1}
    plan = {**PLAN, "size_r": 0.5}
    v, r, detail = _run(plan=plan, port=port)
    assert v == "REVIEW" and r == ["portföy ısısı yüksek (~3.6R açık risk)"]
    d = _by(detail, "heat_review")
    assert d["severity"] == "soft" and d["value"] == 3.6 and d["threshold"] == "<=3.5R"


# ============================================================================================
# S5 + S7: sektör yığılması ve korelasyon
# ============================================================================================
def test_s5_sektorde_tek_pozisyon_bile_yigilma_bayragi_kaldirir():
    """`>= 1` → `> 1` / `>= 2` ve `portfolio.get("sector_counts", ...)` anahtar mutantları."""
    port = {**PORT, "sector_counts": {"tech": 1}}
    v, r, detail = _run(port=port)
    assert v == "REVIEW" and r == ["'tech' sektöründe korelasyon yığılması"]
    d = _by(detail, "sector_stacking")
    assert d["passed"] is False and d["severity"] == "soft"
    assert d["note"] == "'tech' sektöründe korelasyon yığılması"
    assert d["value"] == 1 and d["threshold"] == "0"
    assert _by(detail, "sector_cap")["value"] == 2      # sc.get(sec,0) + 1


def test_s5_korelasyon_esigine_tam_esitken_bayrak_yok():
    """`> 0.85` → `>= 0.85`."""
    v, r, detail = _run(port={**PORT, "max_corr": 0.85})
    assert (v, r) == ("GO", [])
    assert _by(detail, "correlation")["value"] == 0.85


def test_s7_correlation_mesaji_gercek_rho_yazar():
    """Mesajdaki ρ, portföyün GERÇEK max_corr'ı olmalı (yanlış anahtar → 0.00 yazardı)."""
    v, r, detail = _run(port={**PORT, "max_corr": 0.9})
    assert v == "REVIEW"
    assert r == ["açık pozisyonlarla yüksek korelasyon (ρ≈0.90) — gerçek konsantrasyon"]
    d = _by(detail, "correlation")
    assert d["severity"] == "soft" and d["value"] == 0.9 and d["threshold"] == "<=0.85"


def test_s5_korelasyon_olculemediginde_sifir_sayilir_bir_degil():
    """`portfolio.get("max_corr", 0.0)` varsayılanı 1.0 olsaydı ölçüm yokluğu KONSANTRASYON
    bayrağına dönerdi (uydurma yasağı: ölçülemeyen ≠ en kötü)."""
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0, "open_risk_r": 0.0}
    v, r, detail = _run(port=port)
    assert (v, r) == ("GO", [])
    assert _by(detail, "correlation")["value"] == 0.0


# ============================================================================================
# S7 + S4: leading_sector — join ayracı, dilim uzunluğu, threshold üretimi
# ============================================================================================
def test_s7_lider_sektor_mesaji_ilk_ucunu_virgul_bosluk_ile_listeler():
    reg = {"exposure_budget_pct": 60, "leading_sectors": ["a", "b", "c", "d"]}
    v, r, detail = _run(reg=reg)
    assert v == "REVIEW"
    assert r == ["'tech' bugünün lider sektörlerinde değil (a, b, c)"]
    d = _by(detail, "leading_sector")
    assert d["severity"] == "soft" and d["value"] == "tech" and d["threshold"] == "a,b,c"


def test_s5_lider_sektor_listesi_bosken_bayrak_kalkmaz_ve_esik_none_olur():
    reg = {"exposure_budget_pct": 60, "leading_sectors": []}
    v, r, detail = _run(reg=reg)
    assert (v, r) == ("GO", [])
    d = _by(detail, "leading_sector")
    assert d["passed"] is True and d["value"] == "tech" and d["threshold"] is None


# ============================================================================================
# S9: eksik alanların VARSAYILANLARI — "ölçülemedi" ile "sıfır" aynı şey değil
# ============================================================================================
def test_s9_tamamen_bos_girdilerde_kapi_patlamaz_ve_yalnizca_butce_vetosu_verir():
    """Bu tur, `.get(anahtar, VARSAYILAN)` varsayılanı None'a çevrilen tüm mutantları (float(None),
    None <= sayı, None.get(...)) TypeError/AttributeError ile düşürür; ayrıca 0 → 1 kayan
    varsayılanları hüküm ve karar ağacı üzerinden yakalar."""
    goal = _goal(max_position_r=0.5)
    v, r, detail = _run(plan={}, port={}, reg={}, goal=goal)
    assert v == "NO_GO"
    assert r == ["exposure_budget %0 — bugün yeni risk yok"], "R:R varsayılanı 0.0 olmalı, 1.0 değil"
    assert _names(detail) == [
        "exposure_budget", "max_open_positions", "sector_cap", "daily_loss_breaker",
        "position_size", "rr_floor", "heat_hard",
        "sector_stacking", "heat_review", "correlation", "leading_sector", "rr_defined"]
    beklenen = {
        "exposure_budget":    (0, ">0"),
        "max_open_positions": (0, "<5"),
        "sector_cap":         (1, "%60"),
        "daily_loss_breaker": (0.0, ">-%3"),
        "position_size":      (0, "<=0.5R"),
        "rr_floor":           (0.0, ">=2.0"),
        "heat_hard":          (0.0, "<=5.0R"),
        "sector_stacking":    (0, "0"),
        "heat_review":        (0.0, "<=3.5R"),
        "correlation":        (0.0, "<=0.85"),
        "leading_sector":     ("?", None),
        "rr_defined":         (0.0, None),
    }
    for name, (val, th) in beklenen.items():
        d = _by(detail, name)
        assert d["value"] == val, f"{name}.value → {d['value']!r} (beklenen {val!r})"
        assert d["threshold"] == th, f"{name}.threshold → {d['threshold']!r}"


def test_s9_sektoru_olmayan_plan_soru_isareti_ile_temsil_edilir():
    """`plan.get("sector", "?")` — varsayılan None olursa hüküm metni "'None'" yazardı."""
    plan = {"size_r": 0.5, "r_multiple_expected": 3.0}
    reg = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}
    v, r, detail = _run(plan=plan, port={**PORT, "sector_counts": {}}, reg=reg)
    assert v == "REVIEW"
    assert r == ["'?' bugünün lider sektörlerinde değil (tech)"]
    assert _by(detail, "leading_sector")["value"] == "?"


def test_s9_rr_anahtari_yanlis_okunursa_sifir_gorunurdu_bu_yuzden_gercek_deger_sinanir():
    """`plan.get("r_multiple_expected", ...)` anahtarı bozulursa rr 0.0'a düşer ve kapı
    "belirsiz" bayrağı kaldırır — temiz GO ile ayrışır."""
    v, r, detail = _run()
    assert (v, r) == ("GO", [])
    assert _by(detail, "rr_floor")["value"] == 3.14
    assert "rr_defined" not in _names(detail)


# ============================================================================================
# S5 + S7 + S4: score_band (yalnız params verildiğinde)
# ============================================================================================
def test_s5_params_yokken_skor_bandi_hic_calismaz():
    _, _, detail = _run(params=None)
    assert "score_band" not in _names(detail)


def test_s5_skor_min_score_arti_bant_altindayken_bayrak_kalkar():
    """`entry.min_score` anahtarı ve `min_score + REVIEW_SCORE_BAND` işareti."""
    plan = {**PLAN, "score": 85}
    v, r, detail = _run(plan=plan, params={"entry.min_score": 80})
    assert v == "REVIEW" and r == ["skor alt bantta"]
    d = _by(detail, "score_band")
    assert d["passed"] is False and d["severity"] == "soft"
    assert d["note"] == "skor alt bantta" and d["value"] == 85 and d["threshold"] == ">=90"


def test_s5_skor_tam_bant_ucundayken_bayrak_kalkmaz():
    """`<` → `<=`: min_score + 10 = 90 skoru artık 'alt bant' değildir."""
    v, r, _ = _run(plan={**PLAN, "score": 90}, params={"entry.min_score": 80})
    assert (v, r) == ("GO", [])


def test_s5_min_score_varsayilani_altmistir():
    """params boş sözlükken varsayılan 60 → bant tavanı 70; 61 olsaydı 70 skoru bayraklanırdı."""
    v, r, detail = _run(plan={**PLAN, "score": 70}, params={})
    assert (v, r) == ("GO", [])
    assert _by(detail, "score_band")["threshold"] == ">=70"


def test_s5_skoru_olmayan_plan_yuz_sayilir_yuzbir_degil():
    """`plan.get("score", 100)` varsayılanı: bant tavanı 100.5 iken 100 bayraklanır, 101 bayraklanmaz.

    NOT: karar ağacındaki `value` AYNI satırdan gelmez — orada varsayılan YOKTUR (`plan.get("score")`),
    yani skoru olmayan planda hüküm 100 üzerinden verilir ama ağaca None yazılır. Bu ayrım bilerek
    sınanıyor: iki okumadan biri sessizce diğerine benzetilirse ağaç hükmü yanlış açıklar."""
    plan = {"ticker": "AAA", "sector": "tech", "size_r": 0.5, "r_multiple_expected": 3.0}
    v, r, detail = _run(plan=plan, params={"entry.min_score": 90.5})
    assert v == "REVIEW" and r == ["skor alt bantta"]
    assert _by(detail, "score_band")["value"] is None
    assert _by(detail, "score_band")["threshold"] == ">=100"


# ============================================================================================
# S10: _y3_portfolio_caps çağrısı — dört argümanın DÖRDÜ de gerçek olmalı
# ============================================================================================
def test_s10_y3_sektor_tavani_knob_acikken_karar_agacina_girer_ve_dort_argumani_da_kullanir():
    """`_y3_portfolio_caps(plan, portfolio, params, _chk)` argümanlarından biri None'a çevrilirse
    ya blok tamamen sessizleşir (params=None) ya da patlar (plan/portfolio/_chk=None)."""
    port = {**PORT, "equity": 100000.0, "sector_notional": {"tech": 10000.0}}
    plan = {**PLAN, "notional": 5000.0}
    params = {"entry.min_score": 60, "portfolio.sector_cap": 25.0}
    v, r, detail = _run(plan=plan, port=port, params=params)
    assert (v, r) == ("GO", [])
    d = _by(detail, "y3_sector_cap")
    assert d["passed"] is True and d["severity"] == "hard"
    assert d["value"] == 15.0 and d["threshold"] == "<=25%"     # 100*(10000+5000)/100000


def test_s10_y3_sektor_tavani_asilinca_sert_veto_verir():
    port = {**PORT, "equity": 100000.0, "sector_notional": {"tech": 30000.0}}
    plan = {**PLAN, "notional": 5000.0}
    params = {"entry.min_score": 60, "portfolio.sector_cap": 25.0}
    v, r, _ = _run(plan=plan, port=port, params=params)
    assert v == "NO_GO" and r == ["Y3 sektör tavanı: 'tech' payı %35.0 > %25"]


# ============================================================================================
# S2: hüküm SIRASI — sert varsa yumuşak hiç dönmez (kapının üç durumlu sözleşmesi)
# ============================================================================================
def test_s2_sert_ihlal_varken_yumusak_bayraklar_hukmu_kirletmez():
    port = {**PORT, "open_positions": 5, "sector_counts": {"tech": 1}, "max_corr": 0.99}
    v, r, detail = _run(port=port)
    assert v == "NO_GO"
    assert r == ["max 5 pozisyon dolu"], "NO_GO turunda YALNIZ sert nedenler döner"
    assert _by(detail, "sector_stacking")["passed"] is False, "yumuşak kontrol yine de ÖLÇÜLÜR"
    assert _by(detail, "correlation")["passed"] is False


def test_s2_detail_out_verilmeden_de_ayni_hukum_cikar():
    """Karar ağacı bir GÖZLEM kanalıdır; hükmü DEĞİŞTİRMEZ."""
    port = {**PORT, "sector_counts": {"tech": 1}}
    a = guard.classify_gate(PLAN, port, REG, _goal(), None)
    b = _run(port=port)[:2]
    assert a == b == ("REVIEW", ["'tech' sektöründe korelasyon yığılması"])


@pytest.mark.parametrize("rr,beklenen", [(0.0, "REVIEW"), (0.5, "NO_GO"), (1.9999, "NO_GO"),
                                         (2.0, "REVIEW"), (2.2999, "REVIEW"), (2.3, "GO"),
                                         (5.0, "GO")])
def test_s5_rr_ekseninin_tamami_uc_duruma_dogru_bolunur(rr, beklenen):
    """Tek eksende üç durumun sınırları: (0, 2.0) sert, [2.0, 2.3) yumuşak, 0 ve ≥2.3 temiz."""
    v, _, _ = _run(plan={**PLAN, "r_multiple_expected": rr})
    assert v == beklenen
