"""API/serialization contract — the boundary where the numeric layer meets JSON.

Regression origin: the OOS gate computes `cand_oos > inc_oos + GATE_MARGIN` on values that come from the
numpy/pandas layer, so that comparison is a **numpy.bool_**. Python's `and` returns the FIRST FALSY operand,
so every probe that FAILED the magnitude gate made `passes` a numpy.bool_ — not JSON-serializable. The
moment it was exposed through /api/hermes the endpoint returned **HTTP 500** and the whole Hermes page died.
A passing probe yielded a real bool, which is exactly why it hid.

These tests pin the contract: nothing derived from numpy may escape into a serialized payload.
"""
import json
import pathlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from meridian import reflect, analytics, hermes, hermes_runtime
from meridian.api import app

from tests import wf_fixtures as wf


def _wf(oos, folds):
    """Thin bridge to the ONE walk_forward fixture factory (tests/wf_fixtures.py). Keeps the
    caller-supplied oos scalar — numpy types included, which is the whole point of this file — and
    the per-fold (n, avg_r) shape, but lays REAL Search/Confirm slices underneath so `has_slices` is
    True and `_gate_eval` runs the PROBABILISTIC path production actually ships. The old slice-less
    mimic silently fell into the unreachable legacy point-margin branch, so these tests were pinning
    a dead code path. holdout mirrors oos as before; note that under the factory the fold `n` now
    also sets the synthetic trade count, so callers pass floor-clearing sizes (>=21 trades/side)."""
    return wf.wf_from_scores(oos, folds=folds, holdout=oos)


def test_gate_eval_returns_plain_bool_on_the_failing_path_with_numpy_inputs():
    """The failing branch is the one that leaked. Assert BOTH branches return a real bool — now over
    the PROBABILISTIC law the fixture carries slices for, not the legacy fallback the slice-less
    mimic used to hit."""
    # İncumbent'ta İKİ fold (2026-07-22): `_gate_eval` cand/inc fold'larını zip'ler, yani eşleşme
    # sayısını iki taraf birden belirler. Fold-sağlamlığı artık TEK pencerelik kanıtla iddia
    # edilemez; bu test TİPİ ölçüyor (bool vs numpy.bool_), kapı yasasını değil. Fold n'leri
    # olasılıksal tabanı (>=21 işlem/taraf) aşacak boyda: büyüklük kararı artık nokta-marjdan değil,
    # Search dilimindeki blok-bootstrap P(ΔS>0)'dan geliyor — üretimin GERÇEKTE koştuğu yol.
    inc = _wf(np.float64(0.20), [(30, np.float64(0.5)), (30, np.float64(0.4))])

    # aday fold R'leri incumbent'ın belirgin ALTINDA → P(ΔS>0) ~ 0 → büyüklük kapısı reddeder
    failing = _wf(np.float64(0.21), [(30, np.float64(0.1)), (30, np.float64(0.1))])
    passes, _gate, _why = reflect._gate_eval(inc, failing)
    assert _gate["gate_law"] == "probabilistic"                   # legacy'ye kaçmadı: gerçek yol koştu
    assert passes is False                                        # identity: a real bool, not numpy.bool_
    assert type(passes) is bool
    json.dumps({"passes": passes})                                # would raise TypeError before the fix

    # aday fold R'leri incumbent'ın belirgin ÜSTÜNDE → P(ΔS>0) ~ 1 → geçer
    winning = _wf(np.float64(0.40), [(30, np.float64(0.9)), (30, np.float64(0.8))])
    p2, _g, _w = reflect._gate_eval(inc, winning)
    assert _g["gate_law"] == "probabilistic"
    assert p2 is True and type(p2) is bool


