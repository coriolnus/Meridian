"""Dynamic Regime patch — P1.a durable failed_broker_rejection, P1.b positions reconciliation,
P3.a regime-nested schema, P3.b regime-isolated walk-forward gate, P3.c regime-scoped strict-AND
horizon, P3.d market_regime telemetry + parent-score reachability. Alpaca mocked; no heavy replays
(walk_forward's replay is monkeypatched with synthetic regime-tagged trades)."""
from pathlib import Path
import shutil

import pytest

from meridian import config, store


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ============ P1.b — position reconciliation (orders AND positions fetched) ============
def test_reconcile_positions_missing_drift_and_external(seeded_sandbox, monkeypatch):
    from meridian import loop, obs
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    # BBB has a LIVE entry order (stop not yet triggered) → its absence from positions is NOT split-brain
    orders = [{"client_order_id": "P-BBB", "symbol": "BBB", "status": "new", "legs": []}]
    apos = [{"symbol": "CCC", "qty": "20"},      # internal says 10 → >25% drift
            {"symbol": "DDD", "qty": "10.4"},    # internal says 10 → 4% gap, fine
            {"symbol": "NVDA", "qty": "1"}]      # operator's own — external, info only
    monkeypatch.setattr(alpaca, "orders", lambda status="open", limit=50, nested=False: orders)
    monkeypatch.setattr(alpaca, "positions", lambda: apos)
    alarms = []
    monkeypatch.setattr(obs, "alarm", lambda token, msg, **k: alarms.append((token, k.get("ticker"))))
    out = loop.reconcile_broker_state({"armed": []}, "2026-07-15", [],
                                      open_positions={"AAA": 10, "BBB": 10, "CCC": 10, "DDD": 10})
    p = out["positions"]
    assert p["missing_on_alpaca"] == ["AAA"]                        # no position AND no live order
    assert "BBB" not in p["missing_on_alpaca"]                      # resting entry order → not split-brain
    assert [d["ticker"] for d in p["qty_drift"]] == ["CCC"]         # 2x qty → drift; 4% → not
    assert p["external"] == ["NVDA"]                                # operator's holding: listed, NO alarm
    alarm_syms = {t for _, t in alarms}
    assert alarm_syms == {"AAA", "CCC"}                             # exactly the split-brain cases alarm
    bj = store.read_json("broker_reconcile.json", {})
    assert bj["position_drift"] is True and bj["positions"]["external"] == ["NVDA"]


# ============ P3.a — regime-nested schema + dynamic resolution ============
def test_default_strategy_carries_regime_keys_and_resolve_overlays():
    ds = config.default_strategy()
    assert set(ds["params_by_regime"].keys()) == set(config.VALID_REGIMES)
    assert all(v == {} for v in ds["params_by_regime"].values())    # empty on purpose: no global shadowing
    params = {"stop_loss_atr_mult": 2.0, "entry.min_score": 60}
    by = {"chop": {"stop_loss_atr_mult": 1.5}}
    assert config.resolve_params(params, by, "chop")["stop_loss_atr_mult"] == 1.5
    assert config.resolve_params(params, by, "trend_up")["stop_loss_atr_mult"] == 2.0
    assert config.resolve_params(params, by, "chop")["entry.min_score"] == 60


def test_bump_routes_regime_knob_into_params_by_regime():
    from meridian import versioning
    child = versioning.bump({"version": 1, "params": {"stop_loss_atr_mult": 2.0}},
                            "stop_loss_atr_mult@chop", 1.5)
    assert child["params"]["stop_loss_atr_mult"] == 2.0             # global untouched
    assert child["params_by_regime"]["chop"]["stop_loss_atr_mult"] == 1.5


# ============ P3.b — regime-isolated walk-forward grading ============
def _fake_trades():
    mk = lambda i, reg, r: {"ts_open": f"2024-0{1 + i % 6}-10", "ts_close": f"2024-0{1 + i % 6}-20",
                            "regime": reg, "r_multiple": r, "pnl_dollars": r * 100.0}
    return ([mk(i, "chop", 1.0) for i in range(6)] +          # chop is profitable
            [mk(i, "trend_up", -1.0) for i in range(6)])      # trend_up loses


def test_walk_forward_grades_only_the_target_regime(seeded_sandbox, monkeypatch):
    from meridian import backtest
    goal = dict(config.goal()); goal["min_sample"] = 3
    res = backtest.BacktestResult(trades=_fake_trades(), equity=[], params={}, start="2024-01-01", end="2024-12-31")
    monkeypatch.setattr(backtest, "replay", lambda *a, **k: res)
    wf_chop = backtest.walk_forward({}, {}, __import__("pandas").DataFrame({"date": []}), goal,
                                    "2024-01-01", "2024-01-01", "2024-12-31", "2024-12-31",
                                    eval_regime="chop")
    wf_all = backtest.walk_forward({}, {}, __import__("pandas").DataFrame({"date": []}), goal,
                                   "2024-01-01", "2024-01-01", "2024-12-31", "2024-12-31")
    assert wf_chop["eval_regime"] == "chop" and wf_chop["n_trades_graded"] == 6
    assert wf_all["n_trades_graded"] == 12
    # chop-only grading sees the profitable slice; global grading sees the mixed book → scores differ
    assert wf_chop["oos_score"] is not None and wf_chop["oos_score"] > wf_all["oos_score"]


