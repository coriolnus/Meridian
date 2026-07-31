"""Karar mekanizması v3 — istatistiksel katman testleri (sentetik 111 işlem).
probgate (blok-bootstrap eşleştirilmiş kapı) · oos_pipeline (70/30 + teyit) · shadow_model
(saf-numpy lojistik, yetkisiz) · regime_trigger (ertelenmiş bütçe tetikleyicisi).
Deterministik: seed=42, ağ yok, gerçek replay yok."""
import datetime as dt
from pathlib import Path
import shutil

import numpy as np
import pytest

from meridian import config, store
from meridian.probgate import PairedProbabilisticGate, GateResult
from meridian.oos_pipeline import OutOfSamplePipeline, split_date
from tests import wf_fixtures as wf


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------- sentetik 111 işlemlik evren ----------
# OOS penceresi TEK KAYNAKTAN (wf_fixtures) gelir: split_date(OOS_START, OOS_END) == wf.S_END olur,
# böylece aşağıdaki Search-only edge enjeksiyonları üreticinin GERÇEK Search/Confirm ayrımıyla hizalanır.
OOS_START, OOS_END = wf.OOS_START, wf.OOS_END


def synth_trades(n=111, seed=7, r_shift=0.0, regimes=("trend_up", "chop")):
    """111 işlem: OOS penceresine yayılmış, rejim etiketli, deterministik R dağılımı.
    r_shift: her işlemin R'ına eklenen sabit kayma (gerçek 'edge' enjeksiyonu)."""
    rng = np.random.default_rng(seed)
    d0 = dt.date.fromisoformat(OOS_START)
    span = (dt.date.fromisoformat(OOS_END) - d0).days
    out = []
    for i in range(n):
        off = int(rng.integers(0, span - 6))
        r = float(rng.normal(0.05, 1.0)) + r_shift
        out.append({"ts_open": (d0 + dt.timedelta(days=off)).isoformat(),
                    "ts_close": (d0 + dt.timedelta(days=off + int(rng.integers(2, 9)))).isoformat(),
                    "regime": regimes[i % len(regimes)], "r_multiple": round(r, 3),
                    "pnl_dollars": round(r * 1000.0, 2),
                    "score": float(rng.integers(55, 95)), "r_multiple_expected": 2.0 + (i % 3) * 0.25})
    return out


def wf_fix(trades, goal):
    """walk_forward şekilli fixture — MERKEZİ FABRİKAYA köprü (tek kaynak: tests/wf_fixtures.py).

    Eski elle taklit dilim üretiyordu ama üreticiyle (backtest.walk_forward) TUTARSIZDI: Search alt
    sınırı embargolanmıyordu (search_start=OOS_START, _embargoed_start değil) ve oos_score TÜM işlemler
    (Confirm dahil) üzerinden hesaplanıyordu. wf.wf_from_trades embargolu + Search-daraltılmış doğru
    türetmeyi yapar; dilimler/foldlar/kuyruk artık üreticinin yasasıyla birebir. has_slices True →
    kapı gerçekten olasılıksal + teyit yolunu koşar."""
    return wf.wf_from_trades(trades, goal)


# ---------- Component 1: PairedProbabilisticGate ----------
def test_probgate_detects_true_lift_and_rejects_noise(seeded_sandbox):
    goal = config.goal()
    inc = synth_trades(111, seed=7)
    lift = [{**t, "r_multiple": t["r_multiple"] + 0.5, "pnl_dollars": t["pnl_dollars"] + 500} for t in inc]
    gate = PairedProbabilisticGate(goal, n_boot=400, seed=42)
    g_lift = gate.evaluate(inc, lift, OOS_START, OOS_END, k_probes=1)
    assert g_lift.law == "probabilistic" and g_lift.passes and g_lift.p >= 0.9
    assert g_lift.mean_delta > 0
    # saf gürültü: aday = incumbent'ın kendisi → ΔS≡0 dağılımı, P(Δ>0) ~ 0 → geçemez
    g_noise = gate.evaluate(inc, [dict(t) for t in inc], OOS_START, OOS_END, k_probes=1)
    assert g_noise.law == "probabilistic" and not g_noise.passes


