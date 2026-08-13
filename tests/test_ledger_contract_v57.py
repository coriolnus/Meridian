"""test_ledger_contract_v57.py — DEFTER SÖZLEŞMESİ (2026-07-21).

Bugün çıkan yedi hatanın altısı aynı kökten geliyordu: her defteri 2-3 modül yazıyor, 5-8 modül
okuyor, arada yazılı anlaşma yok. Hiçbiri istisna fırlatmadı — `.get()` None döndü, satır atlandı,
sayı küçüldü, kimse fark etmedi. 800 testin hiçbiri yakalamadı çünkü testler KENDİ fixture'larını
üretiyor; gerçek defterle konuşmuyorlar.

Bu dosya sözleşmeyi üç yerden bağlar:
  1. ÜRETİCİ testi   — modül GERÇEK bir satır üretir, sözleşmeye uyuyor mu? (fixture değil, üretim)
  2. STATİK tarama   — beyan edilmemiş bir yazar belirdi mi? (ikinci kopya sınıfı)
  3. TEK KAYNAK      — şema iki yerde tanımlı olmasın (aynı hatanın kendisi)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, ledgers, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# ---------- 1) ÜRETİCİLER sözleşmeye uyuyor mu (gerçek satır üreterek) ----------
def test_broker_trade_row_satisfies_the_contract():
    """En kritik defter: bir alan eksik olursa skor kalibrasyonu ve gölge model o satırı SESSİZCE
    eler. Canlıda tam bu oldu (`score`/`setup` yoktu → 'gerçek 0 / simüle 241')."""
    from meridian.broker import PaperBroker
    b = PaperBroker(equity=100_000, slippage_bps=5, commission_per_share=0.005)
    plan = {"id": "P-2026-01-02-AAA", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
            "profit_target": 115.0, "size_r": 1.0, "setup": "breakout_vcp", "score": 71,
            "regime_at_plan": "chop", "r_multiple_expected": 3.0, "strategy_version": 1}
    b.fill_entry(plan, 100.0, "2026-01-02", 100_000)
    row = b.close_position("AAA", 110.0, "target", "2026-01-09")
    assert ledgers.validate_row("trades.jsonl", row) == []


def test_backtest_plan_row_satisfies_the_contract():
    from meridian import backtest
    from tests.conftest import make_bars
    idx = make_bars(400, seed=1, trend=0.0012)
    bars = {f"T{i}": make_bars(400, seed=10 + i, breakout_at=300 + i * 5) for i in range(8)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-12-01", strategy_version=1)
    assert res.plan_log, "plan üretilmedi — test bir şey kanıtlamıyor"
    for p in res.plan_log:
        assert ledgers.validate_row("trade_plans.jsonl", p) == [], p
    for t in res.trades:
        assert ledgers.validate_row("trades.jsonl", t) == [], t


def test_counterfactual_row_satisfies_the_contract(seeded):
    from meridian import counterfactual as cf
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    plan = {"id": "P-2026-07-20-AAA", "ticker": "AAA", "setup": "breakout_vcp", "score": 71,
            "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0,
            "r_multiple_expected": 3.0, "regime_at_plan": "chop", "gate_verdict": "GO"}
    cf.collect("2026-07-20", [plan], {"P-2026-07-20-AAA"}, [], 15, regime="chop")
    for row in store.read_json(cf.OPEN_FILE, []):
        assert ledgers.validate_row("counterfactuals.jsonl", row) == [], row


def test_memory_hypothesis_row_satisfies_the_contract(seeded):
    from meridian import memory
    row = memory.record({"variable": "entry.min_score", "new": 65, "status": "proposed"})
    assert ledgers.validate_row("hypotheses.jsonl", row) == []


def test_obs_event_row_satisfies_the_contract(seeded):
    from meridian import obs
    assert ledgers.validate_row("events.jsonl", obs.log("x", a=1)) == []
    assert ledgers.validate_row("events.jsonl", obs.warn("y")) == []


def test_spend_row_satisfies_the_contract(seeded):
    from meridian import spend
    assert ledgers.validate_row("spend.jsonl", spend.record(10, 5, "claude-opus-4-8")) == []


def test_pipeline_run_row_satisfies_the_contract(seeded):
    from meridian import skills as sk
    store.write_json(sk.REGISTRY, {"skills": {"vcp-screener": {"enabled": True, "mode": "active",
                                                               "pipeline": "P2_SCREEN"}}})
    with sk.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
        pass
    assert ledgers.validate_row("pipeline_runs.jsonl", store.read_jsonl(sk.RUNS)[-1]) == []


# ---------- 2) YAZAR sınırı ----------
def test_no_undeclared_writer_appears():
    """Guard'ın ikinci risk zarfı, mirror_stream'in ikinci iptal kopyası — hepsi 'kimsenin haberi
    olmadan ikinci bir yazar' sınıfındandı. Yeni bir yazar belirirse burada tartışılır."""
    v = ledgers.writer_violations()
    assert not v, f"sözleşme dışı yazar/eksik beyan: {v}"


def test_every_contract_declares_at_least_one_writer():
    for name, c in ledgers.CONTRACTS.items():
        assert c.writers, f"{name}: yazarı beyan edilmemiş"
        assert c.required, f"{name}: zorunlu alanı yok — sözleşme boş olamaz"


# ---------- 3) TEK KAYNAK ----------
def test_schema_is_defined_only_in_the_contract():
    """Şemayı iki yerde tanımlamak, bu denetimin bulduğu hatanın ta kendisidir."""
    import pathlib as _p
    wd = _p.Path("meridian/watchdog.py").read_text()
    assert "LEDGER_REQUIRED_FIELDS = {" not in wd, "şema watchdog'da YENİDEN tanımlanmış"
    assert "ledgers" in wd and "validate_live" in wd


