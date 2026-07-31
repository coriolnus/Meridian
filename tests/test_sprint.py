"""Learning-sprint machinery — the shared gate law, windows threading (+ cache key), the coordinate-descent
search, the honest verdict states, and sandbox isolation. walk_forward/Popen are stubbed — no heavy real
backtests, no real subprocess. Guards the invariants the adversarial judges flagged."""
from pathlib import Path
import shutil

import pytest

from meridian import reflect, analytics, config, store, sprint
from tests import wf_fixtures as wf


@pytest.fixture
def seeded_sandbox(sandbox_state):
    """sandbox_state + the immutable goal.yaml/bounds.yaml so config.goal()/bounds() resolve."""
    repo_state = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo_state / f, sandbox_state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    return sandbox_state


def _wf(oos, folds, tail=None, holdout=None):
    """Bridge to the central walk_forward factory (tests.wf_fixtures). `folds` arrives here as
    [{"n","avg_r"}] (from _folds); wf_from_scores wants [(n, avg_r)]. The given oos/folds/tail/holdout
    scalars are PRESERVED (as before), but the factory lays REAL Search/Confirm slices underneath so
    _gate_eval runs the PRODUCTION probabilistic + confirm path — not the unreachable legacy point-margin
    branch the old slice-less dict fell into (fixture-trap fix, 2026-07-23)."""
    pairs = [(f["n"], f["avg_r"]) for f in folds]
    return wf.wf_from_scores(oos, folds=pairs, tail=tail,
                             holdout=(oos if holdout is None else holdout))


def _folds(*pairs):
    return [{"n": n, "avg_r": r} for (n, r) in pairs]


# ---------------- the one shared gate law ----------------
def test_gate_eval_ships_a_clear_winner_and_rejects_a_marginal():
    # n bumped past the Search-slice floor (max(10, 0.7·min_sample)=21) so the PROBABILISTIC law runs,
    # not the thin/legacy fallback. Magnitude is now decided by P(ΔS>0) over the real slices.
    inc = _wf(0.10, _folds((30, 0.2), (30, 0.2), (30, 0.2)))
    winner = _wf(0.20, _folds((30, 0.5), (30, 0.5), (30, 0.1)))  # clear Search-slice edge, folds 2/3
    passes, gate, why = reflect._gate_eval(inc, winner)
    assert passes and why == "" and gate["candidate_oos"] == 0.20
    assert gate["gate_law"] == "probabilistic" and gate["search_p"] >= gate["search_p_required"]
    # a MARGINAL candidate = no genuine Search-slice edge (same R as incumbent) → P(ΔS>0) below the
    # required bar. Under the live law "marginal" means unproven probabilistically, not "<+0.02 oos".
    marginal = _wf(0.11, _folds((30, 0.2), (30, 0.2), (30, 0.2)))
    p2, g2, why2 = reflect._gate_eval(inc, marginal)
    assert not p2 and g2["gate_law"] == "probabilistic"
    assert g2["search_p"] < g2["search_p_required"] and "P(ΔS>0)" in why2


def test_gate_eval_tail_veto_blocks_a_riskier_winner():
    # candidate WINS magnitude probabilistically (higher Search-slice R) but its OOS tail risk is worse —
    # the tail veto (law-independent) still blocks it. n past the slice floor so the veto is the blocker,
    # not a thin-slice magnitude failure.
    inc = _wf(0.10, _folds((30, 0.2), (30, 0.2)), tail={"var_r": 1.0, "cvar_r": 1.5})
    cand = _wf(0.30, _folds((30, 0.5), (30, 0.5)), tail={"var_r": 3.0, "cvar_r": 4.0})  # tail metrics worse
    passes, gate, why = reflect._gate_eval(inc, cand)
    assert gate["search_p"] >= gate["search_p_required"]   # magnitude cleared; only the tail vetoes
    assert not passes and "tail risk" in why


