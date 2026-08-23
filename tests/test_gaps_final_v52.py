"""test_gaps_final_v52.py — KALAN 41 boşluk (2026-07-21, boşluk kapatma turu 6 — son).

Bu dosya kuyruğun kuyruğu: bileşen başına 1-2 hücre. Sorular aynı üç başlıkta toplanıyor:
  ÜRETKENLİK — modül gerçekten bir çıktı/etki üretiyor mu, yoksa yalnız import mu ediliyor?
  DETERMİNİZM — aynı girdi aynı sonucu mu veriyor (kapı iki tarafı kıyaslıyor)?
  TUTARLILIK — türev kaynağından taze mi / iki yüzey aynı şeyi mi söylüyor?
  SAHİPLİK — modül SAHİBİ OLMADIĞI dosyaya yazıyor mu?
"""
from __future__ import annotations

import ast
import datetime as dt
import inspect
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


# ---------- DETERMİNİZM ----------
def test_alpaca_request_bodies_are_deterministic(monkeypatch):
    """Bizim taraf deterministik: aynı plan → aynı emir gövdesi (broker'ın fill'i bizim işimiz değil)."""
    import httpx
    from meridian.adapters import alpaca
    bodies = []
    monkeypatch.setattr(alpaca, "asset_tradable", lambda s: True)
    monkeypatch.setattr(httpx, "post", lambda u, headers=None, json=None, timeout=None:
                        bodies.append(json) or type("R", (), {"status_code": 200,
                                                              "json": lambda self: {}})())
    plan = {"id": "P-1", "ticker": "KO", "entry_trigger": 61.234, "stop": 58.7,
            "profit_target": 70.1, "size_r": 1.0}
    alpaca.submit_plan(dict(plan), equity=100_000)
    alpaca.submit_plan(dict(plan), equity=100_000)
    assert bodies[0] == bodies[1]


def test_constituents_as_of_is_deterministic(sandbox_state):
    from meridian.adapters import constituents as con
    base = [f"S{i:03d}" for i in range(460)]
    store.write_json(con.CACHE, {"as_of": dt.date.today().isoformat(), "current": base + ["NEW"],
                                 "changes": [{"date": "2026-10-01", "added": "NEW", "removed": "OLD"}]})
    assert con.as_of("2025-01-01") == con.as_of("2025-01-01")


def test_macro_snapshot_determinizmi_kaynagina_tasindi():
    """DEVİR (2026-07-30 temizlik turu): `macro.snapshot` EMEKLİ edildi (üretim tüketicisi yoktu;
    çağıran taraması + geri-al notu `meridian/adapters/macro.py` mezar taşında).

    Determinizm SORUSU ölmedi, SAHİBİ değişti: `snapshot` zaten `regime.classify`ı sarmalıyordu ve
    canlı rejim yolu ONU doğrudan çağırıyor. Yani çivi artık sarmalayıcıda değil, kaynağın
    kendisinde: aynı barlar → aynı sınıflama + aynı metrikler. Sarmalayıcının determinizmini test
    etmek, ölçtüğü şeyi ikinci kez ölçmekti."""
    from meridian import regime
    from tests.conftest import make_bars
    bars = make_bars(300, seed=9, trend=0.001)
    assert regime.classify(bars) == regime.classify(bars)
    assert regime.distribution_days(bars) == regime.distribution_days(bars)


def test_config_resolve_params_is_pure(seeded):
    base = {"a": 1.0, "b": 2.0}
    by = {"chop": {"a": 9.0}}
    first = config.resolve_params(base, by, "chop")
    second = config.resolve_params(base, by, "chop")
    assert first == second and base == {"a": 1.0, "b": 2.0}      # girdi MUTASYONA uğramadı


def test_guard_verdict_is_deterministic(seeded):
    from meridian import guard
    plan = {"ticker": "AAA", "sector": "tech", "size_r": 1.0, "r_multiple_expected": 2.5, "score": 70}
    port = {"open_positions": 1, "sector_counts": {"tech": 1}, "day_pnl_pct": -0.01, "open_risk_r": 1.0}
    reg = {"exposure_budget_pct": 60, "leading_sectors": [{"sector": "tech"}]}
    a = guard.classify_gate(plan, port, reg, config.goal())
    b = guard.classify_gate(plan, port, reg, config.goal())
    assert a == b


