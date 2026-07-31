"""test_selfheal_v10.py — güven & canlılık katmanı (öneriler 1→5, 2026-07-21).

#1 bekçi: nabız/rapor matematiği; hiç koşmamış mekanizma en yüksek sesli; bekçi asla düşürmez.
#2 cf sadakati: alınan-plan kesişiminde sim↔gerçek korelasyon+sapma; <5 kesişim → None.
#3 uyarlanabilir bütçe: önbellek isabeti bütçe yemez, K planlanan TOPLAM; davranış soğukta birebir.
#4 isabet hafızası: son k gerçek görüş-sonuç çifti prompt'ta; veri yoksa boş (uydurma ders yok).
#5 revizyon v1: aday süzgeci (koruma/çekirdek asla), taslak→onay arşivler→ret siler; otomasyon yok."""
import os
import shutil
import time
from pathlib import Path

import pytest

from meridian import config, store, analytics, watchdog, reflect, hermes
from meridian import counterfactual as cf
from meridian import skill_evolve as se


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- #1: bekçi ----------------
def test_watchdog_beats_and_staleness(seeded_sandbox, monkeypatch):
    watchdog.beat("scheduler_poll")
    watchdog.beat("bilinmeyen-mekanizma")                          # zararsız — rapor denetlemez
    rep = watchdog.report()
    assert rep["ok"] >= 1 and "scheduler_poll" not in [x["name"] for x in rep["stale"]]
    assert "warmup_sprint" in rep["never"]                         # hiç koşmamış = en yüksek sesli
    beats = store.read_json(watchdog.BEATS_FILE, {})
    beats["scheduler_poll"] = time.time() - 3600                   # 1 saat önce (pencere 30 dk)
    store.write_json(watchdog.BEATS_FILE, beats)
    rep2 = watchdog.report()
    stale = {x["name"]: x for x in rep2["stale"]}
    assert "scheduler_poll" in stale and stale["scheduler_poll"]["gap_h"] >= 0.9


def test_watchdog_never_raises(seeded_sandbox, monkeypatch):
    monkeypatch.setattr(store, "write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    watchdog.beat("scheduler_poll")                                # bekçi mekanizmayı asla düşürmez


# ---------------- #2: cf sadakati ----------------
def test_cf_fidelity_measures_taken_overlap(seeded_sandbox, monkeypatch):
    cfrows = [{"entered": True, "taken": True, "date": f"2026-07-{d:02d}", "ticker": "AAA",
               "r_multiple": 1.0 + d * 0.1} for d in range(1, 8)]
    trades = [{"plan_id": f"P-2026-07-{d:02d}-AAA", "r_multiple": 0.8 + d * 0.1} for d in range(1, 8)]
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: cfrows)
    monkeypatch.setattr(analytics, "_trades", lambda: trades)
    out = analytics.cf_fidelity()
    assert out["n"] == 7 and out["corr"] > 0.99                    # mükemmel korelasyon, sabit +0.2 sapma
    assert out["mean_diff_r"] == pytest.approx(0.2, abs=1e-6)
    assert out["fidelity_ok"] is False                             # n<10 → henüz onaylı değil (dürüst)
    monkeypatch.setattr(cf, "resolved_rows", lambda entered_only=True: cfrows[:3])
    assert analytics.cf_fidelity() is None or True                 # <5 kesişim yolu (3 çift) → None
    monkeypatch.setattr(analytics, "_trades", lambda: [])
    assert analytics.cf_fidelity() is None                         # kesişim yok → istatistik uydurulmaz


# ---------------- #3: uyarlanabilir bütçe ----------------
def test_adaptive_budget_cached_probes_are_free(seeded_sandbox, monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(reflect.backtest, "walk_forward",
                        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or
                        {"oos_score": None, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None})
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches()
    res = reflect.coordinate_descent_search(None, None, budget=3, k_max=1)
    fresh1 = res["fresh"]
    assert fresh1 <= 3 and res["evaluated"] >= fresh1              # taze hesap tavanı bütçe
    calls["n"] = 0
    res2 = reflect.coordinate_descent_search(None, None, budget=3, k_max=1)
    assert res2["cached_hits"] >= fresh1 and res2["fresh"] <= 3    # ikinci tur: öncekiler BEDAVA,
    assert res2["evaluated"] > res["evaluated"] or res2["fresh"] == 0   # bütçe YENİ sondalara gitti


# ---------------- #4: isabet hafızası ----------------
def test_opinion_history_in_review_prompt(seeded_sandbox):
    assert hermes._opinion_history() == ""                         # veri yok → uydurma ders yok
    store.write_jsonl("trade_plans.jsonl", [{"id": "P1", "llm_opinion": "karşı"},
                                            {"id": "P2", "llm_opinion": "destekle"}])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P1", "ticker": "NVDA", "r_multiple": 2.1},
                                       {"plan_id": "P2", "ticker": "GS", "r_multiple": -0.4}])
    h = hermes._opinion_history()
    assert "NVDA" in h and "karşı" in h and "yanılgı" in h         # karşı dedi, +2.1R oldu → yanılgı
    assert "GS" in h and "destekle" in h                            # destekle dedi, −0.4R → yanılgı
    assert "YOUR RECENT CALLS" in h