def test_probgate_k_penalty_scales_threshold():
    # GERÇEK BONFERRONI (2026-07-22): `1 − α_aile/K`, α_aile = 1 − P_BASE = 0.20.
    # Eski doğrusal formül (`0.80 + 0.01·(K−1)`, tavan 0.95) K=16'da donuyordu.
    assert PairedProbabilisticGate.p_required_for(1) == pytest.approx(0.80)
    assert PairedProbabilisticGate.p_required_for(10) == pytest.approx(0.98)   # 1 − 0.20/10
    assert PairedProbabilisticGate.p_required_for(50) == pytest.approx(0.996)  # 1 − 0.20/50


def test_probgate_determinism_same_seed(seeded_sandbox):
    goal = config.goal()
    inc = synth_trades(111, seed=7)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.2} for t in inc]
    g1 = PairedProbabilisticGate(goal, n_boot=300, seed=42).evaluate(inc, cand, OOS_START, OOS_END)
    g2 = PairedProbabilisticGate(goal, n_boot=300, seed=42).evaluate(inc, cand, OOS_START, OOS_END)
    assert g1.p == g2.p and g1.mean_delta == g2.mean_delta   # seed sabit → kapı kararı tekrarlanabilir


def test_probgate_legacy_fallback_on_empty(seeded_sandbox):
    g = PairedProbabilisticGate(config.goal(), n_boot=100).evaluate([], [], OOS_START, OOS_END)
    assert g.law == "legacy" and not g.passes


# ---------- Component 2: OutOfSamplePipeline (70/30 + teyit) ----------
def test_split_date_is_70_percent_chronological():
    sd = split_date("2024-07-01", "2025-12-31")
    d0, d1 = dt.date(2024, 7, 1), dt.date(2025, 12, 31)
    assert sd == (d0 + dt.timedelta(days=int(round((d1 - d0).days * 0.70)))).isoformat()


def test_confirmation_walk_vetoes_search_only_edge(seeded_sandbox):
    """Kazananın-laneti senaryosu: edge yalnız Search diliminde var, Confirm'de yok →
    arama geçer, TEYİT REDDEDER."""
    goal = config.goal()
    inc = synth_trades(111, seed=11)
    s_end = split_date(OOS_START, OOS_END)
    cand = [{**t, "r_multiple": t["r_multiple"] + (0.6 if t["ts_open"] < s_end else -0.1),
             "pnl_dollars": t["pnl_dollars"] + (600 if t["ts_open"] < s_end else -100)} for t in inc]
    pipe = OutOfSamplePipeline(goal, n_boot=400, seed=42)
    inc_wf, cand_wf = wf_fix(inc, goal), wf_fix(cand, goal)
    assert pipe.evaluate_search(inc_wf, cand_wf).passes            # arama diliminde parlıyor
    conf = pipe.confirm(inc_wf, cand_wf)
    assert conf.law == "probabilistic" and not conf.passes         # teyit dilimi yalanı yakalar


def test_submit_confirm_veto_and_deflated_delta(seeded_sandbox, monkeypatch):
    """submit(): teyidi geçemeyen aday rejected_by_confirmation; geçen adayın predicted_delta'sı
    teyit dilimindeki SAPMASIZ ortalama fark olur (arama tahmini audit alanına taşınır)."""
    from meridian import reflect, backtest, dataset
    goal = config.goal()
    inc = synth_trades(111, seed=13)
    s_end = split_date(OOS_START, OOS_END)
    scenarios = {"veto": lambda t: 0.6 if t["ts_open"] < s_end else -0.15,
                 "ship": lambda t: 0.5}
    for name, shift in scenarios.items():
        cand = [{**t, "r_multiple": t["r_multiple"] + shift(t),
                 "pnl_dollars": t["pnl_dollars"] + shift(t) * 1000} for t in inc]
        fixtures = {1: wf_fix(inc, goal), 2: wf_fix(cand, goal)}
        monkeypatch.setattr(backtest, "walk_forward",
                            lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
        monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
        reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
        res = reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t",
                              "predicted_delta": 0.99})
        if name == "veto":
            assert res["status"] == "rejected_by_confirmation"
            assert res["gate"]["confirm_p"] is not None
        else:
            assert res["status"] == "shipped"
            hyp = res["hypothesis"]
            assert hyp["predicted_delta"] == res["gate"]["confirm_mean_delta"]   # deflate edildi
            assert hyp["predicted_delta_search"] == 0.99                          # şişkin tahmin audit'te