def test_mcp_tools_are_deterministic(sandbox_state):
    from meridian import mcp_server as mcp
    store.write_json("regime.json", {"date": "2026-07-20", "regime": "chop", "exposure_budget_pct": 40})
    call = lambda: mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "meridian_regime", "arguments": {}}})
    assert call() == call()


def test_oos_split_is_deterministic():
    from meridian.oos_pipeline import split_date
    assert split_date("2024-07-01", "2025-12-31") == split_date("2024-07-01", "2025-12-31")


def test_regime_classification_is_deterministic():
    from meridian import regime as rg
    from tests.conftest import make_bars
    bars = make_bars(300, seed=12, trend=0.0008)
    assert rg.classify(bars) == rg.classify(bars)
    assert rg.build_regime_json(bars, {"regime.min_exposure_score": 40}, "2026-07-20") == \
        rg.build_regime_json(bars, {"regime.min_exposure_score": 40}, "2026-07-20")


def test_validation_report_is_deterministic(sandbox_state):
    from meridian import validation_report as vr
    assert vr.build() == vr.build()


# ---------- ÜRETKENLİK ----------
def test_hermes_evidence_pack_is_non_empty_and_sourced(sandbox_state):
    """Boş state'te BOŞ dönmesi dürüsttür (uydurma kanıt yok); kanıt VARSA taşımalı."""
    from meridian import hermes
    assert hermes.evidence_pack() == ""                       # kanıt yok → sessiz, uydurma yok
    store.write_json("regime_edge.json", {"trend_up": {"n": 99, "avg_r": 0.42}})
    store.write_json("score_calibration.json", {"rank_ic": 0.21, "n": 80})
    pack = hermes.evidence_pack()
    assert isinstance(pack, str) and len(pack) > 20, "kanıt var ama pakete girmiyor"


def test_mcp_server_exposes_its_tools(sandbox_state):
    from meridian import mcp_server as mcp
    r = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert len(r["result"]["tools"]) == len(mcp.TOOLS) >= 5


def test_mirror_stream_state_machine_produces_a_snapshot(sandbox_state):
    from meridian import mirror_stream as ms
    ms.MACHINE = None
    sm = ms.MirrorOrderStateMachine()
    sm.apply("new", {"client_order_id": "P-1", "symbol": "AAA", "status": "new", "filled_qty": "0"})
    st = store.read_json(ms.STATE_FILE, {})
    assert st.get("orders", {}).get("P-1", {}).get("symbol") == "AAA"
    assert st.get("updated")


def test_notify_reports_delivery_outcome(sandbox_state, monkeypatch):
    from meridian import notify
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: {"MERIDIAN_WEBHOOK_URL": "http://x"}.get(n))
    monkeypatch.setattr(notify, "_post", lambda *a, **k: True)
    assert notify.send("mesaj") is True                          # ÜRETİM = teslimat sonucu döner


def test_obs_every_call_emits_a_persisted_event(sandbox_state):
    from meridian import obs
    n0 = len(store.read_jsonl("events.jsonl"))
    obs.log("x_event", a=1); obs.warn("y_event"); obs.alarm(obs.ALARM_DATA_QUALITY, "z")
    rows = store.read_jsonl("events.jsonl")
    assert len(rows) == n0 + 3 and {r["level"] for r in rows[-3:]} == {"info", "warn", "alarm"}


def test_regime_trigger_produces_a_state_file(sandbox_state):
    from meridian.regime_trigger import DeferredRegimeBudgetTrigger, THRESHOLD_N, STATE_FILE
    out = DeferredRegimeBudgetTrigger().evaluate([{"regime": "chop"}] * (THRESHOLD_N + 1))
    assert out["chop"]["ready"] is True
    assert store.read_json(STATE_FILE, {}).get("fired") == ["chop"]


def test_run_bootstrap_produces_v01(seeded):
    from meridian import run
    strat = run.bootstrap_v01()
    assert strat["version"] == 1 and (config.STATE / "strategy.yaml").exists()