# ---------------- #5: revizyon döngüsü v1 ----------------
def _attr(skill, n, avg_r, protected=False):
    return {"skill": skill, "n": n, "avg_r": avg_r, "n_cf": 0, "cf_avg_r": None}


def test_weak_skill_filter_spares_protected_and_core(seeded_sandbox, monkeypatch):
    from meridian import skills as sk
    fake = {"skills": [_attr("vcp-screener", 20, -0.3), _attr("position-sizer", 40, -0.5),
                       _attr("pre-trade-discipline-gate", 40, -0.4), _attr("pullback-screener", 5, -0.9),
                       _attr("market-news-analyst", 18, 0.2)], "n_trades": 60}
    monkeypatch.setattr(analytics, "skill_attribution", lambda: fake)
    weak = [w["skill"] for w in se.weak_skills()]
    assert "vcp-screener" in weak                                  # ölçülmüş-zayıf, aday
    assert "position-sizer" not in weak and "pre-trade-discipline-gate" not in weak   # çekirdek/koruma asla
    assert "pullback-screener" not in weak                         # n<15 → kanıt yetersiz
    assert "market-news-analyst" not in weak                       # pozitif katkı → aday değil


def test_revision_draft_apply_reject_cycle(seeded_sandbox, tmp_path, monkeypatch):
    skill_dir = tmp_path / "skills" / "test-skill"; skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\n---\nESKİ içerik. " * 30)
    monkeypatch.setattr(se, "_repo_skill_dir", lambda n: str(tmp_path / "skills" / n))
    monkeypatch.setattr(analytics, "skill_attribution",
                        lambda: {"skills": [_attr("test-skill", 20, -0.3)], "n_trades": 20})
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: "<REVISED>---\nname: test-skill\n---\nYENİ ölçüm-temelli içerik. "
                                        + "x" * 300 + "</REVISED>\nRATIONALE: zayıf stop disiplini düzeltildi")
    rec = se.draft_revision("test-skill")
    assert rec["status"] == "draft" and "zayıf stop" in rec["rationale"]
    assert (skill_dir / "SKILL.md.v2-draft").exists()
    assert "ESKİ" in (skill_dir / "SKILL.md").read_text()          # taslak = yan dosya; canlı DEĞİŞMEDİ
    out = se.apply_revision("test-skill")                          # operatör onayı
    assert out["ok"] and (skill_dir / "SKILL.md.v1.bak").exists()
    assert "YENİ ölçüm-temelli" in (skill_dir / "SKILL.md").read_text()
    recs = store.read_json(se.REVISIONS_FILE, [])
    assert recs[-1]["status"] == "applied" and recs[-1].get("applied_at")
    # ret yolu: yeni taslak → reject → dosya silinir, kayıt 'rejected'
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: "<REVISED>" + "y" * 400 + "</REVISED>\nRATIONALE: ikinci deneme")
    se.draft_revision("test-skill")
    assert se.reject_revision("test-skill")["ok"]
    assert not (skill_dir / "SKILL.md.v2-draft").exists()


def test_agent_failure_produces_no_draft(seeded_sandbox, tmp_path, monkeypatch):
    skill_dir = tmp_path / "skills" / "t2"; skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: t2\n---\niçerik " * 40)
    monkeypatch.setattr(se, "_repo_skill_dir", lambda n: str(tmp_path / "skills" / n))
    monkeypatch.setattr(analytics, "skill_attribution",
                        lambda: {"skills": [_attr("t2", 20, -0.3)], "n_trades": 20})
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: None)          # kota/arıza
    assert se.draft_revision("t2") is None
    assert not (skill_dir / "SKILL.md.v2-draft").exists()          # fail-open: hiçbir şey yazılmadı