def test_thin_regime_slice_cannot_ship(seeded_sandbox, monkeypatch):
    """min_sample floor applies to the SLICE: 2 high_vol trades → score None → gate refuses honestly."""
    from meridian import backtest, reflect
    goal = dict(config.goal()); goal["min_sample"] = 5
    trades = _fake_trades()[:12] + [{"ts_open": "2024-03-10", "ts_close": "2024-03-15",
                                     "regime": "high_vol", "r_multiple": 3.0, "pnl_dollars": 300.0}] * 2
    res = backtest.BacktestResult(trades=trades, equity=[], params={}, start="2024-01-01", end="2024-12-31")
    monkeypatch.setattr(backtest, "replay", lambda *a, **k: res)
    wf = backtest.walk_forward({}, {}, __import__("pandas").DataFrame({"date": []}), goal,
                               "2024-01-01", "2024-01-01", "2024-12-31", "2024-12-31",
                               eval_regime="high_vol")
    assert wf["oos_score"] is None and wf["n_trades_graded"] == 2
    passes, gate, why = reflect._gate_eval({**wf, "oos_folds": []}, {**wf, "oos_folds": []})
    # ince rejim dilimi iki yasadan biriyle durdurulur: legacy min_sample YA DA v3 olasılıksal
    # dilim tabanı ("arama dilimi ince") — koruma aynı, v3 gerekçesi daha açık.
    assert passes is False and ("min_sample" in why or "dilimi ince" in why)


def test_eval_regime_derivation():
    from meridian.reflect import _eval_regime_of
    assert _eval_regime_of("stop_loss_atr_mult@chop") == "chop"
    assert _eval_regime_of("stop_loss_atr_mult") is None
    assert _eval_regime_of("stop_loss_atr_mult@risk_off") is None   # phantom regime → global grading


# ============ P3.c — regime-scoped STRICT-AND reflection horizon ============
def test_horizon_regime_scoped_count_and_span():
    from meridian import hermes_runtime as hr
    trades = ([{"ts_close": "2026-01-01", "regime": "chop"}, {"ts_close": "2026-02-15", "regime": "chop"},
               {"ts_close": "2026-02-16", "regime": "chop"}, {"ts_close": "2026-02-17", "regime": "chop"},
               {"ts_close": "2026-02-18", "regime": "chop"}] +                      # 5 chop over 48 days
              [{"ts_close": "2026-02-1%d" % (i + 1), "regime": "trend_up"} for i in range(5)])  # 5 trend_up in 5 days
    assert hr._horizon_ok(trades, 0, min_days=30, regime="chop", min_trades=5) is True
    assert hr._horizon_ok(trades, 0, min_days=30, regime="trend_up", min_trades=5) is False  # clustered → defer
    assert hr._horizon_ok(trades, 0, min_days=30, regime="chop", min_trades=6) is False      # count is AND'd too
    assert hr._horizon_ok(trades, 0, min_days=30, regime="high_vol", min_trades=1) is False  # no trades in regime


# ============ P3.d — market_regime telemetry + parent-score reachability ============
def test_writeback_lifts_market_regime_top_level(seeded_sandbox):
    from meridian import memory
    memory.record({"id": "H1", "version_to": 7, "status": "live", "predicted_delta": 0.05})
    hyp = memory.writeback_outcome(7, realized_delta=-0.02,
                                   realized_detail={"cur_score": 0.1, "par_score": 0.12, "n": 30,
                                                    "market_regime": "chop|trend_up"})
    assert hyp["market_regime"] == "chop|trend_up"                  # top-level, greppable
    assert store.read_jsonl("hypotheses.jsonl")[-1]["market_regime"] == "chop|trend_up"
    assert hyp["calibration_hit"] is False                          # predicted +, realized − → honest miss


def test_parent_score_falls_back_to_shipping_gate(seeded_sandbox):
    """Parent has no live trades AND no scoreboard row (re-seeded ledger) → the shipping hypothesis's
    incumbent OOS is the score the child had to beat; evaluate_outcomes must reach the writeback."""
    from meridian import memory, rollback
    memory.record({"id": "H1", "version_to": 2, "status": "live", "predicted_delta": 0.06,
                   "backtest": {"incumbent_oos": 0.1963, "candidate_oos": 0.2555}})
    assert rollback._parent_score_fallback(2, None) == 0.1963
    assert rollback._parent_score_fallback(2, 0.5) == 0.5           # explicit score always wins
    assert rollback._parent_score_fallback(9, None) is None         # unknown version → still None