def test_hermes_status_payload_is_json_serializable_mid_search():
    """The exact shape that 500'd: a FAILING probe recorded in SEARCH_PROGRESS, then /api/hermes
    serializes. Fold sizes clear the probabilistic floor so the FAILING verdict is the real
    bootstrap law's, and the `passes` it records must still be a plain bool."""
    inc = _wf(np.float64(0.20), [(30, np.float64(0.5))])
    failing = _wf(np.float64(0.21), [(30, np.float64(0.1))])
    passes, _g, _w = reflect._gate_eval(inc, failing)
    assert _g["gate_law"] == "probabilistic"
    hermes.SEARCH_PROGRESS.update(running=True, phase="probing", i=1, total=2,
                                  variable="entry.min_score", new=61, candidate_oos=0.21,
                                  incumbent_oos=0.20, passes=passes, best=None)
    try:
        json.dumps(hermes_runtime.status())        # TypeError before the fix → HTTP 500 in production
    finally:
        hermes.SEARCH_PROGRESS.clear()


# ---- LIVE LEDGER COPY (2026-07-30, ghost-session gate round) ----------------------------------
# FINDING (full suite): this test ran WITHOUT `sandbox_state`, so it read the operator's LIVE state —
# `trades.jsonl` and `state/bars/spy.csv`. The read was silent until the bar chain gained a trading
# calendar gate; the live SPY cache holds two non-session rows (2018-11-22, 2025-05-26), the gate
# dropped them and emitted an event straight into the LIVE `events.jsonl`, and the conftest leak
# guard failed at teardown.
# THE TEST IS THE BUG, NOT THE GATE: an integrity repair on the read path SHOULD be audible; a test
# touching production ledgers is both a leak and a determinism defect (its verdict would depend on
# whatever the operator's data happened to look like).
# WHY A BARE SANDBOX IS NOT ENOUGH: with an empty state `benchmark_relative()` returns None and the
# assertion below never runs — a test that always no-ops proves nothing. So the ledgers are COPIED
# into the sandbox: same measurement, writes land in the copy. `events.jsonl` is skipped on purpose
# (nothing here reads it, it is 8.8 MB, and it is the write target being protected).
_LIVE_STATE = pathlib.Path(__file__).resolve().parent.parent / "state"


@pytest.fixture
def live_ledger_copy(sandbox_state):
    import shutil
    for p in sorted(_LIVE_STATE.glob("*.json*")) + sorted(_LIVE_STATE.glob("*.yaml")):
        if p.name == "events.jsonl" or not p.is_file():
            continue
        try:
            shutil.copy2(p, sandbox_state / p.name)
        except OSError:  # sessiz-yutma: tek dosya okunamadı — kopya eksik kalır, testin kendi ön koşulu ayrıca sorulur
            pass
    spy = _LIVE_STATE / "bars" / "spy.csv"
    if spy.exists():
        shutil.copy2(spy, sandbox_state / "bars" / "spy.csv")
    return sandbox_state


def test_benchmark_relative_beat_flag_is_a_plain_bool(live_ledger_copy):
    b = analytics.benchmark_relative()
    if b is not None:                              # None when there is not enough history
        assert type(b["beat_benchmark"]) is bool
        json.dumps(b)


# ---------------- systemic guard: no GET endpoint may 500 ----------------
GET_ENDPOINTS = [
    "/healthz", "/metrics", "/api/summary", "/api/today", "/api/signals", "/api/agent",
    "/api/memory", "/api/skills", "/api/performance", "/api/events", "/api/spend",
    "/api/hermes", "/api/scheduler", "/api/sprint", "/api/secrets",
    "/api/diagnostics", "/api/debug_export",
]


@pytest.mark.parametrize("path", GET_ENDPOINTS)
def test_get_endpoint_does_not_500(path, sandbox_state):
    # sandbox_state ZORUNLU (2026-07-22): /api/diagnostics bütünlük dedektörlerini çalıştırır ve
    # onlar KENDİ referans dosyalarını yazar (bars_fingerprint / monotonic_state / ownership_state).
    # Fikstürsüz koşunca bu test operatörün CANLI dedektör tabanını eziyordu — sonraki turda
    # "gerileme yok" diyen bir monotonluk raporu, aslında tabanı bu testin yazdığı rapordu.
    """A 500 on any read endpoint means an unserializable value escaped the engine into the API — the class
    of bug that killed /api/hermes. Auth is open when MERIDIAN_DASH_TOKEN is unset (the test default)."""
    with TestClient(app) as client:
        r = client.get(path)
    assert r.status_code != 500, f"{path} returned 500: {r.text[:300]}"