def test_gate_eval_loses_fold_majority():
    """Aday havuzlanmış Search edge'ini KAZANIR ama fold çoğunluğunu KAYBEDER → veto.

    KURGU DEĞİŞTİ (2026-07-28, Aşama 2.1 n-dengeli fold kesimi). Eski kurgu (40, 6, 6) idi ve tam
    olarak reformun ORTADAN KALDIRMAK için var olduğu patolojiye dayanıyordu: 6 işlemlik bir pencere,
    40 işlemlik bir pencereyle EŞİT oy kullanıyordu (canlı karşılığı: fold dağılımı [45, 46, 7]).
    Kesim artık işlem sayısına göre yapıldığı ve `backtest.FOLD_MIN_N = 15` tabanı bulunduğu için 6
    işlemlik bir fold ARTIK ÜRETİLEMEZ — eski kurgu, var olamayacak bir duruma dayanıyordu.
    Yasa aynen yürürlükte; sınanan kurgu onun HÂLÂ mümkün olan hâline taşındı: eşit ağırlıklı üç
    pencere, adayın yalnız birinde kazandığı."""
    inc = _wf(0.10, _folds((30, 0.4), (30, 0.4), (30, 0.4)))
    cand = _wf(0.30, _folds((30, 3.0), (30, 0.2), (30, 0.2)))     # havuzda kazanır, 2 fold'u düşürür
    passes, gate, why = reflect._gate_eval(inc, cand)
    assert gate["search_p"] >= gate["search_p_required"]   # magnitude cleared; the fold majority vetoes
    assert not passes and "fold-robustness" in why
    assert gate["fold_law"] == "n_dengeli", f"n-dengeli kesim koşmadı: {gate['fold_law']}"


# ---------------- windows threading + cache key ----------------
def test_submit_default_windows_match_production(seeded_sandbox, monkeypatch):
    from meridian import dataset
    seen = []

    def fake_wf(params, bars, index, goal, is_s, oos_s, oos_e, hold_e, **kw):
        seen.append((is_s, oos_s, oos_e, hold_e))
        return _wf(0.10, _folds((5, 0.2), (5, 0.2)))
    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear()
    reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t"})
    assert seen and all(s == (dataset.IS_START, dataset.OOS_START, dataset.OOS_END, dataset.HOLDOUT_END)
                        for s in seen)


def test_submit_threads_identical_windows_to_incumbent_and_candidate(seeded_sandbox, monkeypatch):
    W = ("2020-01-01", "2021-01-01", "2021-12-31", "2021-12-31", ["2021-01-01", "2021-07-01", "2021-12-31"], 7)
    seen = []

    def fake_wf(params, bars, index, goal, is_s, oos_s, oos_e, hold_e, **kw):
        seen.append((is_s, oos_s, oos_e, hold_e, tuple(kw.get("oos_folds")), kw.get("embargo_days")))
        return _wf(0.10, _folds((5, 0.2), (5, 0.2)))
    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear()
    reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t"}, windows=W)
    exp = (W[0], W[1], W[2], W[3], tuple(W[4]), W[5])
    assert len(seen) >= 2 and all(s == exp for s in seen)   # apples-to-apples: same window both sides


def test_inc_cache_keys_on_window(monkeypatch, sandbox_state):
    calls = [0]

    def fake_wf(*a, **k):
        calls[0] += 1
        return _wf(0.10, _folds((5, 0.2),))
    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    reflect._INC_CACHE.clear()
    g = {"min_sample": 30}
    W1 = ("2020-01-01", "2021-01-01", "2021-12-31", "2021-12-31", ["a"], 7)
    W2 = ("2019-01-01", "2020-01-01", "2020-12-31", "2020-12-31", ["a"], 7)
    reflect._wf_cached({"x": 1.0}, 1, None, None, g, windows=W1)
    reflect._wf_cached({"x": 1.0}, 1, None, None, g, windows=W1)   # cache hit
    reflect._wf_cached({"x": 1.0}, 1, None, None, g, windows=W2)   # different window → recompute
    assert calls[0] == 2


