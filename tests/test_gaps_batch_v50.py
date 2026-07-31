"""test_gaps_batch_v50.py — arming + cf_backfill + hermes_runtime + memory + rollback boşlukları
(2026-07-21, boşluk kapatma turu 4). Her biri 3 açık hücreyle kuyruğun başındaydı.

Ortak soru: bu mekanizmalar ÜRETİYOR mu (uretkenlik), aynı girdiyle aynı sonucu mu veriyor
(determinizm), türevleri kaynaklarından taze mi (tutarlilik), ve SAHİBİ OLMADIKLARI dosyalara
dokunuyorlar mı (sahiplik)?
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

from meridian import config, memory, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


_ARTGRAPH_CACHE: dict | None = None


def _writes(module_file: str) -> set:
    """Modülün YAZDIĞI state dosyalarının adları — sahiplik sınırının ölçüsü.

    ÜRETİM TARAYICISINA KÖPRÜ (2026-07-23, tarama bulgusu). Eski elle-AST yalnız dört fonksiyon adını
    ve YALNIZ sabit (ast.Constant) ilk argümanı sayıyordu; codelaw.WRITE_CALLS'te olan `update_json`/
    `update_jsonl` ile MODÜL SABİTİ argümanları (ör. rollback.py `store.update_json(OPEN_LOOP_FILE,...)`)
    tamamen kaçıyordu. Sonuç: `_writes(rollback) == set()` YEŞİL geçiyordu ama rollback aslında
    learning_loop_open.json yazıyor — test kendi zayıf kopyasını doğruluyordu. Artık codelaw.artifact_graph
    (WRITE_CALLS + modül/global sabit çözümü + f-string 'unresolved' muhasebesi) tek kaynak."""
    global _ARTGRAPH_CACHE
    if _ARTGRAPH_CACHE is None:
        from meridian import codelaw
        _ARTGRAPH_CACHE = codelaw.artifact_graph()
    modname = pathlib.Path(module_file).name
    arts = _ARTGRAPH_CACHE.get("artifacts", _ARTGRAPH_CACHE)
    return {art for art, rec in arts.items() if modname in rec.get("writers", ())}


# ================= arming (uretkenlik, determinizm, tutarlilik) =================
def test_arming_always_produces_a_report(seeded, monkeypatch):
    from meridian import arming
    monkeypatch.setattr(arming, "setup_report", lambda: {})
    out = arming.evaluate(bars={}, index=None)
    assert store.read_json(arming.REPORT_FILE, {}) == out          # rapor DİSKE düştü
    assert out["measurements"], "hiç ölçüm satırı yok — uyuyan kurulumlar görünmez"
    assert out.get("rule"), "eşik kuralı raporda yazılı değil"


def test_arming_report_is_deterministic_for_the_same_evidence(seeded, monkeypatch):
    from meridian import arming
    rep = {"momentum_burst": {"n": 5, "avg_r": -0.2, "win_rate": 0.3, "regimes": {}}}
    monkeypatch.setattr(arming, "setup_report", lambda: rep)
    a = arming.evaluate(bars={}, index=None)
    b = arming.evaluate(bars={}, index=None)
    assert a["measurements"] == b["measurements"]


def test_arming_report_is_derived_from_the_cf_ledger(seeded):
    """Türev-kaynak bağı: rapor cf defterinden gelir; watchdog bunu tazelik için izler."""
    from meridian import watchdog
    assert "arming_report.json" in watchdog.DERIVED_SOURCES
    assert "counterfactuals.jsonl" in watchdog.DERIVED_SOURCES["arming_report.json"]


def test_arming_writes_only_its_own_file():
    assert _writes("meridian/arming.py") <= {"arming_report.json"}


# ================= cf_backfill (uretkenlik, determinizm, sahiplik) =================
def test_cf_backfill_writes_only_the_counterfactual_ledger():
    """SIFIR YETKİ: geçmişi yeniden oynatır ama YALNIZ cf defterine yazar — portföy, işlem defteri,
    strateji ve karneye ASLA dokunmaz (yoksa 'kanıt üretmek' kitabı yeniden yazmak olurdu)."""
    w = _writes("meridian/cf_backfill.py")
    assert w <= {"counterfactuals.jsonl"}, f"cf_backfill fazladan dosya yazıyor: {w}"
    src = pathlib.Path("meridian/cf_backfill.py").read_text()
    for forbidden in ("versioning.commit", "dump_yaml", "write_heartbeat", "submit("):
        assert forbidden not in src, f"cf_backfill '{forbidden}' çağırıyor — sıfır-yetki ihlali"


def test_cf_backfill_uses_cached_bars_only():
    """Ağa çıkmaz: dataset.load() corporate-action tazelemesi tetikleyip barları değiştirirdi."""
    src = pathlib.Path("meridian/cf_backfill.py").read_text()
    assert "dataset.load(" not in src and "_cache_path" in src


def test_cf_backfill_is_deterministic_by_construction():
    """Aynı barlar + aynı tarih aralığı → aynı cf satırları: modül canlı fonksiyonların AYNISINI
    çağırır ve rastgelelik kullanmaz."""
    src = pathlib.Path("meridian/cf_backfill.py").read_text()
    assert "random" not in src and "shuffle" not in src
    assert "build_regime_json" in src and "classify_gate" in src   # canlı yasanın kendisi


# ================= hermes_runtime (uretkenlik, korunum, sahiplik) =================
def test_hermes_runtime_persists_its_status(sandbox_state):
    from meridian import hermes_runtime as hr
    hr._persist()
    st = store.read_json(hr.STATUS_FILE, {})
    assert st.get("updated") and "brain" in st, "durum dosyası üretilmiyor — pano kör kalır"


def test_reflection_outcome_is_always_recorded(sandbox_state):
    """Her yansıma bir SONUÇ bırakır: sayaç artar, son durum ve taban güncellenir."""
    from meridian import hermes_runtime as hr
    before = hr._state.get("reflections", 0)
    hr._record({"status": "rejected_by_backtest", "hypothesis": {"variable": "entry.min_score"}})
    assert hr._state["reflections"] == before + 1
    assert hr._state["last_result"] == "rejected_by_backtest"
    assert hr._state["last_variable"] == "entry.min_score"
    assert hr._state["last_reflect_at"] is not None                # sayaç tabanı ilerledi


def test_hermes_runtime_writes_only_its_status_file():
    w = _writes("meridian/hermes_runtime.py")
    assert w <= {"hermes_status.json"}, f"runtime fazladan dosya yazıyor: {w}"


# ================= memory (uretkenlik, tutarlilik, sahiplik) =================
def test_memory_produces_both_the_ledger_and_the_lessons(seeded):
    memory.record({"variable": "entry.min_score", "new": 65, "status": "proposed"})
    assert len(memory.all_hypotheses()) == 1
    text = memory.distill_lessons()
    assert (config.STATE / memory.LESSONS).exists() and "Meridian" in text


def test_lessons_are_regenerated_from_the_current_ledger(seeded):
    """Türev tazeliği: defter değişince dersler DEĞİŞMELİ (bayat ders = tekrar edilen ölü son)."""
    memory.record({"variable": "entry.min_score", "new": 65, "status": "rejected_by_backtest",
                   "predicted_direction": "up", "regime": "chop"})
    first = memory.distill_lessons()
    memory.record({"variable": "exit.trail_atr_mult", "new": 3.5, "status": "rejected_by_backtest",
                   "predicted_direction": "up", "regime": "chop"})
    second = memory.distill_lessons()
    assert "exit.trail_atr_mult" in second and second != first


def test_memory_writes_only_the_ledger_and_lessons():
    w = _writes("meridian/memory.py")
    # hypothesis_id_hwm.json MEŞRU sahiplik (2026-07-23): _writes artık codelaw'a köprülü olduğu için
    # `store.write_json(ID_HWM_FILE, ...)` (Name argümanı, eski AST'nin kaçırdığı) görünür oldu. Kimlik
    # yüksek-su işareti memory'nin kendi sahibidir — defter silinse bile numaralar geri sarmasın diye.
    assert w <= {"hypotheses.jsonl", "hypothesis_id_hwm.json", "lessons.md"}, f"memory fazladan dosya yazıyor: {w}"
    # metin araması değil ÇAĞRI araması: 'strategy.yaml' yorumda ANLATILIYOR olabilir
    called = {n.func.attr for n in ast.walk(ast.parse(pathlib.Path("meridian/memory.py").read_text()))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "dump_yaml" not in called and "commit" not in called, \
        "memory canlı stratejiye yazıyor olabilir — defter tutar, karar vermez"


# ================= rollback (uretkenlik, monotonluk, sahiplik) =================
def test_rollback_produces_an_outcome_record(seeded):
    """Öğrenme döngüsünün KAPANDIĞININ kanıtı: hipoteze realized_delta yazılır."""
    from meridian import rollback, versioning
    n = int(config.goal()["min_sample"])
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    config.dump_yaml(config.default_strategy(), config.HISTORY / "v0001.yaml")
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {**config.default_strategy(), "version": 2, "parent": 1}))
    memory.record({"id": "H1", "version_to": 2, "status": "live", "variable": "entry.min_score",
                   "predicted_delta": 0.05, "backtest": {"incumbent_oos": 0.30}})
    trades = [{"strategy_version": v, "regime": "trend_up", "r_multiple": r, "pnl_dollars": r * 1000,
               "ts_open": f"2026-0{1 + (i % 6)}-{(i % 27) + 1:02d}",
               "ts_close": f"2026-0{1 + (i % 6)}-{(i % 27) + 2:02d}"}
              for v, r in ((2, 0.30), (1, 0.30)) for i in range(n)]
    store.write_jsonl("trades.jsonl", trades)
    out = rollback.evaluate_outcomes()
    assert out is not None
    assert memory.all_hypotheses()[0].get("realized_delta") is not None
    assert versioning.scoreboard()["versions"]["2"].get("live_score") is not None


def test_promotion_is_a_one_way_ratchet(seeded):
    """Terfi geri alınamaz: sonradan gelen piyasa sürüklenmesi 'promoted' satırı bozamaz (audit #21)."""
    store.write_jsonl(memory.HYP, [{"id": "H1", "version_to": 4, "status": "promoted",
                                    "predicted_delta": 0.1, "realized_delta": 0.2}])
    memory.writeback_outcome(4, realized_delta=-5.0, realized_detail={"n": 99})
    row = memory.all_hypotheses()[0]
    assert row["status"] == "promoted" and row["realized_delta"] == 0.2


def test_rollback_writes_only_through_owned_paths():
    """rollback stratejiyi YALNIZ versioning.revert_to ile değiştirir (ham strateji yazımı yok);
    kendi SAHİP OLDUĞU tek state dosyası learning_loop_open.json'dır (açık öğrenme döngüsü kaydı)."""
    w = _writes("meridian/rollback.py")
    # BULGUNUN TA KENDİSİ (2026-07-23): eski `_writes(rollback) == set()` YEŞİL geçiyordu çünkü elle-AST
    # `store.update_json(OPEN_LOOP_FILE, ...)` çağrısını (update_json fonksiyon adı + Name argümanı)
    # kaçırıyordu. Gerçekte rollback learning_loop_open.json yazar — MEŞRU: _open_loop/_close_loop onun
    # sahibidir (öğrenme döngüsü ölçüm yapamadığında sessiz kalmasın diye). Strateji yazımı hâlâ YOK.
    assert w == {"learning_loop_open.json"}, f"rollback beklenmedik dosya yazıyor: {w}"
    src = pathlib.Path("meridian/rollback.py").read_text()
    assert "dump_yaml" not in src and "revert_to" in src
