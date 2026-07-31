"""test_gaps_batch_v51.py — analytics/counterfactual/shadow_model/selfreview/dataset/backtest/broker
boşlukları (2026-07-21, boşluk kapatma turu 5).

Bu grup "kanıt üreten" katman: kalibrasyonlar, karşı-olgusal defter, gölge model, öz-değerlendirme.
Ortak riskleri aynı: ÜRETMEDEN 'ürettim' görünmek, aynı girdide farklı sayı vermek, ve başkasının
dosyasına yazmak.
"""
from __future__ import annotations

import ast
import pathlib
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _writes(module_file: str) -> set:
    tree = ast.parse(pathlib.Path(module_file).read_text())
    return {n.args[0].value for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in ("write_json", "write_jsonl", "append_jsonl", "merge_dated_jsonl")
            and n.args and isinstance(n.args[0], ast.Constant)}


def _trades(n=40, r=0.4):
    return [{"id": f"T{i}", "strategy_version": 1, "regime": "trend_up", "r_multiple": r,
             "pnl_dollars": r * 1000, "score": 70, "r_multiple_expected": 2.5,
             "ts_open": f"2026-0{1 + (i % 6)}-{(i % 27) + 1:02d}",
             "ts_close": f"2026-0{1 + (i % 6)}-{(i % 27) + 2:02d}",
             "setup": "breakout_vcp", "skill_chain": ["vcp-screener"],
             "mfe_r": 1.8, "mae_r": 0.4, "exit_reason": "target"} for i in range(n)]


# ================= analytics (determinizm, sahiplik) =================
def test_analytics_is_deterministic_for_a_fixed_ledger(seeded):
    from meridian import analytics
    store.write_jsonl("trades.jsonl", _trades())
    a, b = analytics.learning_scorecard(), analytics.learning_scorecard()
    assert a == b
    assert analytics.per_regime_scores() == analytics.per_regime_scores()
    assert analytics.skill_attribution() == analytics.skill_attribution()


