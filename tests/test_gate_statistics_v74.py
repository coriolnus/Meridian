"""test_gate_statistics_v74.py — KAPI İSTATİSTİĞİ denetimi (2026-07-22, tur 74).

Dedektör bataryası kanıtın ÜRETİLDİĞİNİ, KORUNDUĞUNU ve BİRLEŞTİRİLDİĞİNİ ölçüyor. Ölçmediği tek şey:
sayıların İSTATİSTİKSEL OLARAK DOĞRU olup olmadığı. Bu dosya tam olarak onu ölçer — çünkü bu kapı,
canlı deftere hangi strateji sürümünün gireceğine karar veriyor; istatistiği yanlışsa sistem kendinden
emin biçimde YANLIŞ şeyi öğrenir ve aşağı akıştaki her sayı makul görünmeye devam eder.

Beyan edilen yasa: Search-OOS üzerinde blok-bootstrap EŞLEŞTİRİLMİŞ kapı, P(ΔS>0) ≥ 0.80, + fold
çoğunluğu + kuyruk vetosu; risk zarfı ise tek uygulama olarak guard.classify_gate.

DOSYANIN OKUNMA BİÇİMİ
  * `test_pc*`  — POZİTİF KONTROL: mekanizmanın DOĞRU çalıştığı, kanıtlanmış davranışlar.
  * `test_dfix*`— bu turda DÜZELTİLEN kusurun regresyon testi (sahip olunan dosyalarda).
  * `test_def*` — DOĞRULANMIŞ kusur; düzeltmesi YASAK bir dosyaya düşüyor. `xfail(strict=True)` ile
                  işaretli: bugün kırmızı-beklenen, düzeltildiği gün XPASS ile SUITE'i DÜŞÜRÜR ve
                  işaretin kaldırılmasını zorlar. Yani bulgu, yorum değil YÜRÜTÜLEBİLİR kanıttır.

Deterministik: sabit tohumlar, ağ yok, gerçek replay yok, canlı state'e yazım yok.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from meridian import backtest, config, guard, reflect, score as score_mod, store
from meridian.oos_pipeline import OutOfSamplePipeline, split_date
from meridian.probgate import PairedProbabilisticGate as Gate, META_FILE, P_BASE

# ---- üretim pencereleri (dataset.py ile birebir) -------------------------------------------------
IS_START = "2022-01-01"
OOS_START, OOS_END = "2023-07-01", "2025-12-31"
FOLDS = ["2023-07-01", "2024-04-01", "2025-01-01", "2025-12-31"]
EMBARGO = 10
S_END = split_date(OOS_START, OOS_END)                     # 2025-04-01
S_LO = backtest._embargoed_start(OOS_START, EMBARGO)       # 2023-07-11

N_BOOT = 600            # tam 2000 gerekmez: p'nin MC hatası ~0.02, iddialar 0.1+ uzakta


@pytest.fixture
def seeded(sandbox_state):
    """sandbox_state zaten goal/bounds'u kopyalıyor; kapı meta-kalibrasyonu nötrlenir."""
    store.write_json(META_FILE, {"extra_p": 0.0})
    config.goal.cache_clear()
    yield sandbox_state
    config.goal.cache_clear()


def _body(src: str, doc: str | None) -> str:
    """Kaynaktan DOCSTRING'i çıkarır. Kaynak-üzerinde-iddia eden testlerin klasik tuzağı: kusuru
    ANLATAN yorum, kusurun KENDİSİ sanılıp eşleşiyor. Yalnız yürütülen gövdeye bak."""
    return src.replace(doc, "") if doc else src


def trades(n, seed, lo, hi, r_mu, hold=4):
    """[lo, hi) içinde n adet kapalı işlem; R ~ N(r_mu, 1). Tamamen deterministik."""
    rng = np.random.default_rng(seed)
    d0 = dt.date.fromisoformat(lo)
    span = max(1, (dt.date.fromisoformat(hi) - d0).days - hold - 1)
    out = []
    for _ in range(n):
        off = int(rng.integers(0, span))
        r = float(rng.normal(r_mu, 1.0))
        out.append({"ts_open": (d0 + dt.timedelta(days=off)).isoformat(),
                    "ts_close": (d0 + dt.timedelta(days=off + hold)).isoformat(),
                    "regime": "trend_up", "r_multiple": round(r, 3),
                    "pnl_dollars": round(r * 400.0, 2)})
    return out


# SEARCH'e daraltılmış fold sınırları — ÜRETİCİYLE AYNI türetme (backtest.walk_forward, 2026-07-22).
# Bu yardımcı `walk_forward` çıktısını elle taklit ediyor; taklidin YASASI da üreticininkiyle aynı
# olmalı, yoksa test kendi kopyasını doğrular ve gerçek düzeltmeyi göremez (fikstür tuzağı).
SEARCH_FOLDS = [b for b in FOLDS if b < S_END] + [S_END]


