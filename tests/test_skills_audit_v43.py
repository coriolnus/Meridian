"""test_skills_audit_v43.py — skills denetimi (2026-07-21, tur 30).

Kayıt defteri "ajanın ne yapabildiğinin" tek kaynağı. 7. soru:
  SL1 "korunan skill hiçbir yoldan kapatılamaz" → iki ayrı yol var (apply_skill_action ve
     reconcile_enablement); ikisi de KORUMAYI ayrı ayrı uyguluyor, kıyaslanmıyordu
  SL2 "kayıt defteri kilitli yazılır" → HAYIR: oku-değiştir-yaz, üstelik İKİ daemon iş parçacığından
     (zamanlayıcı pipeline damgası + pano gölge kararı). memory.py'de aynı desen audit #19'da
     veri kaybına yol açmıştı; burada kilit yoktu → bir 'shadow' kararı sessizce geri dönebilirdi
  SL3 "koşan ile mevcut olan ayrıdır" → declared-only skill'ler 'invoked' diye loglanmamalı (eski hata)
"""
from __future__ import annotations

import threading

import pytest

from meridian import skills as sk, store


def _reg(names=("vcp-screener", "pullback-screener", "pre-trade-discipline-gate", "canslim-screener")):
    store.write_json(sk.REGISTRY, {"skills": {
        n: {"enabled": True, "mode": "active", "reason": "enabled", "pipeline": "P2_SCREEN",
            "fmp": "opt", "alpaca": "opt", "style_active": True} for n in names}})


# ---------- SL1: koruma her yolda ----------
def test_sl1_protected_cannot_be_shadowed(sandbox_state):
    _reg()
    for name in sorted(sk.PROTECTED):
        res = sk.apply_skill_action(name, "shadow")
        assert res["ok"] is False and "korumalı" in res["reason"]


def test_sl1b_protected_is_never_key_disabled(sandbox_state, monkeypatch):
    """audit #36 nüksü: Alpaca anahtarı silinince PROTECTED portfolio-manager kapanmıştı."""
    store.write_json(sk.REGISTRY, {"skills": {
        "portfolio-manager": {"enabled": True, "mode": "active", "reason": "enabled",
                              "fmp": "req", "alpaca": "req", "style_active": True}}})
    from meridian.adapters import fmp, alpaca
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    sk.reconcile_enablement()
    assert sk.registry()["skills"]["portfolio-manager"]["enabled"] is True


def test_sl1c_shadow_decision_outranks_key_gating(sandbox_state, monkeypatch):
    store.write_json(sk.REGISTRY, {"skills": {
        "canslim-screener": {"enabled": True, "mode": "shadow", "shadow": True, "reason": "gölge",
                             "fmp": "req", "alpaca": "opt", "style_active": True}}})
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    sk.reconcile_enablement()
    assert sk.registry()["skills"]["canslim-screener"]["mode"] == "shadow"   # operatör kararı korunur


def test_sl1d_unknown_skill_and_action_are_refused(sandbox_state):
    _reg()
    assert sk.apply_skill_action("yok-boyle-skill", "shadow")["ok"] is False
    assert sk.apply_skill_action("vcp-screener", "delete")["ok"] is False


# ---------- SL2: eşzamanlı yazımda karar kaybolmaz ----------
def test_sl2_concurrent_writes_do_not_lose_a_shadow_decision(sandbox_state):
    _reg()
    errors = []

    def stamp():
        try:
            for _ in range(40):
                sk._touch_registry_run("vcp-screener", "state/x.json")
        except Exception as e:                       # pragma: no cover
            errors.append(e)

    t = threading.Thread(target=stamp)
    t.start()
    for _ in range(20):
        sk.apply_skill_action("canslim-screener", "shadow")
        sk.apply_skill_action("canslim-screener", "activate")
    sk.apply_skill_action("canslim-screener", "shadow")
    t.join()
    assert not errors
    info = sk.registry()["skills"]["canslim-screener"]
    assert info["shadow"] is True and info["mode"] == "shadow", "gölge kararı eşzamanlı yazımda kayboldu"


def test_sl2b_registry_has_a_lock():
    import inspect
    src = inspect.getsource(sk)
    assert "_REG_LOCK" in src and "with _REG_LOCK" in src


# ---------- SL3: koşan ≠ mevcut ----------
def test_sl3_declared_only_skills_are_not_logged_as_invoked(sandbox_state):
    _reg()
    with sk.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
        pass
    run = store.read_jsonl(sk.RUNS)[-1]
    for s in run["skills_invoked"]:
        assert s in sk.ENGINE_IMPLEMENTED, f"{s} motorda YOK ama 'invoked' diye loglandı"
    assert set(run["skills_declared_not_run"]).isdisjoint(set(run["skills_invoked"]))


def test_sl3b_pipeline_error_is_logged_not_hidden(sandbox_state):
    _reg()
    with pytest.raises(RuntimeError):
        with sk.pipeline_run("P2_SCREEN"):
            raise RuntimeError("patla")
    run = store.read_jsonl(sk.RUNS)[-1]
    assert run["status"] == "error" and "patla" in run["error"]


def test_sl3c_only_invoked_skills_get_a_run_stamp(sandbox_state):
    _reg()
    with sk.pipeline_run("P2_SCREEN", artifact="state/candidates.jsonl"):
        pass
    reg = sk.registry()["skills"]
    for name, info in reg.items():
        if name in sk.ENGINE_IMPLEMENTED:
            continue
        assert "last_run" not in info, f"{name} koşmadan 'last_run' damgası aldı"