# ---------------- coordinate-descent search + submit ----------------
def _search_stub(monkeypatch, cand_oos):
    """incumbent(v1)→oos 0.10 with Search-slice R≈0.2. Every candidate(v>=2)→oos cand_oos, and its
    Search-slice EDGE is tied to whether cand_oos is a genuine lift: a real improver (cand_oos beyond the
    margin) gets R=0.5 → strong P(ΔS>0) → the probabilistic magnitude law ships it; a marginal one gets
    R=0.2 (no edge) → P(ΔS>0) stays below the required bar → nothing clears. Same production law decides,
    now over REAL slices instead of the legacy point-margin on the oos scalar."""
    genuine_lift = cand_oos > 0.10 + reflect.GATE_MARGIN
    cand_folds = (_folds((30, 0.5), (30, 0.5), (30, 0.5)) if genuine_lift
                  else _folds((30, 0.2), (30, 0.2), (30, 0.2)))   # no edge → never clears

    def fake_wf(params, bars, index, goal, *a, **kw):
        v = kw.get("strategy_version", 1)
        if v == 1:
            return _wf(0.10, _folds((30, 0.2), (30, 0.2), (30, 0.2)))
        return _wf(cand_oos, cand_folds)
    monkeypatch.setattr(reflect.backtest, "walk_forward", fake_wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear()
    reflect._PROBE_CACHE.clear()


def test_search_ships_when_a_candidate_clears(seeded_sandbox, monkeypatch):
    _search_stub(monkeypatch, cand_oos=0.30)                       # genuine Search edge, 3/3 folds
    bars, index = (None, None)
    res = reflect.search_and_submit(bars, index, config.goal(), windows=None, k_max=2, budget=4)
    assert res["status"] == "shipped" and res["version"] == 2
    hyp = res["hypothesis"]
    # the SEARCH-slice estimate is the MEASURED OOS lift (0.30−0.10), not a hardcoded ±step guess
    assert hyp["predicted_delta_search"] == pytest.approx(0.20, abs=1e-6)
    # what actually gets calibrated is the UNBIASED confirm-slice delta — measured & positive, and
    # (honestly) no larger than the inflated search estimate (winner's-curse deflation)
    assert hyp["predicted_delta"] is not None and 0.0 < hyp["predicted_delta"] <= 0.20 + 1e-6


def test_search_ships_nothing_when_none_clear(seeded_sandbox, monkeypatch):
    _search_stub(monkeypatch, cand_oos=0.11)                       # +0.01 < GATE_MARGIN → never clears
    commits = []
    monkeypatch.setattr(reflect.versioning, "commit", lambda c: commits.append(c))
    res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=2, budget=4)
    assert res["status"] == "no_clearing_candidate" and not commits   # nothing shipped
    assert res["search"]["cleared"] == 0


# ---------------- honest verdict states ----------------
def test_verdict_names_the_real_blocker_no_ship(monkeypatch):
    hyps = [{"status": "rejected_by_backtest"}, {"status": "rejected_by_guard"}]
    monkeypatch.setattr(analytics.memory, "all_hypotheses", lambda: hyps)
    monkeypatch.setattr(analytics.store, "read_jsonl", lambda *a, **k: [{"strategy_version": 1}] * 40)
    monkeypatch.setattr(analytics.store, "read_json", lambda *a, **k: {"versions": {}, "current_version": 1})
    monkeypatch.setattr(analytics, "calibration", lambda *a, **k: {"n": 0, "hit_rate": None, "brier": None})
    sc = analytics.learning_scorecard(goal={"min_sample": 30})
    assert sc["loop_state"] == "no_ship_v1_stands"
    assert "geçemedi" in sc["verdict"] and "yeterli işlem yok" not in sc["verdict"]   # truth, not the old lie
    assert sc["trades_total"] == 40


def test_verdict_awaiting_min_sample_after_a_ship(monkeypatch):
    hyps = [{"status": "live", "version_to": 2}]                   # shipped, no realized_delta yet
    monkeypatch.setattr(analytics.memory, "all_hypotheses", lambda: hyps)
    monkeypatch.setattr(analytics.store, "read_jsonl", lambda *a, **k: [{"strategy_version": 2}] * 5)
    monkeypatch.setattr(analytics.store, "read_json", lambda *a, **k: {"versions": {"2": {}}, "current_version": 2})
    monkeypatch.setattr(analytics, "calibration", lambda *a, **k: {"n": 0, "hit_rate": None, "brier": None})
    sc = analytics.learning_scorecard(goal={"min_sample": 30})
    assert sc["loop_state"] == "shipped_awaiting_min_sample" and "5/30" in sc["verdict"]