def test_skill_evolve_lists_candidates_or_says_none(sandbox_state):
    from meridian import skill_evolve as se
    assert isinstance(se.weak_skills(), list)                    # veri yoksa BOŞ liste, hata değil
    assert isinstance(se.pending_drafts(), list)


def test_skills_pipeline_run_emits_a_row(sandbox_state):
    from meridian import skills as sk
    store.write_json(sk.REGISTRY, {"skills": {"vcp-screener": {"enabled": True, "mode": "active",
                                                               "pipeline": "P2_SCREEN"}}})
    with sk.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
        pass
    assert store.read_jsonl(sk.RUNS)[-1]["pipeline"] == "P2_SCREEN"


def test_spend_ledger_row_is_written(sandbox_state):
    from meridian import spend
    spend.record(1000, 500, "claude-opus-4-8", note="t")
    assert len(store.read_jsonl("spend.jsonl")) == 1


def test_sprint_status_is_readable_even_when_never_run(sandbox_state):
    from meridian import sprint
    st = sprint.status()
    assert isinstance(st, dict) and st.get("active") is False


def test_sprint_run_declares_its_phases():
    from meridian import sprint_run
    src = inspect.getsource(sprint_run)
    assert "phase" in src and "eval" in src.lower()


def test_strategy_scan_produces_a_scored_signal_or_an_honest_none():
    """ÜRETKENLİK: tarama ya PUANLI bir sinyal üretir ya da dürüstçe None — 'belki' yok."""
    from meridian import strategy
    from tests.conftest import make_bars
    params = config.default_strategy()["params"]
    bars = make_bars(320, seed=2, breakout_at=300)
    sig = strategy.scan_entry(bars, params, 90, ticker="AAA")
    if sig is not None:
        assert 0 <= sig.score <= 100 and sig.entry_trigger > sig.stop and sig.setup
    # scan_all HER ekranı koşturur ve {setup: sinyal} döner; hiçbiri tetiklemezse BOŞ dict dürüsttür
    det = strategy.scan_all(bars, params, 90, ticker="AAA")
    assert isinstance(det, dict)
    for setup, sg in det.items():
        assert sg.setup == setup and sg.entry_trigger > sg.stop