# ============ adversarial-review fixes ============
def test_rollback_measures_regime_ship_on_regime_slice_only(seeded_sandbox):
    """F1 (HIGH): a var@regime ship's realized outcome must be measured on that regime's trades only,
    against the identically-sliced gate incumbent — never global-live vs regime-sliced-backtest."""
    from meridian import memory, rollback, versioning
    import yaml
    config.dump_yaml({"version": 2, "parent": 1, "params": {"stop_loss_atr_mult": 2.0}},
                     config.strategy_path())
    memory.record({"id": "H1", "version_to": 2, "status": "live", "variable": "stop_loss_atr_mult@chop",
                   "predicted_delta": 0.05, "backtest": {"incumbent_oos": 0.10, "eval_regime": "chop"}})
    goal = dict(config.goal()); goal["min_sample"] = 3; goal["rollback_if_worse_by"] = 0.5
    # 3 chop trades under v2 (profitable) + a pile of trend_up v2 trades that must NOT enter the measure
    for i in range(3):
        store.append_jsonl("trades.jsonl", {"strategy_version": 2, "regime": "chop", "r_multiple": 1.0,
                                            "pnl_dollars": 500.0, "ts_open": f"2026-0{i+1}-10",
                                            "ts_close": f"2026-0{i+1}-20"})
    for i in range(6):
        store.append_jsonl("trades.jsonl", {"strategy_version": 2, "regime": "trend_up", "r_multiple": -2.0,
                                            "pnl_dollars": -2000.0, "ts_open": f"2026-0{i+1}-11",
                                            "ts_close": f"2026-0{i+1}-21"})
    out = rollback.evaluate_outcomes(goal)
    assert out is not None and out["rolled_back"] is False
    hyp = [h for h in store.read_jsonl("hypotheses.jsonl") if h["id"] == "H1"][0]
    assert hyp["realized_detail"]["n"] == 3                       # ONLY the chop slice was measured
    assert hyp["realized_detail"]["eval_regime"] == "chop"
    assert hyp["realized_detail"]["par_score"] == 0.10            # sliced gate incumbent, not a global score
    sb = versioning.scoreboard()["versions"]["2"]
    assert "live_score@chop" in sb and "live_score" not in sb     # global baseline NOT polluted


def test_guard_regime_noop_uses_effective_value_and_missing_base_rejected(seeded_sandbox):
    """F2/F9: reverting a regime override to the flat value is a REAL change (not a no-op); an override
    on a knob absent from flat params is honestly rejected instead of shipping a silent no-op."""
    from meridian import guard
    bounds = config.bounds()
    params = {"stop_loss_atr_mult": 2.0}
    by = {"chop": {"stop_loss_atr_mult": 1.8}}
    v = guard.validate_change({"variable": "stop_loss_atr_mult@chop", "new": 2.0},
                              params, bounds, config.goal(), [], 0, params_by_regime=by)
    assert v.ok, v.reasons                                        # 1.8 → 2.0 in chop is a real reversion
    v2 = guard.validate_change({"variable": "stop_loss_atr_mult@chop", "new": 1.8},
                               params, bounds, config.goal(), [], 0, params_by_regime=by)
    assert not v2.ok and any("no-op" in r for r in v2.reasons)    # already 1.8 in chop → no-op
    v3 = guard.validate_change({"variable": "exit.giveback_pct@chop", "new": 0.1},
                               {"stop_loss_atr_mult": 2.0}, bounds, config.goal(), [], 0)
    assert not v3.ok and any("silently ignored" in r for r in v3.reasons)


def test_reflection_baseline_survives_restart(seeded_sandbox):
    """F4 (HIGH): a fresh process must restore last_reflect_at from hermes_status.json — not re-baseline
    to the ledger length (which reset the 30-day horizon clock on every restart → livelock)."""
    from meridian import hermes_runtime as hr
    for i in range(8):
        store.append_jsonl("trades.jsonl", {"id": f"T{i}"})
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": 5})
    assert hr._restored_baseline() == 5                           # restored, not 8
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": 99})
    assert hr._restored_baseline() == 8                           # re-seeded shorter ledger → clamp
    store.write_json(hr.STATUS_FILE, {})
    assert hr._restored_baseline() == 8                           # first-ever run → current length


def test_save_broker_persists_rejections_and_dedup_set(seeded_sandbox):
    """F5: portfolio.json must carry broker_rejected (dashboard ledger) and alpaca_submitted (the
    double-submit dedup set) across restarts."""
    from meridian import loop
    from meridian.broker import PaperBroker
    b = PaperBroker(100_000, 5, 0.0)
    meta = {"armed": [], "pending_exits": {}, "last_date": "2026-07-18", "day_start_equity": 100_000,
            "alpaca_submitted": ["P-1", "P-2"],
            "broker_rejected": [{"date": "2026-07-18", "plan_id": "P-3", "ticker": "AAA", "detail": "x"}]}
    loop._save_broker(b, meta)
    _, meta2 = loop._load_broker()
    assert meta2["alpaca_submitted"] == ["P-1", "P-2"]
    assert meta2["broker_rejected"][0]["plan_id"] == "P-3"