# ---------------- observability of the long-running search ----------------
def test_search_reports_probe_progress(seeded_sandbox, monkeypatch):
    """Regression: the search runs ~a dozen walk-forwards (MINUTES) and emitted NOTHING — the operator (and
    I, debugging it) could not tell progress from a hang. Every probe must report i/total."""
    _search_stub(monkeypatch, cand_oos=0.11)          # nothing clears; we only assert progress emission
    seen = []
    reflect.coordinate_descent_search(
        None, None, config.goal(), windows=None, k_max=1, budget=3,
        on_probe=lambda i, total, var, new, c_oos, i_oos, passes, best: seen.append((i, total, var)))
    # i=0 is the PLAN event, published as soon as the (slow) incumbent walk is done so the UI immediately
    # knows the scale; then one event per completed probe.
    assert [s[0] for s in seen] == [0, 1, 2, 3]        # plan, then monotonic probe index
    assert all(s[1] == 3 for s in seen)                # total is reported so a UI can draw a bar
    assert seen[0][2] is None                          # the plan event names no knob yet
    assert all(isinstance(s[2], str) for s in seen[1:])   # each probe names the knob under test


def test_progress_callback_failure_never_breaks_the_search(seeded_sandbox, monkeypatch):
    """Progress reporting is best-effort: a broken UI callback must not take down a 13-minute search."""
    _search_stub(monkeypatch, cand_oos=0.30)

    def boom(*a):
        raise RuntimeError("ui exploded")
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=2, on_probe=boom)
    assert res["evaluated"] == 2 and res["best"] is not None   # search completed anyway


def test_next_reflection_countdown_uses_last_reflection_baseline(seeded_sandbox):
    """Regression: the UI computed `reflection_every - closed_trades`, which is 0 for ANY book with more
    trades than `every` — so "Sonraki otomatik düşünme" permanently (and falsely) read 'hazır'. The
    countdown must be measured from the trade count AT THE LAST REFLECTION, server-side."""
    from meridian import hermes_runtime
    hermes_runtime._state["last_reflect_at"] = None
    for i in range(40):                                # a book far larger than reflection_every (5)
        store.append_jsonl("trades.jsonl", {"id": i})
    hermes_runtime._record({"status": "rejected_by_backtest", "hypothesis": {"variable": "x"}})
    st = hermes_runtime.status()
    assert st["closed_trades"] == 40 and st["last_reflect_at"] == 40
    assert st["trades_since_last_reflection"] == 0
    assert st["trades_until_next"] == st["reflection_every"]   # a FULL wait — the old code said 0 ("hazır")
    for i in range(3):                                 # three more close
        store.append_jsonl("trades.jsonl", {"id": 100 + i})
    st2 = hermes_runtime.status()
    assert st2["trades_since_last_reflection"] == 3
    assert st2["trades_until_next"] == st2["reflection_every"] - 3