def wf(all_trades, goal):
    """walk_forward'ın ÜRETTİĞİ sözlüğün birebir şekli — dilimler/foldlar/kuyruk aynı yasalarla.
    Fold ve kuyruk YALNIZ Search-OOS'tan hesaplanır: Confirm dilimi aramanın hiçbir parçasına
    girmez (kazananın-laneti savunması bunun üzerine kurulu)."""
    _in = backtest._in_segment
    oos = [t for t in all_trades if _in(t, S_LO, OOS_END)]
    search = [t for t in all_trades if _in(t, S_LO, S_END)]
    return {"oos_score": score_mod.score_detail(oos, goal)["score"],
            "oos_folds": backtest._fold_metrics(all_trades, SEARCH_FOLDS, EMBARGO),
            "oos_tail_risk": score_mod.tail_risk(search),
            "holdout_score": None,
            "oos_split": {"search_start": S_LO, "search_end": S_END,
                          "confirm_start": S_END, "confirm_end": OOS_END},
            "_trades_search": [t for t in all_trades if _in(t, S_LO, S_END)],
            "_trades_confirm": [t for t in all_trades if _in(t, S_END, OOS_END)]}


# =================================================================================================
# POZİTİF KONTROLLER — mekanizmanın sağlam olduğu, KANITLANMIŞ kısmı
# =================================================================================================
def test_pc1_identical_candidate_can_never_pass(seeded):
    """Aday incumbent'ın BİREBİR aynısıysa her replikasyonda ΔS=0'dır; P(ΔS>0) 0 olmalı.
    Eşleştirmenin (aynı bloklar, iki tarafa da) çalıştığının en sert kanıtı: eşleştirme bozuk olsaydı
    ortak gürültü sönmez ve P ~0.5 civarında salınırdı."""
    goal = config.goal()
    inc = trades(90, 1, S_LO, S_END, 0.05)
    r = Gate(goal, n_boot=N_BOOT, seed=42).evaluate(inc, [dict(t) for t in inc], S_LO, S_END)
    assert r.law == "probabilistic" and r.n_valid == N_BOOT
    assert r.p == 0.0 and r.mean_delta == 0.0
    assert r.passes is False

    # ...ve kapının TAMAMI da (fold + kuyruk dahil) reddetmeli
    all_tr = inc + trades(30, 2, S_END, OOS_END, 0.05)
    w = wf(all_tr, goal)
    passes, gate, why = reflect._gate_eval(w, {**w, "_trades_search": list(w["_trades_search"])}, k_probes=1)
    assert passes is False and gate["search_p"] == 0.0


def test_pc2_uniformly_better_candidate_passes(seeded):
    """Her tek işlemde daha iyi olan aday geçmeli — kapı yalnız reddetmeyi değil, KABUL ETMEYİ de
    becerebilmeli, yoksa öğrenme döngüsü yapısal olarak ölür."""
    goal = config.goal()
    inc = trades(90, 1, S_LO, S_END, 0.05)
    better = [{**t, "r_multiple": round(t["r_multiple"] + 0.5, 3),
               "pnl_dollars": round(t["pnl_dollars"] + 200.0, 2)} for t in inc]
    r = Gate(goal, n_boot=N_BOOT, seed=42).evaluate(inc, better, S_LO, S_END)
    assert r.law == "probabilistic" and r.passes is True
    assert r.p >= 0.95 and r.mean_delta > 0

    d_i = score_mod.score_detail(inc, {**goal, "min_sample": 1}, span_days=630)
    d_c = score_mod.score_detail(better, {**goal, "min_sample": 1}, span_days=630)
    assert d_c["score"] > d_i["score"], "kompozit skor gerçek iyileşmeyi görebilmeli (kırpma doygunluğu yok)"


def test_pc3_edge_only_inside_the_training_window_never_reaches_the_gate(seeded):
    """SIZINTI KONTROLÜ: iyileşmesi TAMAMEN IS penceresinde olan aday geçmemeli.
    Ayrıca sınırı AŞAN işlem (IS'te açılıp OOS'ta kapanan) HİÇBİR dilime sayılmamalı — purge."""
    goal = config.goal()
    common = trades(90, 1, S_LO, S_END, 0.05) + trades(30, 2, S_END, OOS_END, 0.05)
    is_inc = trades(60, 3, IS_START, OOS_START, 0.05)
    is_cand = [{**t, "r_multiple": round(t["r_multiple"] + 3.0, 3),
                "pnl_dollars": round(t["pnl_dollars"] + 1200.0, 2)} for t in is_inc]

    # IS penceresinde aday açık ara önde...
    is_i = backtest.segment_score(is_inc + common, {**goal, "min_sample": 1}, IS_START, OOS_START)
    is_c = backtest.segment_score(is_cand + common, {**goal, "min_sample": 1}, IS_START, OOS_START)
    assert is_c["score"] > is_i["score"] + 0.10, "kurgu geçersiz: IS'te fark yok"

    # ...ama kapı bunu GÖREMEZ: OOS/arama dilimleri birebir aynı, karar 'geçmez'
    wi, wc = wf(is_inc + common, goal), wf(is_cand + common, goal)
    assert wi["_trades_search"] == wc["_trades_search"]
    passes, gate, _why = reflect._gate_eval(wi, wc, k_probes=1)
    assert passes is False and gate["search_p"] == 0.0

    # purge: sınırı aşan işlem ne IS'e ne OOS'a sayılır
    straddler = {"ts_open": "2023-06-25", "ts_close": "2023-07-20", "r_multiple": 9.0,
                 "pnl_dollars": 9000.0}
    assert backtest._in_segment(straddler, IS_START, OOS_START) is False
    assert backtest._in_segment(straddler, S_LO, OOS_END) is False