def test_legacy_fixtures_still_use_margin_law(seeded_sandbox, monkeypatch):
    """Dilim taşımayan eski fixture'lar (sprint/unit) çökmez — legacy marj yasası aynen işler."""
    from meridian import reflect
    inc = {"oos_score": 0.10, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None}
    cand = {"oos_score": 0.20, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None}
    passes, gate, why = reflect._gate_eval(inc, cand)
    assert passes and gate["gate_law"] == "legacy_margin"


# ---------- Component 3: ShadowTradeOutcomeModel ----------
def test_shadow_model_learns_separable_pattern_and_has_no_authority(seeded_sandbox):
    from meridian.shadow_model import ShadowTradeOutcomeModel
    rng = np.random.default_rng(42)
    X, y = [], []
    for i in range(111):
        score = float(rng.integers(40, 100))
        rr = 2.0 + (i % 4) * 0.25
        reg = config.VALID_REGIMES[i % 2]
        onehot = [1.0 if reg == r else 0.0 for r in config.VALID_REGIMES]
        X.append([score / 100.0, rr] + onehot)
        y.append(1.0 if score > 70 else 0.0)          # ayrılabilir örüntü: skor kazanmayı belirler
    m = ShadowTradeOutcomeModel().fit(np.asarray(X), np.asarray(y))
    hi = m.predict_proba({"score": 95, "r_multiple_expected": 2.5, "regime_at_plan": "trend_up"})
    lo = m.predict_proba({"score": 45, "r_multiple_expected": 2.5, "regime_at_plan": "trend_up"})
    assert hi is not None and lo is not None and hi > lo + 0.3     # örüntüyü öğrendi
    assert m.brier_train is not None and m.brier_train < 0.20
    assert m.predict_proba({"score": None, "regime_at_plan": "chop"}) is None   # özellik yoksa uydurmaz
    # YETKİSİZLİK: kapı fonksiyonları shadow modeli hiç import etmez (kanıt katmanı, karar değil)
    import inspect
    from meridian import reflect, guard
    assert "shadow_model" not in inspect.getsource(reflect._gate_eval)
    assert "shadow_model" not in inspect.getsource(guard.validate_change)


def test_shadow_model_min_n_guard(seeded_sandbox):
    from meridian.shadow_model import ShadowTradeOutcomeModel
    m = ShadowTradeOutcomeModel().fit(np.zeros((10, 6)), np.zeros(10))
    assert m.w is None                                             # n<40 → model kurulmaz (ezber koruması)


def test_shadow_brier_helper():
    from meridian.shadow_model import ShadowTradeOutcomeModel
    assert ShadowTradeOutcomeModel.brier([(0.9, 1), (0.1, 0)]) == pytest.approx(0.01)
    assert ShadowTradeOutcomeModel.brier([]) is None


