"""Key-gated skill enablement — the 'auto-enable when the FMP key lands' the registry reason promised.
reconcile_enablement() must flip fmp/alpaca-required skills on when the key is present, off when absent,
and never touch style-inactive or keyless skills wrongly."""
import pytest

from meridian import skills, store, secrets, config


def _seed_registry(sandbox):
    reg = {"skills": {
        # canslim-screener: FMP-temel-kapılı, style-active, HENÜZ engine-implemented DEĞİL (Faz C temel
        # önbelleği yok) → key-gating'in DOĞRU exemplar'ı: anahtar gelince aç, gidince kapat.
        "canslim-screener": {"fmp": "req", "alpaca": "-", "enabled": False, "style_active": True,
                             "mode": "disabled", "reason": "FMP_API_KEY absent — auto-enable when key lands"},
        "vcp-screener":   {"fmp": "req", "alpaca": "-", "enabled": True, "style_active": True,
                           "mode": "active", "reason": "enabled"},   # ENGINE_IMPLEMENTED: key-gating must SKIP it
        # 2026-07-24: pead-screener artık ENGINE_IMPLEMENTED (motor earnings.csv üzerinden ANAHTARSIZ koşar) →
        # vcp gibi key-gating'den MUAF, FMP anahtarı gitse bile asla key-disable edilmez.
        "pead-screener":  {"fmp": "req", "alpaca": "-", "enabled": True, "style_active": True,
                           "mode": "active", "reason": "enabled"},
        "pair-trade":     {"fmp": "req", "alpaca": "-", "enabled": False, "style_active": False,
                           "mode": "disabled", "reason": "FMP_API_KEY absent — auto-enable when key lands"},
        "finviz":         {"fmp": "-", "alpaca": "-", "enabled": True, "style_active": True,
                           "mode": "active", "reason": "enabled"},
        "alpaca-executor": {"fmp": "-", "alpaca": "req", "enabled": False, "style_active": True,
                            "mode": "disabled", "reason": "ALPACA absent"},
    }}
    store.write_json("skills_registry.json", reg)


def test_fmp_key_enables_style_active_fmp_skills(sandbox_state, monkeypatch):
    _seed_registry(sandbox_state)
    monkeypatch.setenv("FMP_API_KEY", "present")
    secrets.clear_cache()
    rec = skills.reconcile_enablement()
    reg = skills.registry()["skills"]
    assert "canslim-screener" in rec["changed"]
    assert reg["canslim-screener"]["enabled"] is True and reg["canslim-screener"]["reason"] == "enabled"
    # pead-screener artık ENGINE_IMPLEMENTED → key-gating onu ATLAR (değişmez, zaten enabled)
    assert "pead-screener" not in rec["changed"] and reg["pead-screener"]["enabled"] is True
    # style-inactive FMP skill stays OFF, with an HONEST reason (not "key absent")
    assert reg["pair-trade"]["enabled"] is False
    assert "stile uygun" in reg["pair-trade"]["reason"]
    # keyless skill untouched; alpaca-req stays off (no alpaca key)
    assert reg["finviz"]["enabled"] is True
    assert reg["alpaca-executor"]["enabled"] is False


def test_removing_fmp_key_disables_again(sandbox_state, monkeypatch):
    _seed_registry(sandbox_state)
    monkeypatch.setenv("FMP_API_KEY", "present")
    secrets.clear_cache()
    skills.reconcile_enablement()
    assert skills.registry()["skills"]["canslim-screener"]["enabled"] is True
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    secrets.clear_cache()
    rec = skills.reconcile_enablement()
    reg = skills.registry()["skills"]
    assert "canslim-screener" in rec["changed"] and reg["canslim-screener"]["enabled"] is False
    assert "FMP_API_KEY" in reg["canslim-screener"]["reason"]  # honest: names the missing key
    # audit #36: ENGINE_IMPLEMENTED (vcp + artık pead) ve PROTECTED skiller ASLA key-disable edilmez —
    # motor onları anahtarsız veride natif koşar / güvenlik katmanıdır
    assert reg["vcp-screener"]["enabled"] is True
    assert reg["pead-screener"]["enabled"] is True             # engine-implemented → anahtar gitse de açık kalır


def test_reconcile_is_idempotent(sandbox_state, monkeypatch):
    _seed_registry(sandbox_state)
    monkeypatch.setenv("FMP_API_KEY", "present")
    secrets.clear_cache()
    skills.reconcile_enablement()
    assert skills.reconcile_enablement()["changed"] == []       # second pass changes nothing