def test_pc4_embargo_is_applied_on_every_gate_path_and_cannot_be_silent(seeded, monkeypatch):
    """Ambargo, kapının HER yolunda (büyüklük dilimi, foldlar, kuyruk vetosu) aynı alt sınırı üretmeli;
    ve uygulanamazsa SESSİZ kalamaz — no-op'a düşen bir ambargo eğitim/sınav pencerelerini bitiştirir."""
    assert backtest._embargoed_start(OOS_START, EMBARGO) == "2023-07-11"

    seen = []
    monkeypatch.setattr(backtest, "_warn_once", lambda ev, **kw: seen.append((ev, kw)))
    backtest._WARNED.discard("embargo_disabled")
    assert backtest._embargoed_start("BOZUK-TARIH", EMBARGO) == "BOZUK-TARIH"
    assert seen and seen[0][0] == "embargo_disabled", "ambargo sessizce kapanamaz"

    # foldlar da aynı ambargoyu uygular (aynı olay adıyla uyarır) ve aynı üyelik yasasını kullanır
    seen.clear()
    backtest._fold_metrics([], ["BOZUK", "2024-01-01"], EMBARGO)
    assert seen and seen[0][0] == "embargo_disabled"

    # büyüklük dilimi ile kuyruk vetosu AYNI popülasyonu görür (L1)
    tr = trades(40, 5, OOS_START, OOS_END, 0.05)
    lo = backtest._embargoed_start(OOS_START, EMBARGO)
    mag = [t for t in tr if backtest._in_segment(t, lo, OOS_END)]
    assert all(t["ts_open"] >= lo for t in mag)


def test_pc5_risk_envelope_has_exactly_one_implementation_and_no_llm_can_move_it(seeded):
    """guard.classify_gate SERT zarfın TEK kaynağı: check_trade onu TÜRETİR (kopya taşımaz), ve
    classify_gate saf bir fonksiyondur — LLM/danışman katmanının girebileceği hiçbir kanal yok."""
    import ast
    import inspect
    src = _body(inspect.getsource(guard.check_trade), guard.check_trade.__doc__)
    assert "classify_gate(" in src, "check_trade zarfı TÜRETMELİ, kopyalamamalı"
    for tok in ("DISCIPLINE_MIN_RR", "HEAT_HARD_R", "max_open_positions", "max_sector_exposure_pct"):
        assert tok not in src, f"check_trade sert kural KOPYASI taşıyor: {tok}"

    # guard'ın TÜM içe aktarımları: LLM/ağ/defter kanalı YOK → verdict yalnız argümanlarının fonksiyonu
    tree = ast.parse(inspect.getsource(guard))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mods.update([(node.module or "").split(".")[0]] + [a.name for a in node.names])
    assert mods <= {"", "__future__", "annotations", "dataclasses", "dataclass",
                    "typing", "Optional", "config"}, \
        f"guard'a dış kanal sızmış: {sorted(mods)}"

    goal, params = config.goal(), {"entry.min_score": 60}
    plan = {"ticker": "AAPL", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 3.0, "score": 90}
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0, "open_risk_r": 0.0, "max_corr": 0.0}
    reg = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}
    a = guard.classify_gate(plan, port, reg, goal, params)
    b = guard.classify_gate(plan, port, reg, goal, params)
    assert a == b == ("GO", [])

    # NO_GO gerçekten geçirmez ve check_trade ile ASLA ayrışmaz (144 senaryolu diferansiyel)
    for rr in (0.5, 2.1, 3.0):
        for openp in (0, 4, 5):
            for heat in (0.0, 3.0, 4.4):
                for budget in (0, 60):
                    p2 = {**plan, "r_multiple_expected": rr}
                    pf = {**port, "open_positions": openp, "open_risk_r": heat}
                    v, _ = guard.classify_gate(p2, pf, {**reg, "exposure_budget_pct": budget}, goal, params)
                    ct = guard.check_trade(p2, pf, {**reg, "exposure_budget_pct": budget}, goal)
                    assert ct.ok is (v != "NO_GO"), f"iki yüzey ayrıştı: {v} vs {ct.ok}"