def test_full_audit_critical_fixes(seeded_sandbox, monkeypatch):
    """2026-07-18 tam denetim kritikleri: #41 fetch_end per-call, #10 peak_equity persisted,
    #17/#31 version numbers never reused, #11 duplicate trade rows suppressed."""
    import datetime as dt
    from meridian import dataset, loop, versioning
    from meridian.broker import PaperBroker
    # 41: fetch_end() computes per call (module constant is only a display snapshot)
    assert dataset.fetch_end() == dt.date.today().isoformat()
    # 10: peak_equity round-trips through portfolio.json
    b = PaperBroker(100_000, 5, 0.0)
    loop._save_broker(b, {"armed": [], "pending_exits": {}, "last_date": "2026-07-18",
                          "day_start_equity": 100_000, "peak_equity": 123_456.0})
    assert loop._load_broker()[1]["peak_equity"] == 123_456.0
    # 17/31: after a rollback (scoreboard already has v2), bump from v1 must allocate v3, not v2
    versioning.update_scoreboard(2, rolled_back=True)
    child = versioning.bump({"version": 1, "params": {"entry.min_score": 60}}, "entry.min_score", 61)
    assert child["version"] == 3 and child["parent"] == 1
    # 11: identical closed-trade row is appended once
    row = {"plan_id": "P-X", "ticker": "AAA", "ts_close": "2026-07-18", "exit_reason": "stop", "exit": 99.5}
    loop._persist_trade(dict(row)); loop._persist_trade(dict(row))
    assert len([t for t in store.read_jsonl("trades.jsonl") if t.get("plan_id") == "P-X"]) == 1


# ============ çok-sağlayıcılı beyin (Nous Hermes · Gemini · Claude · deterministik) ============
def test_brain_chain_resolution_and_order(seeded_sandbox, monkeypatch):
    from meridian import hermes, secrets
    vals = {}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)   # makinede kurulu yerel ajan testi etkilemesin
    assert hermes.active_brain() == "deterministic"              # hiç anahtar yok
    vals["GEMINI_OAUTH_TOKEN"] = "tok"                           # OAuth tek başına yeter
    assert hermes.active_brain() == "gemini"                     # (varsayılan sırada claude/nous hazır değil)
    vals["NOUS_API_KEY"] = "nk"
    assert hermes.active_brain() == "nous"                       # sırada gemini'den önce
    vals["HERMES_BRAIN_ORDER"] = "gemini,nous,claude"
    assert hermes.active_brain() == "gemini"                     # operatör sırası kazanır
    assert hermes.active_model() == hermes.GEMINI_DEFAULT_MODEL
    vals["GEMINI_MODEL"] = "gemini-2.5-flash"
    assert hermes.active_model() == "gemini-2.5-flash"


def test_parse_hyp_repairs_panel_wrapped_json_and_skips_prompt_echo():
    """hermes-agent CLI gerçekçiliği (canlıda bulunan iki hata): (1) prompt başa echo'lanır — ilk JSON
    cevap değildir; (2) çıktı paneli uzun stringleri ~80 sütunda sarar — string İÇİNE ham \\n düşer."""
    from meridian.hermes import _extract_json, _parse_hyp
    out = ('Query: kocaman baglam {"goal": {"a": 1}} devam ediyor...\n'
           "╭─ ⚕ Hermes ────────────╮\n"
           '    {\n      "variable": "entry.min_score",\n      "new": 62,\n'
           '      "rationale": "uzun bir gerekce satiri panel tarafindan\n'
           '    sarilmis ve girintilenmis halde devam ediyor",\n'
           '      "predicted_direction": "improve_oos_score",\n      "predicted_delta": 0.02,\n'
           '      "confidence": 0.5,\n      "regime": "chop"\n    }\n'
           "╰───────────────────────╯\nSession: x\n")
    h = _parse_hyp(_extract_json(out))
    assert h and h["variable"] == "entry.min_score"
    assert "sarilmis ve girintilenmis" in h["rationale"]          # string-içi sarma tek boşluğa katlandı


def test_parse_hyp_tolerates_fences_and_rejects_junk():
    from meridian.hermes import _parse_hyp
    good = '```json\n{"variable":"entry.min_score","new":62,"rationale":"x","predicted_direction":"improve_oos_score","predicted_delta":0.02,"confidence":0.5,"regime":"chop"}\n```'
    assert _parse_hyp(good)["variable"] == "entry.min_score"
    assert _parse_hyp("not json") is None
    assert _parse_hyp('{"rationale":"no variable"}') is None     # şekil doğrulaması


