"""test_reflect_gaps_v47.py — reflect'in AÇIK BOŞLUKLARI (2026-07-21, boşluk kapatma turu 1).

reflect ship YETKİSİNİN ta kendisi ve ilk tam turda yalnız 1/6 deseni doluydu (determinizm, havuz
işçisi düzeltmesinden). Uygulanabilir 6 desenin kalan 5'i burada kapanıyor:

  uretkenlik  — DEĞERLENDİRİLEN her öneri bir hipotez SATIRI üretir (sessiz değerlendirme yok)
  korunum     — her öneri KAYITLI bir terminale ulaşır: guard reddi / kapı reddi / teyit reddi /
                ship / öğrenme-durdu / kilit. Ara bir yol yok.
  tutarlilik  — walk-forward önbelleği BAR REVİZYONUNA bağlı; rev değişince yeniden hesaplanır
                (bayat-bar incumbent'ı bu oturumun en pahalı hatasıydı)
  monotonluk  — ship sürüm numarasını İLERİ taşır; probe önbelleği revizyonu geri sarmaz
  sahiplik    — versioning.commit'i çağıran TEK yer burasıdır (tek ship yetkisi) ve süreçler-arası
                kilit ikinci bir yansımayı dürüstçe reddeder
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, memory, reflect, store
from tests import wf_fixtures as wf


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    config.dump_yaml(config.default_strategy(), config.HISTORY / "v0001.yaml")
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
    yield sandbox_state
    config.reload_config()


def _wf(oos):
    # FİKSTÜR TUZAĞI köprüsü: eski dilimsiz sözlük has_slices=False veriyor, _gate_eval erişilemez
    # LEGACY nokta-marj dalına düşüyordu — yani bu dosya ürünün GERÇEKTE koştuğu olasılıksal + teyit
    # yolunu değil, ölü bir dalı test ediyordu. Merkezi fabrikaya köprü: verilen skalar `oos` hem kapı
    # metriğini sürer hem de Search/Confirm dilimlerinin ortalama-R'sini belirler (yüksek oos → aday
    # gerçekten daha iyi işlemler üretir; düşük oos → daha kötü). Böylece has_slices=True olur ve kapı
    # blok-bootstrap P(ΔS>0) + teyit yürüyüşünü koşar. Skor ayrımı (0.10↔0.90 ship, 0.30↔0.10 red)
    # aynı terminalleri verir, ama artık DOĞRU yasadan geçerek.
    return wf.wf_from_scores(oos, folds=((40, oos), (40, oos)))


# ---------- KORUNUM + ÜRETKENLİK: her öneri kayıtlı bir terminale ulaşır ----------
def test_every_proposal_reaches_a_recorded_terminal(seeded, monkeypatch):
    """Dört gerçek yol da bir hipotez SATIRI bırakmalı — 'değerlendirdim ama iz yok' olamaz."""
    from meridian import backtest
    scenarios = {
        "rejected_by_guard": ({"variable": "yok_boyle_knob", "new": 1.0}, None, None),
        "rejected_by_backtest": ({"variable": "entry.min_score", "new": 65}, 0.30, 0.10),
        "shipped": ({"variable": "entry.min_score", "new": 65}, 0.10, 0.90),
    }
    for expected, (prop, inc_oos, cand_oos) in scenarios.items():
        store.write_jsonl(memory.HYP, [])
        if inc_oos is not None:
            fixtures = {1: _wf(inc_oos), 2: _wf(cand_oos)}
            monkeypatch.setattr(backtest, "walk_forward",
                                lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
            monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
            reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
        res = reflect.submit(dict(prop))
        rows = memory.all_hypotheses()
        assert len(rows) == 1, f"{expected}: hipotez satırı üretilmedi (sessiz değerlendirme)"
        assert res["status"] == expected
        # ship'te sonuç 'shipped', DEFTERDEKİ satır 'live' (sürüm canlıya alındı) — ikisi de terminal
        assert rows[0]["status"] == ("live" if expected == "shipped" else expected)
        assert rows[0].get("variable") is not None


def test_learning_halt_is_a_recorded_refusal_not_a_silent_drop(seeded, monkeypatch):
    from meridian import health
    monkeypatch.setattr(health, "learn_halted", lambda: True)
    res = reflect.submit({"variable": "entry.min_score", "new": 65})
    assert res["status"] == "halt_learning"    # F8-A3 (2026-08-23): üretici kanonik kol adını yazar
    assert memory.all_hypotheses() == []                      # değerlendirme HİÇ yapılmadı
    assert any(e.get("event") == "submit_blocked_learn_halt" for e in store.read_jsonl("events.jsonl"))


def test_gate_record_is_attached_to_every_evaluated_hypothesis(seeded, monkeypatch):
    from meridian import backtest
    fixtures = {1: _wf(0.30), 2: _wf(0.10)}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect.submit({"variable": "entry.min_score", "new": 65})
    row = memory.all_hypotheses()[0]
    assert row["status"] == "rejected_by_backtest"
    assert row.get("reject_reasons") or row.get("backtest"), "reddin GEREKÇESİ kayıtta yok"


# ---------- TUTARLILIK: önbellek bar revizyonuna bağlı ----------
def test_wf_cache_is_invalidated_by_a_bar_revision(seeded, monkeypatch):
    """Bayat-bar incumbent'ı bu oturumun en pahalı hatasıydı: rev değişince önbellek DÜŞMELİ."""
    from meridian import backtest
    calls = {"n": 0}

    def _wfx(*a, **k):
        calls["n"] += 1
        return _wf(0.2 + calls["n"] * 0.01)

    monkeypatch.setattr(backtest, "walk_forward", _wfx)
    store.write_json("wf_cache_rev.json", {"rev": 1})
    reflect._INC_CACHE.clear()
    p = config.default_strategy()["params"]
    a = reflect._wf_cached(p, 1, None, None, config.goal())
    b = reflect._wf_cached(p, 1, None, None, config.goal())
    assert a == b and calls["n"] == 1, "önbellek isabet etmiyor"
    store.write_json("wf_cache_rev.json", {"rev": 2})          # barlar değişti
    reflect.clear_wf_caches.__wrapped__ if hasattr(reflect.clear_wf_caches, "__wrapped__") else None
    reflect._INC_CACHE.clear()                                  # rev değişimi bunu tetikler (data.py)
    c = reflect._wf_cached(p, 1, None, None, config.goal())
    assert calls["n"] == 2 and c != a, "bar revizyonu sonrası BAYAT incumbent servis edildi"