# =================================================================================================
# BU TURDA DÜZELTİLEN KUSURLAR (sahip olunan dosyalar) — regresyon
# =================================================================================================
def test_dfix1_ledger_carries_the_bootstrap_denominator(seeded):
    """KUSUR (probgate.GateResult.as_gate_fields): defter n_valid yazıyor ama n_boot YAZMIYORDU.
    Skorlanamayan replikasyonlar sessizce düşüyor ve P yalnız AYAKTA KALANLAR üzerinden hesaplanıyor;
    paydasız bir n_valid, 1200/1200 ile 1200/2000'i (yani %40'ı elenmiş SEÇİLMİŞ bir altkümeyi)
    ayırt edilemez kılıyordu. Bozacağı karar: kapı kaydına bakan hiç kimse 'bu olasılık kaç
    replikasyondan çıktı' sorusunu cevaplayamıyordu."""
    goal = config.goal()
    r = Gate(goal, n_boot=N_BOOT, seed=42).evaluate(
        trades(90, 1, S_LO, S_END, 0.05), trades(90, 2, S_LO, S_END, 0.30), S_LO, S_END)
    f = r.as_gate_fields("search")
    assert f["search_n_boot"] == N_BOOT
    assert 0 < f["search_n_valid"] <= f["search_n_boot"]

    # ve kapı kaydının kendisinde de görünmeli (reflect._gate_eval bunu doğrudan yayar)
    all_i = trades(90, 1, S_LO, S_END, 0.05) + trades(30, 3, S_END, OOS_END, 0.05)
    all_c = trades(90, 2, S_LO, S_END, 0.30) + trades(30, 4, S_END, OOS_END, 0.30)
    _p, gate, _w = reflect._gate_eval(wf(all_i, goal), wf(all_c, goal), k_probes=1)
    assert "search_n_boot" in gate and gate["search_n_boot"] > 0


def test_dfix2_tail_veto_noise_is_smaller_than_its_own_margin(seeded):
    """KUSUR (score.tail_risk): sims=4000 iken SABİT veride yalnız tohumu değiştirmek cvar_r'yi 0.91R,
    var_r'yi 0.64R oynatıyordu — oysa reflect.TAIL_MARGIN_R = 0.5R SERT bir veto eşiği. Yani vetonun
    karar sınırı kendi Monte Carlo gürültüsünün İÇİNDEYDİ. Bozacağı karar: 'aday kuyruk riskini
    kötüleştiriyor' vetosu, marja yakın her adayda fiilen yazı-tura idi (sabit tohum bunu
    TEKRARLANABİLİR yapar, DOĞRU yapmaz). sims=20000 → gürültü marjın yarısının altında."""
    rng = np.random.default_rng(3)
    tr = [{"r_multiple": float(x)} for x in rng.normal(0.05, 1.0, 60)]
    v = [score_mod.tail_risk(tr, seed=s)["var_r"] for s in range(1, 16)]
    c = [score_mod.tail_risk(tr, seed=s)["cvar_r"] for s in range(1, 16)]
    assert max(v) - min(v) < reflect.TAIL_MARGIN_R / 2.0, f"var_r MC yayılımı {max(v)-min(v):.3f}R"
    assert max(c) - min(c) < reflect.TAIL_MARGIN_R / 2.0, f"cvar_r MC yayılımı {max(c)-min(c):.3f}R"

    # ve eski iddia artık DOĞRU: çekiliş BOYUTTAN BAĞIMSIZ, yani iki taraf aynı göreli konumlardan
    # örneklenir (eskiden `rng.integers(0, rs.size)` üst sınırı boyuta bağlıydı → farklı çekiliş)
    import inspect
    tsrc = _body(inspect.getsource(score_mod.tail_risk), score_mod.tail_risk.__doc__)
    assert "rng.integers(0, rs.size" not in tsrc
    assert "rng.random((sims" in tsrc
    a, b = score_mod.tail_risk(tr), score_mod.tail_risk(tr)
    assert a == b and a["var_r"] <= a["cvar_r"]                 # determinizm + VaR ≤ CVaR korunur
    assert score_mod.tail_risk([{"r_multiple": 1.0}] * 5) is None   # ince dilimde UYDURMA yok