def test_llm_chain_falls_through_on_provider_error(seeded_sandbox, monkeypatch):
    """Zincir dayanıklılığı: ilk sağlayıcı patlarsa sıradaki dener; başaran kaynak etiketi taşır."""
    from meridian import hermes, secrets, spend
    vals = {"HERMES_BRAIN_ORDER": "nous,gemini", "NOUS_API_KEY": "nk", "GEMINI_API_KEY": "gk"}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    monkeypatch.setattr(spend, "over_budget", lambda *a, **k: False)
    def boom():
        raise RuntimeError("nous down")
    monkeypatch.setattr(hermes, "_propose_nous", boom)
    monkeypatch.setattr(hermes, "_propose_gemini",
                        lambda: {"variable": "entry.min_score", "new": 62, "rationale": "g",
                                 "predicted_direction": "improve_oos_score", "predicted_delta": 0.02,
                                 "confidence": 0.5, "regime": "chop"})
    hyp = hermes.propose_with_llm()
    assert hyp is not None and hyp["source"] == "hermes:gemini"
    # bütçe kapısı TÜM ücretli beyinleri keser
    monkeypatch.setattr(spend, "over_budget", lambda *a, **k: True)
    assert hermes.propose_with_llm() is None


def test_nous_local_mode_detection_and_headless_call(seeded_sandbox, monkeypatch, tmp_path,
                                                     hermes_bin_cozumleyici_asil):
    """Yerel hermes-agent = uygulamanın parçası: ikili varsa Nous beyni ANAHTARSIZ hazırdır ve öneri
    tek atımlık `hermes chat -q` süreciyle alınır; 'local' zorlaması ve URL modu ayrışır.

    Conftest'teki `_yerel_ajan_ikilisi_kapali` autouse saplamasının BİLİNÇLİ istisnasıdır: burada
    ölçülen şey çözümleyicinin KENDİSİ, dolayısıyla gerçek fonksiyon geri takılır."""
    import subprocess
    from meridian import hermes, secrets
    monkeypatch.setattr(hermes, "_hermes_bin", hermes_bin_cozumleyici_asil)
    vals = {}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    fake_bin = tmp_path / "hermes"; fake_bin.write_text("#!/bin/sh\n"); fake_bin.chmod(0o755)
    monkeypatch.setenv("HERMES_LOCAL_BIN", str(fake_bin))
    assert hermes._hermes_bin() == str(fake_bin)
    assert hermes._nous_local() is True                        # boş endpoint + yerel ikili → yerel
    assert hermes._provider_ready("nous") is True              # anahtar gerekmez
    vals["NOUS_ENDPOINT"] = "https://ornek.uc/v1"
    assert hermes._nous_local() is False                       # URL → uzak mod
    vals["NOUS_ENDPOINT"] = "local"
    assert hermes._nous_local() is True                        # zorla yerel
    seen = {}
    class Out:
        returncode = 0
        stdout = 'durum çubuğu\n{"variable":"entry.min_score","new":62,"rationale":"r","predicted_direction":"improve_oos_score","predicted_delta":0.02,"confidence":0.5,"regime":"chop"}\n'
        stderr = ""
    def fake_run(cmd, **kw):
        seen["cmd"] = cmd; return Out()
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(hermes, "build_context", lambda: "{}")
    hyp = hermes._propose_nous()
    assert hyp and hyp["variable"] == "entry.min_score"
    assert seen["cmd"][0] == str(fake_bin) and seen["cmd"][1] == "chat"       # headless tek atım
    assert "--accept-hooks" in seen["cmd"] and "-q" in seen["cmd"]            # koruma hook'u onaylı çağrı


def test_gemini_key_syncs_local_agent_and_restores_on_delete(seeded_sandbox, monkeypatch, tmp_path):
    """Tek giriş noktası ARAYÜZ: Gemini anahtarı girilince yerel ajan Gemini'a çevrilir (Nous ayarı
    yedeklenir, .env'e OPENAI_API_KEY yazılır); anahtar silinince eski ayar geri yüklenir."""
    import subprocess, os as _os, json as _json
    from meridian import hermes, secrets
    home = tmp_path / ".hermes"; home.mkdir()
    (home / ".env").write_text("MEVCUT_SATIR=korunur\n")
    fake_bin = tmp_path / "hermes"; fake_bin.write_text("#!/bin/sh\n"); fake_bin.chmod(0o755)
    monkeypatch.setenv("HERMES_LOCAL_BIN", str(fake_bin))
    monkeypatch.setattr(_os.path, "expanduser", lambda p: str(home) if p == "~/.hermes" else p)
    vals = {"GEMINI_API_KEY": "gk-123", "GEMINI_MODEL": None}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    calls = []
    class R:
        returncode = 0; stderr = ""
        stdout = "nous\n"     # config get cevabı (yedek için)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd) or R())
    res = hermes.sync_local_agent_gemini(enable=True)
    # SABİTTEN TÜRETİLİR (2026-08-12): çıplak "gemini-3.1-pro" Google listesinden hiç geçmedi → 404
    # sınıfı; varsayılan artık sabit alias (GEMINI_DEFAULT_MODEL) ve test adı çivilemez.
    assert res["ok"] and hermes.GEMINI_DEFAULT_MODEL in res["detail"]
    env = (home / ".env").read_text()
    assert "GEMINI_API_KEY=gk-123" in env and "MEVCUT_SATIR=korunur" in env   # diğer satırlar korunur
    assert (home / "meridian-model-backup.json").exists()                      # Nous ayarı yedeklendi
    sets = [c for c in calls if c[1:3] == ["config", "set"]]
    assert any("model.provider" in c and "gemini" in c for c in sets)
    assert any("model.default" in c and hermes.GEMINI_DEFAULT_MODEL in c for c in sets)
    res2 = hermes.sync_local_agent_gemini(enable=False)
    assert res2["ok"]
    env2 = (home / ".env").read_text()
    assert "GEMINI_API_KEY" not in env2 and "MEVCUT_SATIR=korunur" in env2     # anahtar silindi, kalan korundu
    assert not (home / "meridian-model-backup.json").exists()                  # yedek tüketildi