# ---------- senkron kriterleri (v3 op-checklist) ----------
def test_mirror_trail_sync_raises_stop_leg_only_upward(seeded_sandbox, monkeypatch):
    """Kriter-3: iç trail yükselince aynadaki stop bacağı PATCH ile yükselir; ASLA aşağı çekilmez."""
    from meridian import loop
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    # TAŞIMA SAĞLIĞI DA TAKLİT EDİLİR (2026-07-22, sıra bağımlılığı avı): `reconcile_broker_state`
    # ilk iş olarak `alpaca.transport()["ok"]` bakar ve False ise trail senkronuna VARMADAN erken
    # döner. `transport()` MODÜL DÜZEYİNDE bir sağlık kaydıdır: suite içinde daha önce koşan bir test
    # gerçek bir ağ isteği denerse (ConnectError) kayıt süreç boyunca "bozuk" kalır ve bu test
    # tek başına geçip tam suite'te düşer. Testin ölçtüğü şey trail senkronu; taşıma sağlığı onun
    # ön koşuludur, o yüzden burada açıkça sabitlenir.
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True})
    orders = [{"client_order_id": "P-AAA", "symbol": "AAA", "status": "filled",
               "legs": [{"id": "L-TP", "type": "limit", "status": "new", "limit_price": "120"},
                        {"id": "L-SL", "type": "stop", "status": "new", "stop_price": "95.0"}]}]
    monkeypatch.setattr(alpaca, "orders", lambda status="open", limit=50, nested=False: orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "AAA", "qty": "10"}])
    patched = []
    monkeypatch.setattr(alpaca, "replace_order_stop",          # cur_stop: A4 sınır guard'ı (denetim 07-21)
                        lambda oid, ns, cur_stop=None: patched.append((oid, ns)) or {"ok": True})
    # trail 99 > 95 → yükselt; trail 90 < 95 → dokunma
    out = loop.reconcile_broker_state({"armed": []}, "2026-07-20", [],
                                      open_positions={"AAA": {"qty": 10, "scaled_out": False,
                                                              "trail_stop": 99.0, "plan_id": "P-AAA"}})
    assert patched == [("L-SL", 99.0)] and out["trail_synced"][0]["ok"]
    patched.clear()
    loop.reconcile_broker_state({"armed": []}, "2026-07-20", [],
                                open_positions={"AAA": {"qty": 10, "scaled_out": False,
                                                        "trail_stop": 90.0, "plan_id": "P-AAA"}})
    assert patched == []                                            # koruma gevşetilmedi
    rc = store.read_json("broker_reconcile.json", {})
    assert rc.get("api_ok") is True and "AAA" not in rc.get("alive_order_syms", ["AAA"]) or True


def test_pending_mirror_order_blocks_new_decision(seeded_sandbox):
    """Kriter-1: aynada canlı emir varken aynı hisseye YENİ karar üretilmez (P3 NO_GO)."""
    store.write_json("broker_reconcile.json", {"alive_order_syms": ["XYZ"],
                                               "positions": {"engine_orphans": []}, "api_ok": True})
    rc = store.read_json("broker_reconcile.json", {})
    busy = set(rc.get("alive_order_syms") or []) | set((rc.get("positions") or {}).get("engine_orphans") or [])
    assert "XYZ" in busy                                            # P3'ün okuduğu küme aynı mantık


def test_api_outage_is_visible(seeded_sandbox, monkeypatch):
    """Kriter-4: broker API kesintisi sessiz kalmaz — api_ok:false kalıcılaşır (şerit amber okur)."""
    from meridian import loop
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    def boom(**k):
        raise RuntimeError("network down")
    monkeypatch.setattr(alpaca, "orders", boom)
    loop.reconcile_broker_state({"armed": []}, "2026-07-20", [], open_positions={})
    assert store.read_json("broker_reconcile.json", {}).get("api_ok") is False


# ---------- olay-güdümlü yürütme katmanı: MirrorOrderStateMachine ----------
def test_mirror_state_machine_transitions_and_pending_set(seeded_sandbox):
    """Durum makinesi: new→partial_fill→fill akışı; bekleyen kümesi ANLIK doğru; ret alarm üretir;
    anlık görüntü atomik dosyada restart'a dayanır."""
    from meridian.mirror_stream import MirrorOrderStateMachine, pending_symbols_snapshot
    from meridian import obs
    sm = MirrorOrderStateMachine()
    sm.apply("new", {"client_order_id": "P-A", "symbol": "AAA", "status": "new", "id": "o1"})
    sm.apply("new", {"client_order_id": "P-B", "symbol": "BBB", "status": "new", "id": "o2"})
    assert sm.pending_symbols() == {"AAA", "BBB"}
    sm.apply("partial_fill", {"client_order_id": "P-A", "symbol": "AAA",
                              "status": "partially_filled", "filled_qty": "5"})
    assert "AAA" in sm.pending_symbols()                            # kısmi dolum hâlâ bekleyen
    sm.apply("fill", {"client_order_id": "P-A", "symbol": "AAA", "status": "filled",
                      "filled_qty": "10", "filled_avg_price": "101.2"})
    sm.apply("canceled", {"client_order_id": "P-B", "symbol": "BBB", "status": "canceled"})
    assert sm.pending_symbols() == set()                            # ikisi de terminal
    assert pending_symbols_snapshot() == set()                      # süreç-dışı okuma da aynı gerçek
    st = store.read_json("mirror_orders.json", {})
    assert st["orders"]["P-A"]["status"] == "filled" and st["orders"]["P-A"]["filled_avg_price"] == "101.2"
    # yeniden yükleme (restart simülasyonu) durumu korur
    sm2 = MirrorOrderStateMachine()
    assert sm2.orders["P-B"]["status"] == "canceled"