# =================================================================================================
# DOĞRULANMIŞ KUSURLAR — düzeltmesi YASAK dosyalara düşüyor (xfail strict)
# =================================================================================================
def test_search_verdict_does_not_depend_on_confirm_window_data(seeded):
    """oos_pipeline'ın merkezi iddiası: 'Confirm-OOS, aramanın ASLA dokunmadığı dilimdir' — kazananın
    -laneti savunmasının TAMAMI buna dayanıyor. Değil.

    Kurgu: iki aday, arama diliminde BİREBİR AYNI işlemlere sahip (search_p ikisinde de 0.9965), yalnız
    teyit dilimindeki işlemleri farklı. Kapı yine de FARKLI karar veriyor (A geçiyor, B fold-çoğunluğunu
    ve kuyruk vetosunu kaybediyor). Yani arama, kazananı teyit penceresine BAKARAK seçiyor; sonra
    submit() aynı pencerede 'dokunulmamış teyit yürüyüşü' koşturuyor. Bozduğu karar: teyit adımı bir
    bağımsız sınav değil, ön-elemesi zaten o pencerede yapılmış bir adayın yeniden sınanmasıdır —
    v2'de +0.059 arama → −0.036 canlı olarak ödenen kazananın-laneti savunmasız kalır."""
    goal = config.goal()
    inc = trades(90, 11, S_LO, S_END, 0.02) + trades(40, 12, S_END, OOS_END, 0.02)
    shared = trades(90, 21, S_LO, S_END, 0.55)
    cand_a = shared + trades(40, 31, S_END, OOS_END, 0.60)
    cand_b = shared + trades(40, 31, S_END, OOS_END, -0.90)

    wi, wa, wb = wf(inc, goal), wf(cand_a, goal), wf(cand_b, goal)
    assert wa["_trades_search"] == wb["_trades_search"], "kurgu geçersiz: arama dilimleri farklı"
    pa, ga, _ = reflect._gate_eval(wi, wa, k_probes=1)
    pb, gb, _ = reflect._gate_eval(wi, wb, k_probes=1)
    assert ga["search_p"] == gb["search_p"]          # arama olasılığı gerçekten aynı
    assert pa == pb, (f"arama kararı teyit verisine bağlı: A={pa} B={pb} "
                      f"(fold {ga['fold_wins']} vs {gb['fold_wins']}, "
                      f"tail {ga['tail_ok']} vs {gb['tail_ok']})")


def test_multiple_comparisons_correction_keeps_growing(seeded):
    """Arama tipik olarak budget=10 ile 40'a kadar sonda planlar (reflect: probes[:max(budget*4,40)])
    ve K = TOPLAM sonda sayısı olarak kapıya gider. Ceza `min(0.95, 0.80 + 0.01·(K−1))`:

      K=16 → 0.95 (tavan)   K=40 → 0.95   K=400 → 0.95

    ÖLÇÜM (bu dosyanın altındaki Monte Carlo ile aynı kurgu, 60 null aday): p≥0.95 için sonda-başı
    yanlış-geçiş oranı 0.033. K=40'ta aile-çapı en az bir yanlış geçiş olasılığı 1−0.967^40 = 0.74;
    K=100'de 0.97. Gerçek Bonferroni (aile α=0.20) K=40 için p ≥ 1 − 0.20/40 = 0.995 isterdi.
    Bozduğu karar: kapının 'kazananın-laneti cezası' 16 sondadan sonra hiç artmıyor, yani geniş bir
    arama neredeyse KESİN olarak şansa dayalı bir kazanan üretir ve o kazanan canlı deftere girer."""
    # DÜZELTİLDİ (2026-07-22): doğrusal +0.01 ve 0.95 tavanı yerine GERÇEK Bonferroni —
    # p_req = 1 − α_aile/K. Ceza K büyüdükçe büyümeye DEVAM eder.
    assert Gate.p_required_for(40) >= 1.0 - 0.20 / 40, (
        f"K=40 için istenen p yalnız {Gate.p_required_for(40)} — Bonferroni 0.995 ister")
    assert Gate.p_required_for(100) > Gate.p_required_for(40) > Gate.p_required_for(16), \
        "ceza hâlâ bir yerde DONUYOR — geniş arama dar aramayla aynı çıtayı ödüyor"
    assert Gate.p_required_for(1) == pytest.approx(0.80), "tek aday davranışı değişmemeli"


def test_meta_calibration_tightens_a_real_search(seeded):
    """'öneri #4' kapının kendi iyimserliğini ölçüp KENDİNİ SIKILAŞTIRMASI için var. Ama ofset tavanın
    ALTINDA toplandığı için, gerçek bir aramada (K=40) hiçbir etkisi yok: sistem 'öngörülerimin dörtte
    biri bile gerçekleşmiyor' tespitini yapıp extra_p=0.05 yazsa bile kapı hiç sıkılaşmaz.
    Bozduğu karar: ölçülmüş iyimserlik düzeltmesi, tam da gerektiği yerde (geniş arama) devre dışı."""
    store.write_json(META_FILE, {"extra_p": 0.0}); gevsek = Gate.p_required_for(40)
    store.write_json(META_FILE, {"extra_p": 0.10}); siki = Gate.p_required_for(40)
    assert siki > gevsek, f"meta-kalibrasyon K=40'ta etkisiz ({gevsek} → {siki})"