def test_review_candidates_is_advisory_and_shape_gated(seeded_sandbox, monkeypatch, tmp_path):
    """Aday danışma katmanı: yerel ajan skill'lerle İKİNCİ GÖRÜŞ verir — kapı kararlarına dokunmaz,
    geçersiz görüşler elenir, sonuç atomik state dosyasına yazılır."""
    import subprocess
    from meridian import hermes, secrets
    monkeypatch.setattr(secrets, "get", lambda k: None)
    fake_bin = tmp_path / "hermes"; fake_bin.write_text("#!/bin/sh\n"); fake_bin.chmod(0o755)
    monkeypatch.setenv("HERMES_LOCAL_BIN", str(fake_bin))
    store.append_jsonl("trade_plans.jsonl", {"date": "2026-07-18", "ticker": "AAA", "setup": "breakout_vcp",
                                             "gate_verdict": "GO", "entry_trigger": 10, "stop": 9,
                                             "profit_target": 12, "size_r": 1, "score": 70})
    seen = {}
    class Out:
        returncode = 0
        stdout = ('╭─ ⚕ Hermes ─╮\n    {"reviews":[{"ticker":"AAA","opinion":"destekle","note":"vcp taban sıkı"},'
                  '{"ticker":"AAA","opinion":"bozuk-görüş","note":"elenmeli"}]}\n╰─╯\n')
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: seen.update(cmd=cmd) or Out())
    res = hermes.review_candidates("2026-07-18")
    assert res and len(res["reviews"]) == 1 and res["reviews"][0]["opinion"] == "destekle"
    assert "-s" in seen["cmd"] and "vcp-screener" in seen["cmd"]          # skill'ler önceden yüklendi
    saved = store.read_json("candidate_review.json", {})
    assert saved["date"] == "2026-07-18" and "kapı" in saved["note"]      # danışma sınırı kayıtta
    plan = store.read_jsonl("trade_plans.jsonl")[-1]
    assert plan["gate_verdict"] == "GO"                                    # kapı kararına dokunulmadı


def test_gemini_proposer_parses_rest_response(seeded_sandbox, monkeypatch):
    import httpx
    from meridian import hermes, secrets
    vals = {"GEMINI_API_KEY": "gk"}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    monkeypatch.setattr(hermes, "build_context", lambda: "{}")
    payload = {"candidates": [{"content": {"parts": [{"text":
        '{"variable":"stop_loss_atr_mult","new":2.1,"rationale":"r","predicted_direction":"improve_oos_score","predicted_delta":0.01,"confidence":0.4,"regime":"chop"}'}]}}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}}
    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return payload
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R())
    hyp = hermes._propose_gemini()
    assert hyp and hyp["variable"] == "stop_loss_atr_mult"