# ---------------- live reflect_once wiring (search is the workhorse) ----------------
def test_reflect_once_searches_when_no_claude(seeded_sandbox, monkeypatch):
    """Beyin yokken ARAMA hâlâ iş atıdır — ama artık ondan ÖNCE meşru bir basamak var.

    2026-07-30 (üreteç keşif dengesi turu, Nous N00002): beyin zinciri boş dönünce `reflect_once`
    eskiden DOĞRUDAN koordinat-inişi aramasına düşüyordu — tek akıllı hamle yuvası BOŞTU. Artık o
    yuva bakir bir düğmeden (`hermes.propose_virgin_knob`) deterministik bir hamleyle doluyor ve
    hamle AYNI boru hattından, `reflect.submit`ten geçiyor; ship etmezse arama devralır. Bu fikstür
    `submit`i mock'lamadığı için o hamle GERÇEK backtest'e giriyor ve stub bar'larda patlıyordu:
    üretim hatası değil, fikstürde EKSİK BİR BASAMAK.

    İKİ ONARIM VARDI, BU SEÇİLDİ. `HERMES_VIRGIN_FALLBACK=0` yamalamak testi VARSAYILAN OLMAYAN bir
    yapılandırmada koştururdu: bakir yol bir gün yansımayı yutsa test yine yeşil kalır, üretim ise
    aramaya HİÇ ulaşmazdı — tam olarak bu deponun kovaladığı sessiz ayrışma deseni. Onun yerine eksik
    basamak fikstüre eklendi ve İDDİAYA dahil edildi; hemen alttaki komşu test
    (`..._falls_through_to_search_when_claude_rejected`) zaten aynı deseni kullanıyor: tek hamle
    denenir, ship etmez, arama devralır. Testin dar iddiası (arama PRODUCTION pencereleriyle çağrılır)
    aynen korundu. Bakir yolun KENDİ davranış testleri (değer seçimi, guard ön-denetimi, bakir
    kalmayınca zarif düşüş, anahtarla kapatma) `test_uretec_kesif_dengesi_v135.py`dedir."""
    from meridian import hermes, reflect, dataset
    monkeypatch.setattr(hermes, "propose_with_claude", lambda: None)
    monkeypatch.setattr(dataset, "load", lambda **k: ("BARS", "IDX"))
    onerilen = []

    def fake_submit(prop, *a, **k):
        onerilen.append(prop)
        return {"status": "rejected_by_backtest"}      # ship etmez → arama devralır
    monkeypatch.setattr(reflect, "submit", fake_submit)
    seen = {}

    def fake_search(bars, index, goal=None, *, windows, budget, k_max, on_probe=None, regime=None):
        seen.update(bars=bars, windows=windows, budget=budget, k_max=k_max, on_probe=on_probe, regime=regime)
        return {"status": "no_clearing_candidate", "search": {"evaluated": 5, "cleared": 0}}
    monkeypatch.setattr(reflect, "search_and_submit", fake_search)
    res = hermes.reflect_once()
    assert res["status"] == "no_clearing_candidate"
    # (1) tek hamle yuvası artık BOŞ DEĞİL: bakir düğme yolu kapıya TEK bir öneri verdi
    assert len(onerilen) == 1 and onerilen[0]["source"] == "deterministic:virgin"
    assert onerilen[0]["variable"] in config.bounds(), "bakir öneri bounds evreninin dışından geldi"
    # (2) ve arama HÂLÂ iş atı — üretim pencereleri, üretim bütçesiyle
    assert seen["bars"] == "BARS" and seen["windows"] is None            # PRODUCTION windows
    assert seen["budget"] == hermes.SEARCH_BUDGET and seen["k_max"] == hermes.SEARCH_KMAX


def test_reflect_once_takes_claude_ship_without_searching(seeded_sandbox, monkeypatch):
    from meridian import hermes, reflect
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: {"variable": "x", "new": 1, "source": "hermes:claude"})
    monkeypatch.setattr(reflect, "submit", lambda p, *a, **k: {"status": "shipped", "version": 2})
    searched = {"n": 0}
    monkeypatch.setattr(reflect, "search_and_submit", lambda *a, **k: searched.__setitem__("n", 1))
    res = hermes.reflect_once()
    assert res["status"] == "shipped" and searched["n"] == 0             # claude shipped → search never runs


def test_reflect_once_falls_through_to_search_when_claude_rejected(seeded_sandbox, monkeypatch):
    from meridian import hermes, reflect, dataset
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: {"variable": "x", "new": 1, "source": "hermes:claude"})
    monkeypatch.setattr(reflect, "submit", lambda p, *a, **k: {"status": "rejected_by_backtest"})
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    monkeypatch.setattr(reflect, "search_and_submit", lambda *a, **k: {"status": "shipped", "version": 2, "search": {}})
    assert hermes.reflect_once()["status"] == "shipped"                  # claude rejected → search took over


# ---------------- sandbox isolation ----------------
def test_sprint_start_isolates_the_live_book(seeded_sandbox, monkeypatch):
    store.append_jsonl("trades.jsonl", {"id": 1, "strategy_version": 1})
    store.write_json("strategy.yaml_marker", {"live": True})       # a plain live file to prove non-mutation
    live_trades_before = (config.STATE / "trades.jsonl").read_text()

    class FakePopen:
        def __init__(self, *a, **k):
            self.pid = 424242
    monkeypatch.setattr(sprint.subprocess, "Popen", FakePopen)
    res = sprint.start({"budget": 4})
    assert res["started"]
    sb = config.STATE / "sprint" / res["sid"] / "state"
    assert sb.exists() and (sb / "bars").exists()                  # sandbox built, bars linked
    assert (sb / "trades.jsonl").read_text() == ""                 # sandbox ledgers reset to empty
    assert (config.STATE / "trades.jsonl").read_text() == live_trades_before   # LIVE untouched