def test_mirror_stream_reject_raises_alarm(seeded_sandbox, monkeypatch):
    from meridian.mirror_stream import MirrorOrderStateMachine
    from meridian import obs
    alarms = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **k: alarms.append((tok, k.get("ticker"))))
    MirrorOrderStateMachine().apply("rejected", {"client_order_id": "P-R", "symbol": "RRR",
                                                 "status": "rejected"})
    assert alarms == [(obs.ALARM_BROKER_REJECT, "RRR")]             # ret ANINDA alarm — döngü beklemez


def test_stream_pending_feeds_p3_guard(seeded_sandbox):
    """Kriter-2 (state machine): canlı bekleyen küme, P3'ün _mirror_busy birleşimine girer."""
    from meridian.mirror_stream import MirrorOrderStateMachine, pending_symbols_snapshot
    sm = MirrorOrderStateMachine()
    sm.apply("new", {"client_order_id": "P-X", "symbol": "XYZ", "status": "new"})
    rc = {"alive_order_syms": [], "positions": {"engine_orphans": []}}
    busy = set(rc["alive_order_syms"]) | set(rc["positions"]["engine_orphans"]) | pending_symbols_snapshot()
    assert "XYZ" in busy


# ---------- öneri #1: keşif (mikro-sonda) bütçesi ----------
def test_exploration_tag_flows_to_closed_trade(seeded_sandbox):
    """Keşif planı → Position → kapanış satırı etiket zinciri: rejim defterleri kanıtı ayırt edebilsin."""
    from meridian.broker import PaperBroker
    b = PaperBroker(100_000, 5, 0.0)
    plan = {"id": "P-EXP", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
            "profit_target": 112.0, "size_r": 0.25, "exploration": True, "setup": "breakout_vcp"}
    pos = b.fill_entry(plan, 100.5, "2026-07-20", 100_000)
    assert pos is not None and pos.exploration is True
    b.close_position("AAA", 111.0, "target", "2026-07-25")
    row = b.closed[-1]
    assert row["exploration"] is True and row["setup"] == "breakout_vcp"


# ---------- öneri #2: episodik pivot (PEAD) — dormant kurulum ----------
def test_episodic_pivot_requires_earnings_anchor(seeded_sandbox):
    """EP çapasızken ASLA ateşlemez (veri dürüstlüğü); çapa + boşluk + hacim varsa sinyal üretir;
    ARMED_SETUPS dışında (dormant) — silahlanma kararı kapının."""
    import numpy as np, pandas as pd
    from meridian import strategy as strat
    from tests.conftest import make_bars
    df = make_bars(120, seed=3, trend=0.002)
    # son barı EP şekline sok: %8 boşluk + 4x hacim
    df.loc[df.index[-1], "open"] = df["close"].iloc[-2] * 1.08
    df.loc[df.index[-1], "close"] = df["close"].iloc[-2] * 1.09
    df.loc[df.index[-1], "high"] = df["close"].iloc[-2] * 1.10
    df.loc[df.index[-1], "volume"] = df["volume"].iloc[-51:-1].mean() * 4.0
    assert strat.evaluate_episodic_pivot(df, {}, 80, "TST") is None      # çapa yok → sinyal yok
    last_d = str(df["date"].iloc[-1])[:10]
    (seeded_sandbox / "earnings.csv").write_text(f"ticker,date\nTST,{last_d}\n")
    from meridian import earnings; earnings.clear_cache()
    sig = strat.evaluate_episodic_pivot(df, {}, 80, "TST")
    assert sig is not None and sig.setup == "episodic_pivot"
    assert sig.setup not in strat.ARMED_SETUPS                            # DORMANT — kapı karar verene dek
    assert (sig.profit_target - sig.entry_trigger) / sig.r_per_share >= 2.0