# ---------- TUTARLILIK ----------
def test_api_diagnostics_reflects_current_state(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    store.write_json("regime.json", {"date": "2026-07-20", "regime": "chop"})
    d = TestClient(api.app).get("/api/diagnostics").json()
    assert d["coverage"]["cells_applicable"] > 0
    assert "integrity" in d and "universe_drift" in d


def test_earnings_cache_follows_the_file(sandbox_state):
    from meridian import earnings
    fut = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    (sandbox_state / "earnings.csv").write_text(f"ticker,date\nAAA,{fut}\n")
    earnings.clear_cache()
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is True
    (sandbox_state / "earnings.csv").write_text("ticker,date\n")
    earnings.clear_cache()
    assert earnings.in_blackout("AAA", dt.date.today().isoformat()) is False


def test_hermes_evidence_pack_reflects_the_ledgers(sandbox_state):
    from meridian import hermes
    before = hermes.evidence_pack()
    store.write_json("regime_edge.json", {"trend_up": {"n": 99, "avg_r": 0.42}})
    after = hermes.evidence_pack()
    assert after != before, "kanıt paketi defter değişince TAZELENMİYOR"


def test_mirror_pending_view_matches_the_file(sandbox_state):
    from meridian import mirror_stream as ms
    ms.MACHINE = None
    sm = ms.MirrorOrderStateMachine()
    sm.apply("new", {"client_order_id": "P-1", "symbol": "AAA", "status": "new", "filled_qty": "0"})
    assert sm.pending_symbols() == ms.pending_symbols_snapshot()   # süreç-içi ve süreç-dışı AYNI


def test_probgate_meta_reads_the_live_calibration_file(sandbox_state):
    from meridian.probgate import PairedProbabilisticGate as G, META_FILE, P_BASE
    store.write_json(META_FILE, {"extra_p": 0.05})
    assert G.p_required_for(1) == pytest.approx(min(0.95, P_BASE + 0.05))
    store.write_json(META_FILE, {"extra_p": 0.0})
    assert G.p_required_for(1) == pytest.approx(P_BASE)


def test_score_targets_come_from_the_goal(seeded):
    from meridian import score as sc
    goal = config.goal()
    d = sc.score_detail([{"r_multiple": 0.5, "pnl_dollars": 500, "ts_open": "2026-01-01",
                          "ts_close": "2026-01-05"}] * 40, goal, span_days=90)
    assert d["targets"]["target_return_30d"] == goal["target_return_30d"]
    assert d["targets"]["max_drawdown"] == goal["max_drawdown"]


def test_secrets_status_matches_the_store(sandbox_state, monkeypatch):
    from meridian import secrets
    for n in list(secrets.ALLOWED):
        monkeypatch.delenv(n, raising=False)
    secrets.clear_cache()
    secrets.set("FMP_API_KEY", "abcdefghijkl")
    st = secrets.status()["FMP_API_KEY"]
    assert st["set"] is True and st["hint"] == "••••ijkl"
    secrets.delete("FMP_API_KEY")
    assert secrets.status()["FMP_API_KEY"]["set"] is False


def test_skills_enablement_follows_key_presence(sandbox_state, monkeypatch):
    from meridian import skills as sk
    from meridian.adapters import fmp
    store.write_json(sk.REGISTRY, {"skills": {"canslim-screener": {
        "enabled": False, "mode": "disabled", "reason": "FMP_API_KEY yok — Ayarlar'dan ekleyin",
        "fmp": "req", "alpaca": "opt", "style_active": True}}})
    monkeypatch.setattr(fmp, "available", lambda: True)
    sk.reconcile_enablement()
    assert sk.registry()["skills"]["canslim-screener"]["enabled"] is True


def test_strategy_and_backtest_share_one_scan(sandbox_state):
    """TUTARLILIK: kapı ile canlı AYNI tarama fonksiyonunu çağırmalı — iki tarama = iki strateji."""
    from meridian import backtest, loop
    import inspect as _i
    # backtest scan_entry (işlem seçimi), canlı döngü scan_all (cf defteri uyuyanları da görsün)
    # — İKİSİ DE strategy.py'nin AYNI değerlendiricilerini çağırır; ikinci bir tarama kopyası yok.
    assert "scan_entry" in _i.getsource(backtest.replay)
    assert "scan_all" in _i.getsource(loop.daily_cycle)
    src = pathlib.Path("meridian/strategy.py").read_text()
    assert "def scan_entry" in src and "def scan_all" in src
    assert "evaluate_entry" in _i.getsource(strategy_scan_sources()), "tarama tek yerde tanımlı olmalı"


def strategy_scan_sources():
    from meridian import strategy
    return strategy.scan_all


def test_watchdog_reports_are_derived_from_live_state(sandbox_state):
    from meridian import watchdog
    watchdog.beat("scheduler_poll")
    rep = watchdog.report()
    assert rep["n_ok"] >= 1 and "scheduler_poll" not in rep["never"]   # F8/T3.1: sayaç `n_ok` (A4)


def test_watchdog_conservation_counts_every_plan(sandbox_state):
    """KORUNUM: her plan ya işleme dönüşmüş, ya NO_GO, ya olayla düşmüş sayılır — kalan 'unexplained'."""
    from meridian import watchdog
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P1", "date": "2026-07-20", "ticker": "AAA", "gate_verdict": "GO"},
        {"id": "P2", "date": "2026-07-20", "ticker": "BBB", "gate_verdict": "NO_GO"}])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P1", "r_multiple": 1.0}])
    rep = watchdog.conservation_report()
    assert rep["plans"] == 2 and rep["unexplained"] == 0


# ---------- SAHİPLİK ----------
def test_constituents_writes_only_its_cache():
    assert _writes("meridian/adapters/constituents.py") <= {"sp500_constituents.json"}


def test_config_never_writes_state_files():
    """config OKUR; tek yazımı dump_yaml (çağıranın verdiği yola) — kendi başına state dosyası yazmaz."""
    assert _writes("meridian/config.py") == set()