def test_detector_reads_the_contract(sandbox_state):
    from meridian import watchdog as wd
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P{i:05d}", "r_multiple": 0.4}
                                       for i in range(10)])
    row = next(r for r in wd.parity_report()["rows"] if r["check"] == "ledger_contract:trades")
    assert row["ok"] is False
    assert "eksik alan" in str(row["detail"]) and "anahtar biçimi" in str(row["detail"])


def test_compliant_ledger_is_quiet(sandbox_state):
    from meridian import watchdog as wd
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i}", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAA",
         "r_multiple": 0.4, "pnl_dollars": 400, "plan_id": f"P-2026-01-{i+1:02d}-AAA",
         "regime": "chop", "score": 70, "setup": "breakout_vcp", "strategy_version": 1}
        for i in range(10)])
    row = next(r for r in wd.parity_report()["rows"] if r["check"] == "ledger_contract:trades")
    assert row["ok"] is True


# ---------- anahtar biçimi: üç motor TEK anahtar üretir ----------
def test_all_three_engines_produce_the_same_key_format():
    import inspect
    from meridian import backtest, loop, cf_backfill
    assert ledgers.PLAN_ID_RE.match("P-2026-07-20-NVDA")
    assert not ledgers.PLAN_ID_RE.match("P00140")            # eski backtest şeması REDDEDİLİR
    assert 'f"P-{d.date()}-{sig.ticker}"' in inspect.getsource(backtest.replay)
    assert 'f"P-{dstr}-' in inspect.getsource(loop.daily_cycle)
    assert 'f"P-{dstr}-' in inspect.getsource(cf_backfill)


# ---------- 4) KANIT TÜKETİLİYOR MU (bu denetimin baskın hata sınıfı) ----------
def test_contract_report_is_served_and_consumed(seeded):
    """Sözleşmeyi üretip kimsenin okumaması, tam da bu denetimin bulduğu hata sınıfıdır
    (yedi dedektör rapor üretiyordu, hiçbir panel okumuyordu). Uç → pano zincirini bağla."""
    import pathlib as _p
    api_src = _p.Path("meridian/api.py").read_text()
    assert "ledger_contract" in api_src, "sözleşme /api/diagnostics'te sunulmuyor"
    js = _p.Path("meridian/web/app.js").read_text()
    assert "d.ledger_contract" in js, "pano sözleşmeyi OKUMUYOR — üretilip tüketilmeyen kanıt"
    assert "d.integrity" in js, "bütünlük dedektörleri raporu panoda okunmuyor"
    # 8. DESEN BEYANLI EKLENDİ (2026-08-13): `divergence` panoda da bir satır almalı — arka uç
    # ilerleyip pano geride kalırsa dedektör üretilir ama TÜKETİLMEZ (YASA 6).
    for key in ("production", "conservation", "determinism", "coherence",
                "monotonicity", "ownership", "parity", "divergence"):
        assert key in js, f"{key} deseni panoda gösterilmiyor"


def test_diagnostics_endpoint_carries_the_contract(seeded):
    from fastapi.testclient import TestClient
    from meridian import api
    r = TestClient(api.app).get("/api/diagnostics", headers=_auth_headers())
    assert r.status_code == 200, r.text
    lc = r.json()["ledger_contract"]
    assert lc["ledgers"] == len(ledgers.CONTRACTS) and "detail" in lc


def _auth_headers() -> dict:
    """UYGULAMANIN GERÇEK TOKEN SÖZLEŞMESİ (K1 düzeltmesi, 2026-07-30).

    ESKİ HÂL İKİ KAT YANLIŞTI: `MERIDIAN_API_TOKEN` adlı bir değişken okunuyordu — o ad repo'da
    başka HİÇBİR yerde üretilmiyor/set edilmiyor — ve `Authorization: Bearer` başlığı
    gönderiliyordu. Uygulama ise `MERIDIAN_DASH_TOKEN` + `x-meridian-token` bekliyor (api._auth).
    Yani yardımcı HİÇBİR ZAMAN geçerli kimlik üretemiyordu; testler yalnız token'ın HİÇ kurulu
    olmadığı ortamda geçiyordu (api._auth'un `if not DASH_TOKEN: return` no-op dalı). Token'lı bir
    CI ortamında bu testler sessizce 401 alıp anlamsızlaşırdı — "yetkiyle geçti" sanılan bir yeşil.

    `api.DASH_TOKEN` doğrudan okunur: modül token'ı süreç açılışında environ'dan alıyor, dolayısıyla
    tek gerçek kaynak odur (ortam değişkenini testin görmesi garanti değil)."""
    from meridian import api
    tok = getattr(api, "DASH_TOKEN", None)
    return {"x-meridian-token": tok} if tok else {}


def test_alias_declarations_are_honoured(seeded):
    """cf sözleşmesi kanonik adı beyan ediyor: satır ikisini de taşımalı (eski ad geriye dönük)."""
    from meridian import counterfactual as cf
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    canonical, legacy = ledgers.CONTRACTS["counterfactuals.jsonl"].aliases[0]
    plan = {"id": "P-2026-07-20-AAA", "ticker": "AAA", "setup": "breakout_vcp", "score": 71,
            "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0,
            "r_multiple_expected": 3.0, "regime_at_plan": "chop", "gate_verdict": "GO"}
    cf.collect("2026-07-20", [plan], set(), [], 15, regime="chop")
    row = store.read_json(cf.OPEN_FILE, [])[0]
    assert row[canonical] == row[legacy] == 3.0