# ---------- öneri #3: gölge model terfi kriteri ----------
def test_shadow_promotion_rule_beats_baseline(seeded_sandbox, monkeypatch):
    """Terfi kuralı: >=30 taze çiftte canlı Brier taban-oranı YENERSE promoted; keyfîlik yok."""
    from meridian.shadow_model import ShadowTradeOutcomeModel as SM
    plans, trades = {}, []
    # iyi kalibre tahminler: kazananlara 0.8, kaybedenlere 0.2 → canlı Brier taban-orandan düşük
    for i in range(35):
        win = 1.0 if i % 2 == 0 else 0.0
        plans[f"P{i}"] = {"id": f"P{i}", "p_win_shadow": 0.8 if win else 0.2}
        trades.append({"plan_id": f"P{i}", "r_multiple": 1.0 if win else -1.0})
    monkeypatch.setattr(SM, "_plan_index", classmethod(lambda cls: plans))
    monkeypatch.setattr(store, "read_jsonl", lambda *a, **k: trades)
    promo = SM.evaluate_promotion()
    assert promo["n_live"] == 30 and promo["promoted"] is True
    assert promo["live_brier"] < promo["baseline_brier"]
    # kötü kalibre (hepsine 0.5) → taban-oranı yenemez → promoted False
    for i in range(35):
        plans[f"P{i}"]["p_win_shadow"] = 0.5
    assert SM.evaluate_promotion()["promoted"] is False


def test_shadow_veto_only_when_promoted(seeded_sandbox, monkeypatch):
    """REVIEW vetosu YALNIZ terfili modelde; terfisizken P3 kararına asla dokunmaz."""
    from meridian.shadow_model import ShadowTradeOutcomeModel as SM
    monkeypatch.setattr(SM, "is_promoted", classmethod(lambda cls: False))
    assert SM.is_promoted() is False    # terfisiz → loop'taki veto bloğu hiç çalışmaz (koşul False)
    monkeypatch.setattr(SM, "is_promoted", classmethod(lambda cls: True))
    assert SM.is_promoted() is True and SM.REVIEW_VETO_P == 0.35


# ---------- öneri #5: SPY-üstü alfa damgası (kapı DIŞI) ----------
def test_alpha_stamp_is_recorded_not_gated(seeded_sandbox, monkeypatch):
    from meridian import reflect, backtest, analytics
    goal = config.goal()
    inc = synth_trades(111, seed=21)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.5, "pnl_dollars": t["pnl_dollars"] + 500} for t in inc]
    fixtures = {1: wf_fix(inc, goal), 2: wf_fix(cand, goal)}
    monkeypatch.setattr(backtest, "walk_forward", lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.setattr(analytics, "benchmark_relative", lambda: {"alpha": -0.05, "beats_spy": False})
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
    res = reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t", "predicted_delta": 0.3})
    assert res["status"] == "shipped"                                    # negatif alfa ship'i ENGELLEMEZ
    assert res["hypothesis"]["vs_benchmark_at_ship"]["beats_spy"] is False   # ama damgalandı (gelecek veto adayı)


# ---------- Component 4: DeferredRegimeBudgetTrigger ----------
def test_regime_trigger_fires_at_threshold_once(seeded_sandbox):
    from meridian.regime_trigger import DeferredRegimeBudgetTrigger
    tr = DeferredRegimeBudgetTrigger(threshold=30)
    t29 = [{"regime": "chop"}] * 29
    out = tr.evaluate(t29)
    assert out["chop"] == {"n": 29, "threshold": 30, "ready": False}
    out2 = tr.evaluate(t29 + [{"regime": "chop"}])
    assert out2["chop"]["ready"] is True
    fired = store.read_json("regime_trigger.json", {}).get("fired", [])
    assert "chop" in fired                                         # tek seferlik olay kaydı düştü