def test_analytics_writes_only_calibration_artifacts():
    w = _writes("meridian/analytics.py")
    allowed = {"score_calibration.json", "llm_calibration.json", "exit_efficiency.json",
               "cf_fidelity.json", "near_miss.json", "regime_edge.json",
               # 3b (2026-07-30): MAE karnesi — `exit_efficiency`in ikizi ve onunla AYNI sınıf
               # (ölçüm artefaktı, karar yetkisi YOK). `mae_r` 95 satırın hepsinde vardı ve
               # tüketicisi yoktu; tüketicisi artık /api/diagnostics + evidence_pack.
               "mae_profile.json"}
    assert w <= allowed, f"analytics beyan edilmemiş dosya yazıyor: {w - allowed}"
    called = {n.func.attr for n in ast.walk(ast.parse(pathlib.Path("meridian/analytics.py").read_text()))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "commit" not in called and "dump_yaml" not in called   # ölçer, karar vermez


# ================= counterfactual (determinizm, sahiplik) =================
def test_counterfactual_writes_only_its_own_two_files():
    from meridian import counterfactual as cf
    w = _writes("meridian/counterfactual.py")
    assert w <= {cf.OPEN_FILE, cf.LEDGER}, f"cf fazladan dosya yazıyor: {w}"


def test_counterfactual_has_zero_gate_authority():
    """cf defteri KANIT üretir, KARAR vermez: ne ship, ne sürüm, ne portföy."""
    src = pathlib.Path("meridian/counterfactual.py").read_text()
    called = {n.func.attr for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for forbidden in ("submit", "commit", "dump_yaml", "write_heartbeat"):
        assert forbidden not in called, f"cf '{forbidden}' çağırıyor — sıfır-yetki ihlali"


def test_counterfactual_resolution_is_deterministic(seeded):
    from meridian import counterfactual as cf
    rows = [{"id": "P1", "ticker": "AAA", "date": "2026-01-02", "entry_trigger": 100.0,
             "stop": 95.0, "profit_target": 115.0, "status": "open", "opened": "2026-01-03",
             "entry": 100.5, "r_per_share": 5.5, "bars": 1, "setup": "breakout_vcp"}]
    store.write_json(cf.OPEN_FILE, {"rows": rows})
    a = cf.resolved_rows(entered_only=True)
    b = cf.resolved_rows(entered_only=True)
    assert a == b


# ================= shadow_model (uretkenlik, determinizm) =================
def test_shadow_model_reports_why_it_did_not_train(seeded):
    """Eşiğin altında SESSİZ kalmaz: 'yetersiz örneklem' bir olay olarak kaydedilir ve model
    ağırlıksız kalır — uydurma bir p_win üretmez."""
    from meridian.shadow_model import ShadowTradeOutcomeModel as M
    store.write_jsonl("counterfactuals.jsonl", [])
    store.write_jsonl("trades.jsonl", [])
    m = M().fit()
    assert m.n_fit in (0, None) and getattr(m, "w", None) is None
    assert m.predict_proba({"score": 70, "r_multiple_expected": 2.5, "regime": "trend_up"}) is None
    assert any(e.get("event") == "shadow_model_skip" for e in store.read_jsonl("events.jsonl"))


def test_shadow_model_is_deterministic(seeded):
    """Saf-numpy lojistik: aynı veri → aynı katsayılar (kapıya besleme yapan bir tahmin
    gürültülüyse 'p_win' bir sayı değil, bir zar atışıdır)."""
    from meridian.shadow_model import ShadowTradeOutcomeModel as M
    # cf defterinin GERÇEK şeması: entered=True + rr_expected (shadow_model bu adı okur)
    rows = [{"id": f"P{i}", "plan_id": f"P{i}", "score": 60 + (i % 30),
             "rr_expected": 2.0 + (i % 3) * 0.25, "regime": "trend_up",
             "r_multiple": 1.0 if i % 3 else -1.0, "entered": True, "status": "resolved"}
            for i in range(120)]
    store.write_jsonl("counterfactuals.jsonl", rows)
    store.write_jsonl("trades.jsonl", [])
    a, b = M().fit(), M().fit()
    assert a.n_fit == b.n_fit and a.n_fit >= 40, f"eğitim örneklemi beklenenden küçük: {a.n_fit}"
    import numpy as np
    assert np.allclose(a.w, b.w), "gölge model aynı veriden FARKLI katsayı üretti"
    assert a.brier_train == b.brier_train
    plan = {"score": 72, "r_multiple_expected": 2.5, "regime": "trend_up"}
    assert a.predict_proba(plan) == b.predict_proba(plan)


# ================= selfreview (uretkenlik, determinizm) =================
def test_selfreview_always_produces_a_report(seeded):
    from meridian import selfreview
    rep = selfreview.build()
    assert {"week", "progress", "calibrations", "attention", "contradictions"} <= set(rep)
    assert store.read_json(selfreview.REVIEW_FILE, {}).get("generated"), "rapor diske düşmedi"


def test_selfreview_is_deterministic_for_fixed_state(seeded):
    from meridian import selfreview
    store.write_json("score_calibration.json", {"rank_ic": -0.12, "n": 44})
    a, b = selfreview.build(), selfreview.build()
    a.pop("generated", None); b.pop("generated", None)
    assert a == b


# ================= dataset (uretkenlik, tutarlilik) =================
def test_dataset_windows_are_fixed_and_ordered():
    from meridian import dataset as ds
    assert ds.IS_START < ds.OOS_START < ds.OOS_END <= ds.HOLDOUT_END
    assert ds.FETCH_START < ds.IS_START
    src = pathlib.Path("meridian/dataset.py").read_text()
    for token in ("OOS_START", "OOS_END", "HOLDOUT_END"):
        line = next(l for l in src.splitlines() if l.startswith(f"{token} ="))
        assert "environ" not in line, f"{token} env'den ayarlanabilir → pencere alışverişi"


def test_fetch_end_tracks_today_not_import_time():
    """audit #41: import anında donan FETCH_END, zamanlayıcının portföyü bir daha ilerletmemesine
    yol açmıştı. Her çağrıda BUGÜN olmalı."""
    import datetime as dt
    from meridian import dataset as ds
    assert ds.fetch_end() == dt.date.today().isoformat()
    src = pathlib.Path("meridian/dataset.py").read_text()
    assert "def fetch_end" in src and "FETCH_END = fetch_end()" in src   # sabit yalnız GÖSTERİM için


def test_load_cached_never_touches_the_network():
    src = pathlib.Path("meridian/dataset.py").read_text()
    body = src.split("def load_cached")[1]
    for forbidden in ("load_bars", "fetch(", "httpx"):
        assert forbidden not in body, f"load_cached '{forbidden}' kullanıyor — ağ/tazeleme yolu"


# ================= backtest (uretkenlik, korunum) =================
def test_backtest_produces_the_full_evidence_bundle():
    from meridian import backtest
    from tests.conftest import make_bars
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-06-01", strategy_version=1)
    assert isinstance(res.trades, list) and isinstance(res.plan_log, list)
    assert res.equity and res.equity[0][1] > 0, "öz sermaye eğrisi üretilmedi"
    assert isinstance(res.candidate_log, list)


def test_every_backtest_plan_carries_a_verdict():
    """KORUNUM: değerlendirilen her plan bir karar taşır — sessizce düşen plan yok."""
    from meridian import backtest
    from tests.conftest import make_bars
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-06-01", strategy_version=1)
    for p in res.plan_log:
        assert p.get("gate_verdict") in ("GO", "REVIEW", "NO_GO")
        assert p.get("date") and p.get("ticker")


# ================= broker (uretkenlik, determinizm) =================
def test_broker_produces_a_row_per_closed_position():
    from meridian.broker import PaperBroker
    b = PaperBroker(equity=100_000, slippage_bps=5, commission_per_share=0.005)
    for i, tk in enumerate(("AAA", "BBB")):
        b.fill_entry({"id": f"P{i}", "ticker": tk, "entry_trigger": 100.0, "stop": 95.0,
                      "profit_target": 115.0, "size_r": 1.0}, 100.0, "2026-01-02", 100_000)
        b.close_position(tk, 110.0, "target", "2026-01-09")
    assert len(b.closed) == 2 and all(r["r_multiple"] is not None for r in b.closed)
    assert {r["ticker"] for r in b.closed} == {"AAA", "BBB"}


def test_broker_fills_are_deterministic():
    from meridian.broker import PaperBroker
    def run():
        b = PaperBroker(equity=100_000, slippage_bps=7, commission_per_share=0.005)
        p = b.fill_entry({"id": "P1", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
                          "profit_target": 115.0, "size_r": 1.0}, 100.4, "2026-01-02", 100_000)
        row = b.close_position("AAA", 112.3, "target", "2026-01-09")
        return (p.entry, p.qty, row["pnl_dollars"], row["r_multiple"])
    assert run() == run()