def test_single_window_edge_cannot_claim_robustness(seeded):
    """Fold-çoğunluğunun beyan edilmiş amacı: 'edge TEK bir şanslı pencereye dayanamasın'. Uygulama
    tam da bu durumda kapanıyor.

    Kurgu: aday YALNIZCA fold1 içinde işlem yapıyor (60 işlem, avg_r=+0.93) ve fold2/fold3'te sıfır.
    n<3 olan foldlar sayımdan düşünce fold_total=1 kalıyor; `fold_total >= 2 else True` kuralı
    çoğunluğu BEDAVA veriyor ve kapı geçiyor (search_p=0.9995, fold_wins=1/1). Yani sağlamlık testi,
    var olma nedeni olan arıza deseni tarafından devre dışı bırakılıyor. Bozduğu karar: tek bir
    rejime/pencereye sıkışmış bir edge 'çok pencerede doğrulandı' etiketiyle canlı deftere girer."""
    goal = config.goal()
    inc = (trades(60, 1, S_LO, "2024-04-01", 0.05) + trades(60, 2, "2024-04-11", "2025-01-01", 0.05)
           + trades(60, 3, "2025-01-11", OOS_END, 0.05))
    cand = trades(60, 11, S_LO, "2024-04-01", 0.95)          # SADECE fold1
    wi, wc = wf(inc, goal), wf(cand, goal)
    assert [f["n"] for f in wc["oos_folds"]] == [60, 0, 0], "kurgu geçersiz"
    passes, gate, _why = reflect._gate_eval(wi, wc, k_probes=1)
    assert passes is False, (f"tek pencereye sıkışmış edge kapıyı geçti "
                             f"(fold_wins={gate['fold_wins']}, search_p={gate['search_p']})")


def test_confirmation_walk_enforces_a_minimum_sample_floor(seeded):
    """Arama diliminde `thin` tabanı var (min(inc,cand) ≥ 0.7·min_sample); TEYİT diliminde YOK.
    Teyit dilimi OOS'un %30'u, yani tipik olarak bir avuç işlem. Bootstrap içinde min_sample=1'e
    bypass edildiği için 6 işlemle bile 'probabilistic' yasa altında rahatça p≥0.70 üretiliyor.
    Bozduğu karar: kazananın-lanetine karşı SON savunma olan teyit adımı, kanıt yokken de 'teyit
    edildi' der ve deftere yazılan sapmasız predicted_delta 6 işlemden türetilir."""
    goal = config.goal()
    inc_c, cand_c = trades(6, 1, S_END, OOS_END, 0.0), trades(6, 2, S_END, OOS_END, 0.9)
    shape = {"oos_split": {"search_start": S_LO, "search_end": S_END,
                           "confirm_start": S_END, "confirm_end": OOS_END}, "_trades_search": []}
    conf = OutOfSamplePipeline(goal, n_boot=N_BOOT).confirm({**shape, "_trades_confirm": inc_c},
                                                            {**shape, "_trades_confirm": cand_c})
    assert not (conf.law == "probabilistic" and conf.passes), (
        f"6 işlem/tarafla teyit GEÇTİ: p={conf.p} (n_valid={conf.n_valid})")


def test_probabilistic_law_cannot_ship_an_unmeasured_candidate(seeded):
    """goal.yaml DEĞİŞTİRİLEMEZ ve `min_sample: 30` diyor; score.py de 30'un altında dürüstçe None
    döndürüyor. Ama olasılıksal dalda `magnitude_ok = prob.passes and not thin` — `cand_oos is not None`
    kontrolü YOK ve `thin` tabanı 0.7·30 = 21. Sonuç: 26 kapalı işlemi olan (yani kompozit skoru
    TANIMSIZ) bir aday kapıyı GEÇİYOR ve scoreboard'a `backtest_oos: None` yazılıyor.
    Bozduğu karar: değiştirilemez sayılan örneklem tabanı, kapının kendi katmanında %30 gevşetilmiş."""
    goal = config.goal()
    inc = trades(22, 1, S_LO, S_END, 0.02) + trades(4, 2, S_END, OOS_END, 0.02)
    cand = trades(22, 11, S_LO, S_END, 0.90) + trades(4, 12, S_END, OOS_END, 0.90)
    wi, wc = wf(inc, goal), wf(cand, goal)
    assert wc["oos_score"] is None, "kurgu geçersiz: aday zaten min_sample'ı geçiyor"
    passes, gate, _why = reflect._gate_eval(wi, wc, k_probes=1)
    assert passes is False, (f"OOS skoru TANIMSIZ (n=26 < min_sample={goal['min_sample']}) olan aday "
                             f"kapıyı geçti: candidate_oos={gate['candidate_oos']}, "
                             f"search_p={gate['search_p']}")