def test_fetch_prefers_fresher_fallback_over_stale_first_source(seeded_sandbox, monkeypatch):
    """İleri-dönük değerlendirme tazelik ister: boş-olmayan ama BAYAT ilk kaynak, daha taze fallback'i
    engelleyemez (canlı kanıt: 19 sembol Cboe'nin 1 seans gerisinde kalmıştı, Nasdaq hiç denenmemişti)."""
    import pandas as pd
    from meridian.adapters import data, fmp
    def bars_ending(day):
        dates = pd.bdate_range(end=day, periods=30)
        return pd.DataFrame({"date": dates, "open": 100.0, "high": 101.0, "low": 99.0,
                             "close": 100.0, "volume": 1e6})
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(data, "_fetch_fmp", lambda *a, **k: pd.DataFrame())          # FMP bu sembolü taşımıyor
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: bars_ending("2026-07-16"))   # bayat ama dolu
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: bars_ending("2026-07-17"))  # taze
    out = data.fetch("XYZ", "2026-06-01", "2026-07-18")
    assert str(out["date"].max())[:10] == "2026-07-17"          # taze fallback kazandı
    # TAZE KAYNAK İLK SIRADAYSA ZİNCİR ERKEN DURUR — iddia aynı, SIRA değişti (2026-08-25).
    # Eski hâl FMP'yi ilk sıraya koyup `cboe` çağrılmadığını ölçüyordu. FMP artık zincirin
    # SONUNDA (kota daraltması: ücretsiz plan 250/gün, evren 251 sembol — tek tazeleme kotayı
    # yakıyordu) ve bu testin ölçtüğü tasarruf ters yöne döndü: anahtarsız kaynak yeterliyse
    # FMP'ye İSTEK ATILMAZ. Ölçülen kazanç ≥219 çağrı/gün.
    # ÇİVİ GÜÇLENDİ: eskiden "bir kaynak atlandı" diyordu, şimdi "KOTALI kaynak atlandı" diyor.
    calls = {"fmp": 0}
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: bars_ending("2026-07-17"))   # taze, ANAHTARSIZ
    monkeypatch.setattr(data, "_fetch_fmp",
                        lambda *a, **k: calls.__setitem__("fmp", calls["fmp"] + 1) or pd.DataFrame())
    out2 = data.fetch("XYZ", "2026-06-01", "2026-07-18")
    assert str(out2["date"].max())[:10] == "2026-07-17" and calls["fmp"] == 0, (
        f"anahtarsız kaynak taze barı verdiği hâlde FMP'ye {calls['fmp']} istek atıldı — "
        "kota daraltması geri alınmış olabilir (zincir sırası: cboe → nasdaq → fmp)")


def test_scheduler_flag_survives_publish_lag(seeded_sandbox, monkeypatch):
    """Refetch bayrağı, kapanan seansın barı GERÇEKTEN gelene dek tüketilmez — yayın gecikmesinde
    sınırlı yeniden deneme; bar gelince bayrak yanar ve tekrar cache-only'ye döner.

    2026-07-22'de GÜNCELLENDİ: bu test eskiden tazeliği yalnız ENDEKSTEN modelliyordu (evren boş
    sözlüktü) — yani uygulamayı kilitleyen hatanın ta kendisini kodluyordu. SPY erken yayınlayan
    azınlıktandır; canlıda 07-21 barı 250 sembolün 46'sındaydı ve bayrak ilk denemede tükenip
    kalan 204 sembol bir daha çekilmiyordu. Ölçüt artık EVREN kapsamasıdır, endeks değil."""
    import pandas as pd
    from meridian import scheduler, health
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-20")
    seen = []

    def _uni(session_arrived: bool) -> dict:
        """20 sembollük evren: seans barı ya HEPSİNDE var ya HİÇBİRİNDE."""
        dates = ["2026-07-17"] + (["2026-07-20"] if session_arrived else [])
        return {f"T{i}": pd.DataFrame({"date": pd.to_datetime(dates)}) for i in range(20)}

    stale = (_uni(False), pd.DataFrame({"date": [pd.Timestamp("2026-07-17")]}))
    fresh = (_uni(True), pd.DataFrame({"date": [pd.Timestamp("2026-07-20")]}))
    feed = {"now": stale}
    from meridian import dataset, loop
    monkeypatch.setattr(dataset, "load", lambda use_cache=True: seen.append(use_cache) or feed["now"])
    monkeypatch.setattr(loop, "daily_cycle",
                    lambda b, i, on_date=None: {"status": "ok", "date": "2026-07-20"})
    scheduler._state.update(last_refetch_session=None, refetch_attempts=0)
    scheduler.advance_once()                                    # bar henüz yok → bayrak YANMAZ
    assert scheduler._state["last_refetch_session"] is None and scheduler._state["refetch_attempts"] == 1
    assert seen[-1] is False                                    # ağdan denedi (use_cache=False)
    feed["now"] = fresh
    scheduler.advance_once()                                    # bar geldi → bayrak yanar, sayaç sıfır
    assert scheduler._state["last_refetch_session"] == "2026-07-20"
    assert scheduler._state["refetch_attempts"] == 0
    scheduler.advance_once()                                    # aynı seans → artık cache-only
    assert seen[-1] is True


def test_horizon_progress_is_observable(seeded_sandbox):
    """F6: the dashboard needs the strict-AND horizon as numbers, regime-scoped."""
    from meridian import hermes_runtime as hr
    trades = [{"ts_close": "2026-01-01", "regime": "chop"}, {"ts_close": "2026-02-15", "regime": "chop"},
              {"ts_close": "2026-02-16", "regime": "trend_up"}]
    hz = hr._horizon_progress(trades, 0, "chop", min_trades=5, min_days=30)
    assert hz == {"regime": "chop", "trades": 2, "trades_needed": 5,
                  "span_days": 45, "min_days": 30, "ready": False}