def test_probe_cache_key_includes_the_window(seeded):
    """Farklı pencerede koşan aynı sonda AYNI anahtarı kullanamaz (sprint ile üretim karışır)."""
    strat = config.default_strategy()
    w1 = ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-30", [], 10)
    w2 = ("2022-01-01", "2023-01-01", "2025-01-01", "2025-12-31", [], 10)
    assert reflect._probe_key(strat, "entry.min_score", 65, w1) != \
        reflect._probe_key(strat, "entry.min_score", 65, w2)


# ---------- MONOTONLUK: sürüm ileri gider ----------
def test_ship_moves_the_version_forward(seeded, monkeypatch):
    from meridian import backtest
    fixtures = {1: _wf(0.10), 2: _wf(0.90)}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    before = int(config.load_strategy()["version"])
    res = reflect.submit({"variable": "entry.min_score", "new": 65})
    assert res["status"] == "shipped"
    after = int(config.load_strategy()["version"])
    assert after > before and res["version"] == after
    assert config.load_strategy()["parent"] == before          # soy zinciri kopmaz


def test_rejected_proposal_never_touches_the_live_version(seeded, monkeypatch):
    from meridian import backtest
    fixtures = {1: _wf(0.30), 2: _wf(0.10)}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    before = config.load_strategy()
    reflect.submit({"variable": "entry.min_score", "new": 65})
    assert config.load_strategy() == before, "reddedilen öneri canlı stratejiye dokundu"


# ---------- SAHİPLİK: tek ship yetkisi ----------
def test_only_reflect_commits_a_version():
    """versioning.commit TEK yerden çağrılmalı — ikinci bir çağıran kapıyı atlayan bir ship demektir."""
    callers = []
    for f in pathlib.Path("meridian").rglob("*.py"):
        tree = ast.parse(f.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "commit" and getattr(n.func.value, "id", "") == "versioning":
                callers.append(f.name)
    assert set(callers) == {"reflect.py"}, f"versioning.commit başka yerden çağrılıyor: {set(callers)}"


def test_submit_is_guarded_by_a_cross_process_lock(seeded, monkeypatch):
    """İki süreç aynı anda ship edemez; kaybeden DÜRÜST bir 'locked' alır (audit #24)."""
    src = inspect.getsource(reflect.submit)
    assert "_ProcessLock" in src
    monkeypatch.setattr(reflect._ProcessLock, "__enter__",
                        lambda self: setattr(self, "held", False) or self)
    monkeypatch.setattr(reflect._ProcessLock, "__exit__", lambda self, *a: None)
    res = reflect.submit({"variable": "entry.min_score", "new": 65})
    assert res["status"] == "locked" and memory.all_hypotheses() == []


def test_submit_writes_only_its_own_artifacts(seeded, monkeypatch):
    """Ship, goal/bounds'a ASLA dokunmaz (Hermes'e değişmez olan şeyler)."""
    from meridian import backtest
    fixtures = {1: _wf(0.10), 2: _wf(0.90)}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    goal_before = (config.STATE / "goal.yaml").read_text()
    bounds_before = (config.STATE / "bounds.yaml").read_text()
    reflect.submit({"variable": "entry.min_score", "new": 65})
    assert (config.STATE / "goal.yaml").read_text() == goal_before
    assert (config.STATE / "bounds.yaml").read_text() == bounds_before