def test_tail_veto_bites_when_either_metric_worsens(seeded):
    """Sermaye koruma vetosunun VE'si, iki ölçütten yalnız birinin kötüleşmesini bağışlıyor. Oysa CVaR
    (beklenen kayıp fazlası) tam da VaR'ın GÖREMEDİĞİ uzak kuyruğu ölçer: aynı %5 kantili koruyup
    ötesini kalınlaştıran bir aday — yani kuyruk riskinin ders kitabı tanımı — vetodan muaf.
    Bozduğu karar: 'aday OOS kuyruk riskini kötüleştiremez' yasası, kuyruğun kendisinde delik."""
    goal = config.goal()
    base_i = trades(60, 1, S_LO, S_END, 0.05) + trades(20, 2, S_END, OOS_END, 0.05)
    base_c = trades(60, 3, S_LO, S_END, 0.20) + trades(20, 4, S_END, OOS_END, 0.20)
    wi, wc = wf(base_i, goal), wf(base_c, goal)
    wi = {**wi, "oos_tail_risk": {"var_r": 3.0, "cvar_r": 3.5}}
    wc = {**wc, "oos_tail_risk": {"var_r": 3.0, "cvar_r": 9.0}}   # VaR aynı, CVaR 2.6 kat kötü
    _passes, gate, _why = reflect._gate_eval(wi, wc, k_probes=1)
    assert gate["tail_ok"] is False, (
        f"CVaR {wi['oos_tail_risk']['cvar_r']}→{wc['oos_tail_risk']['cvar_r']} "
        f"({reflect.TAIL_MARGIN_R}R marjının 11 katı) vetoyu tetiklemedi")


def test_def8_rollback_compares_scores_with_incompatible_annualization(seeded):
    """KUSURUN BÜYÜKLÜĞÜ — ve 2026-07-29'da kararın ondan KOPARILDIĞININ çivisi.

    ÖLÇÜLEN OLGU (değişmedi ve bu test hâlâ onu ölçer): `score_mod.score(trades, goal)` span_days
    VERMEZ, yani yıllıklandırma paydası canlı işlem kümesinin KENDİ süresidir; `backtest_oos` ise
    segmentin takvim uzunluğuyla (903 gün) yıllıklandırılmıştır. AYNI 30 işlem, yalnız payda
    değişerek ~0.21 skor farkı üretir — `goal.rollback_if_worse_by = 0.10` eşiğinin iki katı.
    Bu, `backtest.segment_score` docstring'indeki audit #5'in geri alma yolundan geri gelmiş hâli.

    NE DEĞİŞTİ (Aşama 2.3): kusur artık KARARI YÖNETMİYOR. `rollback` geri alma adayı
    tetiklendiğinde ebeveyn parametrelerini çocuğun AYNI canlı döneminde replay eder ve iki tarafı
    da `backtest.segment_score` ile AYNI pencerede puanlar (`baseline.would_have_replay`); karar o
    simetrik çiftten gelir ve `karar_yontemi` ile damgalanır. Yukarıdaki payda çarpıklığı yalnız
    would-have ÖLÇÜLEMEDİĞİNDE (bar önbelleği yok, anlık görüntü yok) devreye giren `legacy`
    yolunda hayatta kalır — ve orada da artık damgalıdır, yani denetimde görünür.
    Bu test bu yüzden ne silindi ne xfail edildi: ölçtüğü aritmetik olgu hâlâ doğru, ama kararın
    ona bağlı OLMADIĞI aşağıda ayrıca çivileniyor."""
    goal = config.goal()
    rng = np.random.default_rng(5)
    d0 = dt.date(2026, 1, 1)
    live = [{"ts_open": (d0 + dt.timedelta(days=int(i * 2))).isoformat(),
             "ts_close": (d0 + dt.timedelta(days=int(i * 2) + 3)).isoformat(),
             "r_multiple": round(float(rng.normal(0.05, 1.0)), 3),
             "pnl_dollars": round(float(rng.normal(0.05, 1.0)) * 400, 2)} for i in range(30)]

    as_rollback_reads_it = score_mod.score(live, goal)                        # payda = küme süresi
    in_backtest_oos_units = score_mod.score_detail(live, goal, span_days=903)["score"]
    assert as_rollback_reads_it is not None and in_backtest_oos_units is not None
    gap = abs(as_rollback_reads_it - in_backtest_oos_units)
    assert gap > float(goal["rollback_if_worse_by"]), (
        f"kurgu geçersiz — fark {gap:.4f} eşiğin altında kaldı")
    # kaynağı: yalnız yıllıklandırma paydası
    assert score_mod._span_days(live) < 120 < 903

    # KARAR ARTIK BU ÇİFTTEN GELMİYOR: ölçülmüş bir would-have varken karar simetrik çifti okur ve
    # yöntemini damgalar. Bu satır düşerse, geri alma sessizce eski asimetrik kıyasa dönmüş demektir.
    from meridian import baseline, rollback
    wh = {"verdict": "olculdu", "yontem": baseline.WOULD_HAVE_YONTEM,
          "canli_skor": -0.20, "would_have_skor": -0.18, "delta": -0.02}
    karar = rollback._karar_girdisi(cur_score=as_rollback_reads_it,
                                    par_score=in_backtest_oos_units, wh=wh)
    assert karar["yontem"] == baseline.WOULD_HAVE_YONTEM, "karar eski asimetrik kıyasa dönmüş"
    assert karar["delta"] == pytest.approx(-0.02), (
        f"karar deltası simetrik çiftten gelmiyor: {karar}")
    assert abs(karar["delta"]) < float(goal["rollback_if_worse_by"]) < gap, (
        "kurgunun anlamı: payda çarpıklığı eşiği aşarken simetrik kıyas aşmıyor — "
        "yani karar artık takvime değil ölçüme bağlı")


