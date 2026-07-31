"""test_probgate_audit_v35.py — probgate denetimi (2026-07-21, tur 21).

Kapının istatistiksel çekirdeği: her öğrenme kararı bu P değerine dayanıyor. 7. soru:
  PG1 "meta-kalibrasyon YALNIZ SIKILAŞTIRIR" → dosya bozuk/negatif/dev bir değer taşırsa ne olur?
     Kelepçe kodda var, testi yoktu — bir gün gevşeme yönünde bir değer yazılırsa kapı SESSİZCE düşer.
  PG2 "karar tohumdan bağımsızdır"           → SEED_DEFAULT=42 sabit. Verdikt tohuma göre değişiyorsa
     'kanıt' değil ŞANS ölçüyoruz demektir; hiçbir yerde kontrol edilmiyordu.
  PG3 "kötü aday asla geçemez"               → yön testi (tek yönlü kapı)
  PG4 "K-ceza monotondur"                    → daha çok sonda ⇒ daha yüksek çıta, asla tersi
"""
from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

import numpy as np
import pytest

from meridian import config, store
from meridian.probgate import PairedProbabilisticGate, P_BASE, META_FILE


OOS_START, OOS_END = "2024-07-01", "2025-12-31"


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _trades(n=111, seed=7, shift=0.0):
    rng = np.random.default_rng(seed)
    d0 = dt.date.fromisoformat(OOS_START)
    span = (dt.date.fromisoformat(OOS_END) - d0).days
    out = []
    for i in range(n):
        off = int(rng.integers(0, span - 6))
        r = float(rng.normal(0.05, 1.0)) + shift
        out.append({"ts_open": (d0 + dt.timedelta(days=off)).isoformat(),
                    "ts_close": (d0 + dt.timedelta(days=off + int(rng.integers(2, 9)))).isoformat(),
                    "regime": "trend_up", "r_multiple": round(r, 3),
                    "pnl_dollars": round(r * 1000.0, 2), "score": 70,
                    "r_multiple_expected": 2.5})
    return out


# ---------- PG1: meta yalnız sıkıştırır ----------
def test_pg1_meta_calibration_can_only_tighten(seeded):
    for bad in (-0.5, -0.01, 0.0):
        store.write_json(META_FILE, {"extra_p": bad})
        assert PairedProbabilisticGate.p_required_for(1) >= P_BASE, "meta eşiği GEVŞETTİ"


def test_pg1b_meta_offset_is_capped(seeded):
    store.write_json(META_FILE, {"extra_p": 99.0})
    assert PairedProbabilisticGate.p_required_for(1) <= 0.95


def test_pg1c_corrupt_meta_file_falls_back_to_base(seeded):
    store.write_json(META_FILE, {"extra_p": "bozuk"})
    assert PairedProbabilisticGate.p_required_for(1) == pytest.approx(P_BASE)
    store.write_json(META_FILE, {})
    assert PairedProbabilisticGate.p_required_for(1) == pytest.approx(P_BASE)


# ---------- PG2: tohumdan bağımsız verdikt ----------
def test_pg2_verdict_is_seed_stable_for_clear_cases(seeded):
    goal = config.goal()
    inc = _trades(111, seed=7)
    lift = [{**t, "r_multiple": t["r_multiple"] + 0.5, "pnl_dollars": t["pnl_dollars"] + 500} for t in inc]
    worse = [{**t, "r_multiple": t["r_multiple"] - 0.5, "pnl_dollars": t["pnl_dollars"] - 500} for t in inc]
    for seed in (1, 42, 99, 1234):
        g = PairedProbabilisticGate(goal, n_boot=300, seed=seed)
        assert g.evaluate(inc, lift, OOS_START, OOS_END, k_probes=1).passes is True, seed
        assert g.evaluate(inc, worse, OOS_START, OOS_END, k_probes=1).passes is False, seed


def test_pg2b_same_seed_is_reproducible(seeded):
    goal = config.goal()
    inc = _trades(111, seed=7)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.2} for t in inc]
    a = PairedProbabilisticGate(goal, n_boot=300, seed=42).evaluate(inc, cand, OOS_START, OOS_END)
    b = PairedProbabilisticGate(goal, n_boot=300, seed=42).evaluate(inc, cand, OOS_START, OOS_END)
    assert (a.p, a.mean_delta, a.n_valid) == (b.p, b.mean_delta, b.n_valid)


# ---------- PG3: yön ----------
def test_pg3_identical_candidate_never_passes(seeded):
    goal = config.goal()
    inc = _trades(111, seed=7)
    g = PairedProbabilisticGate(goal, n_boot=400, seed=42)
    res = g.evaluate(inc, [dict(t) for t in inc], OOS_START, OOS_END, k_probes=1)
    assert res.passes is False and (res.p or 0) < 0.5


@pytest.mark.parametrize("delta", [-1.0, -0.5, -0.2])
def test_pg3b_worse_is_always_rejected(seeded, delta):
    goal = config.goal()
    inc = _trades(111, seed=7)
    cand = [{**t, "r_multiple": t["r_multiple"] + delta,
             "pnl_dollars": t["pnl_dollars"] + delta * 1000} for t in inc]
    assert PairedProbabilisticGate(goal, n_boot=400, seed=42).evaluate(
        inc, cand, OOS_START, OOS_END, k_probes=1).passes is False


# ---------- PG4: K-ceza monoton ----------
def test_pg4_k_penalty_is_monotone(seeded):
    store.write_json(META_FILE, {})
    reqs = [PairedProbabilisticGate.p_required_for(k) for k in (1, 2, 5, 10, 30, 100)]
    assert reqs == sorted(reqs), "daha çok sonda daha DÜŞÜK çıta istiyor — kazananın laneti açık"
    from meridian.probgate import P_CEIL
    assert reqs[-1] <= P_CEIL
    # CEZA DONMAMALI (2026-07-22): eski doğrusal formül K=16'da 0.95'e çarpıp orada kalıyordu, yani
    # 100 sondalık bir arama 16 sondalıkla AYNI çıtayı ödüyordu. Monotonluk yetmez, ARTMAYA devam
    # etmeli — yoksa geniş arama neredeyse kesin olarak şansa dayalı bir kazanan üretir.
    assert reqs[-1] > reqs[-2] > reqs[-3], "ceza bir yerde DONUYOR"


def test_pg4b_block_size_is_bounded_and_data_driven():
    from meridian.probgate import BLOCK_MIN_D, BLOCK_MAX_D
    assert PairedProbabilisticGate.block_days_for([]) == BLOCK_MIN_D
    long_holds = [{"ts_open": "2025-01-01", "ts_close": "2025-06-01"}] * 5
    assert PairedProbabilisticGate.block_days_for(long_holds) == BLOCK_MAX_D
    mid = [{"ts_open": "2025-01-01", "ts_close": "2025-01-11"}] * 5
    assert BLOCK_MIN_D <= PairedProbabilisticGate.block_days_for(mid) <= BLOCK_MAX_D


def test_empty_input_is_legacy_and_fails(seeded):
    g = PairedProbabilisticGate(config.goal(), n_boot=100).evaluate([], [], OOS_START, OOS_END)
    assert g.law == "legacy" and not g.passes