def test_earnings_writes_only_its_csv():
    src = pathlib.Path("meridian/earnings.py").read_text()
    assert _writes("meridian/earnings.py") == set()               # store yazımı yok
    assert 'STATE / "earnings.csv"' in src and src.count("os.replace") >= 1   # atomik, tek dosya


def test_store_is_the_only_writer_of_the_state_dir():
    """SAHİPLİK: state/ yazımı store'un atomik yollarından geçmeli; modüller ham open(...,'w')
    kullanmamalı (yarım dosya + kayıp güncelleme riski).

    `auth.py` İSTİSNASI (2026-07-29) — KARAR ve ÖLÇÜM: sır dosyası store'un GENEL yoluna sokulmaz.
      1) store 0600'ü GARANTİ ETMEZ, tesadüfen üretir. `write_json` geçici dosyayı
         `tempfile.mkstemp` ile açar; 0600 o yardımcının varsayılanıdır — hiçbir yerde
         belgelenmemiş, hiçbir testte çivilenmemiş bir yan etkidir (ölçüldü: bugün 0600 çıkıyor).
         Yarın store başka bir geçici-dosya mekanizmasına geçse parola hash'i ve imza anahtarı
         SESSİZCE 0644'e düşerdi. Sır dosyası iznini MİRAS ALMAZ, kendisi DAYATIR: `auth._write`
         geçici dosyayı açıkça 0600 açar ve `os.replace` sonrası bir kez daha chmod'lar.
      2) store'un OKUMA yolu köken kaydediciden geçer: `read_json` sonucu `provenance.sar`a sarar
         ve o da (MERIDIAN_PROVENANCE=1 iken) artefaktın ALAN ADLARINI ve şeklini depoya işlenen
         `provenance_report.json`a yazar. Değerler yazılmaz — ama bir kimlik kaydının genel amaçlı
         bir iç-gözlem katmanından geçmesi için hiçbir sebep yok.
      3) TUTARLILIK: kardeş sır deposu `secrets.py` ZATEN bu listede ve tam olarak bu sebeple
         kendi `_path()`/`_write_file()`/chmod yoluna sahip. auth.py'yi ondan farklı bir zemine
         koymak, listeyi tutarsız yapardı.
      4) Testin ÖLÇTÜĞÜ risk burada YOK: "yarım dosya + kayıp güncelleme". `auth._write` atomiktir
         (0600 geçici dosya + `os.replace`), yani listenin kendi tarifine — "bilinçli istisnalar
         (atomik kendi yolları)" — birebir uyar.
      5) BEKÇİ KÖRLEŞMİYOR: conftest'in canlı-yazım kancası `os.replace`i sarar ve `auth._write`
         oradan geçer; canlı `state/auth.json`a yazan bir test hâlâ ADIYLA düşer
         (test_kimlik_v114::test_auth_yazimi_canli_state_bekcisine_GORUNUR bunu çivileniyor).
    """
    offenders = []
    for f in pathlib.Path("meridian").rglob("*.py"):
        if f.name in ("store.py", "config.py", "secrets.py", "sprint.py", "sprint_run.py",
                      "earnings.py", "skill_evolve.py", "hermes.py",
                      "api.py",        # debug-export zip'i + statik dosya servisi
                      "auth.py",       # sır dosyası: 0600'ü store'dan MİRAS ALMAZ, kendi dayatır
                      "reflect.py"):   # fcntl kilit dosyası (.reflect.lock) — içerik değil, kilit
            continue                                             # bilinçli istisnalar (atomik kendi yolları)
        src = f.read_text()
        if 'open(' in src and '"w"' in src and "STATE" in src:
            offenders.append(f.name)
    assert not offenders, f"state/ dizinine ham yazım: {offenders}"