def test_def9_sharpe_measurable_is_dropped_at_the_reporting_boundary(seeded):
    """DOĞRULANMIŞ KUSUR — düzeltmesi run.py/api.py/web/app.js'te. Bu test kapsamı SINIRLAR:
    KAPI tüketicisi sağlam (ölçülemeyen Sharpe kompozit içinde 0 kalır ve eşiği GEVŞETMEZ), ama
    RAPOR tüketicileri bayrağı taşımaz — panoda 'Sharpe 0.0' yazar ve 'ölçtük, sıfır çıktı' okunur."""
    goal = config.goal()
    thin = score_mod.score_detail([{"r_multiple": 0.1, "pnl_dollars": 40.0,
                                    "ts_open": "2024-01-0%d" % (i + 1),
                                    "ts_close": "2024-01-0%d" % (i + 2)} for i in range(2)],
                                  {**goal, "min_sample": 1})
    assert thin["sharpe"] == 0.0 and thin["sharpe_measurable"] is False
    # KAPI tarafı dürüst: 0.0 muhafazakâr, min_sharpe eşiğini gevşetmiyor
    assert thin["components"]["sharpe"] == 0.0
    assert thin["sharpe"] <= float(goal["min_sharpe"])

    # RAPOR tarafı: run.py aynı sözlükten 'sharpe' alıp 'sharpe_measurable'ı DÜŞÜRÜYOR
    src = (config.STATE.parent.parent / "meridian" / "run.py")
    if not src.exists():
        import pathlib
        src = pathlib.Path(__file__).resolve().parent.parent / "meridian" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert '"sharpe": detail.get("sharpe")' in text
    assert "sharpe_measurable" not in text, "run.py düzeltilmiş — bu testi güncelle"


# =================================================================================================
# ÖLÇÜM: çoklu-karşılaştırma yanlış-geçiş oranı (def2'nin aritmetiğinin kanıtı)
# =================================================================================================
def test_measurement_null_candidates_false_pass_rate(seeded):
    """Gerçek edge'i OLMAYAN adaylar üzerinde ölçülmüş yanlış-geçiş oranı. p, null altında kabaca
    tekdüze dağılır (medyan ~0.5); dolayısıyla p≥0.95 çıtası sonda başına ~%5 yanlış geçiş bırakır ve
    bu K ile ÇARPILIR. Test, oranın 0'a çökmediğini (yani def2'nin gerçek olduğunu) sabitler."""
    goal = config.goal()
    inc = trades(90, 1000, S_LO, S_END, 0.05)
    gate = Gate(goal, n_boot=300, seed=42)
    ps = [gate.evaluate(inc, trades(90, 2000 + k, S_LO, S_END, 0.05), S_LO, S_END).p for k in range(40)]
    ps = np.array([p for p in ps if p is not None], dtype=float)
    assert ps.size == 40
    assert 0.25 < float(np.median(ps)) < 0.80, "null altında p ~tekdüze olmalı, 0/1'e çökmemeli"
    assert float(np.mean(ps >= P_BASE)) >= 0.10, "K=1 çıtası (0.80) null adayların ~%20'sini geçiriyor"
    fp = float(np.mean(ps >= 0.95))                      # K>=16'da DONAN gerçek çıta
    assert fp > 0.0, "null adaylarda hiç yanlış geçiş yok — ölçüm kurgusu bozuk"
    # K=40'lık gerçek bir aramada aile-çapı EN AZ BİR yanlış geçiş olasılığı
    assert 1.0 - (1.0 - fp) ** 40 > 0.50, f"sonda-başı yanlış geçiş {fp:.3f}"


def test_the_helper_mirrors_the_real_producer(seeded):
    """FİKSTÜR TUZAĞI KİLİDİ (2026-07-22). Bu dosyanın `wf()` yardımcısı `walk_forward` çıktısını
    ELLE taklit ediyor. Confirm-OOS sızıntısı düzeltildiğinde taklit eski yasayı kopyalamaya devam
    etti ve test — düzeltme yapılmış olmasına rağmen — hâlâ sızıntı raporladı: kendi kopyasını
    doğruluyordu, üreticiyi değil. Taklit ile üretici AYNI yasayı kullanmalı, yoksa bu dosyadaki
    hiçbir yeşil bir şey kanıtlamaz."""
    import inspect
    src = inspect.getsource(backtest.walk_forward)
    assert "_search_folds" in src and "_search_end" in src, \
        "üretici artık Search'e daraltmıyor — yardımcıyı da güncelle"
    # Yardımcının fold sınırları üreticininkiyle AYNI türetilmeli
    assert SEARCH_FOLDS == [b for b in FOLDS if b < S_END] + [S_END]
    assert SEARCH_FOLDS[-1] == S_END, "son fold Confirm'e uzanıyor"
    assert all(b <= S_END for b in SEARCH_FOLDS), "fold sınırı Confirm penceresine giriyor"