def test_probe_cache_keys_on_params_not_version(seeded_sandbox, monkeypatch):
    """F3: two different parameter worlds under the SAME version number (rollback → re-ship) must not
    share probe cache entries."""
    from meridian import reflect, backtest
    calls = []
    def fake_wf(params, *a, **k):
        calls.append(dict(params))
        return {"oos_score": 0.1, "oos_folds": [], "oos_tail_risk": None, "holdout_score": 0.1}
    monkeypatch.setattr(backtest, "walk_forward", fake_wf)
    reflect._PROBE_CACHE.clear()
    w = ("2022-01-01", "2024-01-01", "2025-01-01", "2025-06-30", ("2024-01-01",), 5)
    s1 = {"version": 6, "params": {"entry.min_score": 60.0}}
    s2 = {"version": 6, "params": {"entry.min_score": 70.0}}      # same version, different world
    reflect._probe_wf(s1, "entry.min_score", 65, 6, None, None, config.goal(), w)
    reflect._probe_wf(s2, "entry.min_score", 65, 6, None, None, config.goal(), w)
    assert len(calls) == 2                                        # no stale cache hit across worlds


def test_reflect_once_targets_live_nondefault_regime(seeded_sandbox, monkeypatch):
    """Under a non-trend_up live regime the fallback search must become regime-targeted (var@regime,
    graded on that regime's slice); under trend_up it stays global (slice ≈ whole book).

    FİKSTÜR SINIFI (2026-07-30, üreteç keşif dengesi turu — N00002): bu test
    `test_sprint.py::test_reflect_once_searches_when_no_claude` ile AYNI kökü paylaşıyordu. Beyin
    zinciri boş dönünce `reflect_once` artık aramadan ÖNCE bakir bir düğmeden tek deterministik
    hamle üretip `reflect.submit`e veriyor; fikstür `submit`i mock'lamadığı için o hamle GERÇEK
    backtest'e girip `bars=None` üzerinde patlıyordu. Üretim hatası DEĞİL, eksik basamak.

    Kardeş testteki (a) çözümünün aynısı uygulandı — `HERMES_VIRGIN_FALLBACK=0` yamalamak testi
    varsayılan-olmayan bir yapılandırmada koştururdu ve bakir yol bir gün yansımayı yutsa test yine
    yeşil kalırdı. Bu testin ASIL iddiası (rejim hedeflemesi) korunuyor; üstüne bu turun eklediği
    gerçek iddiaya dahil edildi: bakir hamle her zaman KÜRESELdir (`@rejim` soneki YOK), yani rejim
    hedefleme kararı bütünüyle aramaya ait kalır ve bu basamak onu ÖNCELEYEMEZ."""
    from meridian import hermes, reflect, dataset
    monkeypatch.setattr(hermes, "propose_with_claude", lambda: None)
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    onerilen = []

    def fake_submit(prop, *a, **k):
        onerilen.append(prop)
        return {"status": "rejected_by_backtest"}      # ship etmez → arama devralır
    monkeypatch.setattr(reflect, "submit", fake_submit)
    seen = {}

    def fake_search(bars, index, goal=None, *, windows, budget, k_max, on_probe=None, regime=None):
        seen["regime"] = regime
        return {"status": "no_clearing_candidate", "search": {}}
    monkeypatch.setattr(reflect, "search_and_submit", fake_search)
    # K1 DAMGASI (EDG-2026-048, 2026-08-23): örnek rejim `chop`tu; `@chop` üretimi duraklatılınca
    # canlı chop turu bilinçli olarak globale düşer (çivisi test_k5_paketi_v273::test_d5/d6).
    # Bu testin iddiası — varsayılan-dışı canlı rejim hedeflenir — duraklatmasız rejimle sürer.
    store.write_json("regime.json", {"regime": "trend_down"})
    hermes.reflect_once()
    assert seen["regime"] == "trend_down"
    store.write_json("regime.json", {"regime": "trend_up"})
    hermes.reflect_once()
    assert seen["regime"] is None
    # Bakir basamak her iki turda da çalıştı ve HER İKİSİNDE de küresel bir düğme önerdi: rejim
    # hedeflemesi aramaya ait, bu basamak onu öncelemiyor.
    assert len(onerilen) == 2 and all(o["source"] == "deterministic:virgin" for o in onerilen)
    assert all("@" not in o["variable"] for o in onerilen), \
        "bakir hamle rejim-hedefli geldi — aramanın rejim kararını önceler"


def test_hypothesis_rows_stamp_market_regime_on_submit(seeded_sandbox):
    """Every NEW hypothesis row must carry the formation-time market_regime (guard-rejected path is the
    cheapest to exercise: an off-bounds variable never reaches the backtest)."""
    from meridian import reflect
    store.write_json("regime.json", {"regime": "chop", "date": "2026-07-15"})
    res = reflect.submit({"variable": "no_such_variable", "new": 1.0, "source": "test"})
    assert res["status"] == "rejected_by_guard"
    assert store.read_jsonl("hypotheses.jsonl")[-1]["market_regime"] == "chop"