# ---------- dürüstlük kontrolü: yukarıda ZAYIF kalan hücreler için gerçek testler ----------
def test_regime_trigger_fired_set_only_grows(sandbox_state):
    """MONOTONLUK: bir kez 'hazır' ilan edilen rejim listeden DÜŞMEZ — yoksa aynı eşik defalarca
    kutlanır ve sinyal anlamını yitirir."""
    from meridian.regime_trigger import DeferredRegimeBudgetTrigger as T, THRESHOLD_N, STATE_FILE
    t = T()
    t.evaluate([{"regime": "chop"}] * (THRESHOLD_N + 1))
    assert store.read_json(STATE_FILE, {})["fired"] == ["chop"]
    t.evaluate([{"regime": "chop"}] * 2)                        # kanıt azaldı
    assert store.read_json(STATE_FILE, {})["fired"] == ["chop"], "ateşlenmiş rejim listeden düştü"
    t.evaluate([{"regime": "chop"}] * (THRESHOLD_N + 1) + [{"regime": "high_vol"}] * (THRESHOLD_N + 1))
    assert store.read_json(STATE_FILE, {})["fired"] == ["chop", "high_vol"]


def test_spend_month_total_only_grows_within_a_month(sandbox_state):
    """MONOTONLUK: ay içindeki harcama toplamı geri gitmez (defter append-only)."""
    from meridian import spend
    totals = []
    for _ in range(3):
        spend.record(100_000, 0, "claude-opus-4-8")
        totals.append(spend.month_spend())
    assert totals == sorted(totals) and totals[0] < totals[-1]


def test_sprint_conserves_the_live_book(sandbox_state, tmp_path):
    """KORUNUM: sprint kum havuzunu sıfırlarken CANLI defterdeki hiçbir satır kaybolmaz."""
    from meridian import sprint
    store.write_jsonl("trades.jsonl", [{"id": "T1"}, {"id": "T2"}])
    before = store.read_jsonl("trades.jsonl")
    sb = tmp_path / "sbstate"; sb.mkdir()
    sprint._reset_sandbox_state(sb)
    assert store.read_jsonl("trades.jsonl") == before
    assert (sb / "trades.jsonl").read_text() == ""


def test_watchdog_derived_sources_cover_every_calibration(sandbox_state):
    """TUTARLILIK: her kalibrasyon artefaktının bir KAYNAĞI beyan edilmeli; beyan edilmeyen türev
    bayatladığında kimse görmez."""
    from meridian import watchdog
    produced = {"score_calibration.json", "near_miss.json", "cf_fidelity.json",
                "exit_efficiency.json", "llm_calibration.json", "shadow_model.json",
                "regime_edge.json", "arming_report.json", "self_review.json"}
    missing = produced - set(watchdog.DERIVED_SOURCES)
    assert not missing, f"kaynağı beyan edilmemiş türev: {missing}"


def test_skill_evolve_draft_produces_a_file_and_a_record(sandbox_state, monkeypatch, tmp_path):
    """ÜRETKENLİK: taslak GERÇEKTEN bir dosya + kayıt üretir (yoksa 'revizyon döngüsü' bir iddiadır)."""
    from meridian import skill_evolve as se, hermes
    skill_dir = tmp_path / "skills" / "vcp-screener"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# eski\n" + "x" * 300)
    monkeypatch.setattr(se, "_repo_skill_dir", lambda n: str(skill_dir))
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: "<REVISED>\n# yeni\n" + "y" * 300 + "\n</REVISED>\nRATIONALE: test")
    rec = se.draft_revision("vcp-screener")
    assert rec and (skill_dir / "SKILL.md.v2-draft").exists()
    assert store.read_json(se.REVISIONS_FILE, [])[-1]["status"] == "draft"


def test_sprint_run_produces_a_labeled_training_point():
    """ÜRETKENLİK: sprint sonucu AÇIKÇA 'eğitim' etiketli bir kalibrasyon noktasıdır (canlıya karışmaz)."""
    import inspect as _i
    from meridian import sprint_run
    src = _i.getsource(sprint_run)
    # sprint'in ÜRETTİĞİ şey: sızıntısız bir realized_delta + kalibrasyon isabeti (eğitim noktası)
    assert "realized_delta" in src and "calibration_hit" in src
    assert "EVAL_START" in src, "ölçüm penceresi belirtilmemiş — 'sızıntısız' iddiası dayanaksız kalır"
