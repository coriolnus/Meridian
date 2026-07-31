"""test_hermes_audit_v28.py — hermes denetimi (2026-07-21, tur 13).

hermes, sistemdeki TEK "akıllı ama güvenilmez" bileşen: LLM önerir, KAPI karar verir. 7. soru:
  H1 "LLM canlı stratejiyi asla doğrudan yazmaz" → sistemin MERKEZİ güvenlik iddiası; docstring'lerde
     defalarca yazılı, hiçbir yerde ZORLANMIYORDU. Tek satırlık bir gelecek düzenleme (config.dump_yaml
     ya da versioning.bump çağrısı) kapıyı tamamen atlatırdı ve hiçbir test bunu söylemezdi.
  H2 "anahtar değeri loglanmaz"                  → yorumlarda söz veriliyor; test yoktu
  H3 "ajan bütçesi sessiz açlığa dönüşmez"       → RPD dolunca çağıran deterministik yola düşmeli VE
     bu bir kez KAYDA geçmeli
"""
from __future__ import annotations

import ast
import inspect
import re
import shutil
from pathlib import Path

import pytest

from meridian import config, hermes, store


HSRC = inspect.getsource(hermes)
HTREE = ast.parse(HSRC)


def _called_names() -> set:
    """Gerçekten ÇAĞRILAN adlar (docstring/prompt içinde geçen metinler değil) — AST ile."""
    out = set()
    for n in ast.walk(HTREE):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                out.add(f.attr)
            elif isinstance(f, ast.Name):
                out.add(f.id)
    return out


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# ---------- H1: yetki sınırı — öneren, uygulamaz ----------
def test_h1_hermes_never_writes_the_live_strategy():
    """Metin araması yetmez (bounds.yaml/goal.yaml prompt'ta ANLATILIYOR) — ÇAĞRI var mı diye AST'ye
    bakıyoruz. Amaç: kapıyı atlayan tek satırlık bir gelecek düzenleme testi kırsın."""
    called = _called_names()
    forbidden = {"dump_yaml", "save_strategy", "bump", "revert_to", "write_strategy"}
    hits = called & forbidden
    assert not hits, f"hermes canlı yapılandırmayı DOĞRUDAN yazıyor olabilir: {hits}"
    assert "strategy_path" not in called


def test_h1b_only_gate_backed_ship_paths_exist():
    """Gemiye çıkış YALNIZ reflect.submit / reflect.search_and_submit üzerinden — ikisi de kapıyı içerir."""
    ship_calls = set(re.findall(r"reflect\.(\w+)\(", HSRC))
    allowed = {"submit", "search_and_submit"}
    assert ship_calls <= allowed | {"_default_windows", "_wf_cached", "_gate_eval", "backtest"}, \
        f"reflect üzerinden beklenmedik çağrı: {ship_calls - allowed}"
    assert "submit" in ship_calls and "search_and_submit" in ship_calls


def test_h1c_reflect_once_delegates_shipping(sandbox_state, monkeypatch):
    """Davranışsal kilit: öneri gelse bile hermes onu KENDİ uygulamaz — submit()'e verir."""
    from meridian import reflect
    calls = []
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: {"variable": "entry.min_score", "new": 65, "source": "llm"})
    monkeypatch.setattr(reflect, "submit", lambda p: calls.append(p) or {"status": "shipped"})
    out = hermes.reflect_once(target_regime="trend_up")
    assert out["status"] == "shipped" and len(calls) == 1
    assert not (sandbox_state / "strategy.yaml").exists(), "hermes stratejiyi kendi yazmış"


def test_h1d_uncertified_regime_proposal_is_dropped(seeded, monkeypatch):
    """Horizon guardrail BİR rejim için kanıt onayladı; öneri BAŞKA rejime override yazmaya çalışırsa
    yan kapıdan guardrail atlanır (audit #27) — düşürülmeli."""
    from meridian import reflect, dataset
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: {"variable": "entry.min_score@chop", "new": 65})
    monkeypatch.setattr(dataset, "load", lambda **k: ({}, None))
    monkeypatch.setattr(reflect, "submit", lambda p: pytest.fail("sertifikasız rejim gemiye gitti"))
    monkeypatch.setattr(reflect, "search_and_submit", lambda *a, **k: {"status": "no_candidate", "search": {}})
    hermes.reflect_once(target_regime="trend_up")
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "hermes_proposal_uncertified_regime"]
    assert ev and ev[-1]["certified"] == "trend_up"


# ---------- H2: anahtar hijyeni ----------
def test_h2_pool_key_registration_never_logs_the_key(sandbox_state, monkeypatch):
    import subprocess

    class _R:
        returncode = 0
        stdout = stderr = ""

    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/usr/bin/true")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _R())
    hermes.register_pool_key("gemini", "SECRET-POOL-KEY-42")
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "SECRET-POOL-KEY-42" not in blob


def test_h2b_ping_failure_detail_carries_no_key(monkeypatch):
    import httpx
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda n, *a, **k: "SECRET-PING-KEY" if "KEY" in n else None)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: (_ for _ in ()).throw(
        httpx.ConnectError("boom https://x?key=SECRET-PING-KEY")))
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(
        httpx.ConnectError("boom https://x?key=SECRET-PING-KEY")))
    for prov in ("nous", "gemini"):
        r = hermes.ping_brain(prov)
        assert "SECRET-PING-KEY" not in str(r), f"{prov} ping cevabı anahtar taşıyor"


# ---------- H3: bütçe açlığı sessiz değil ----------
def test_h3_rpd_exhaustion_warns_once_and_blocks(sandbox_state):
    store.write_json(hermes.AGENT_BUDGET_FILE,
                     {"date": __import__("datetime").date.today().isoformat(),
                      "day": hermes.AGENT_RPD, "minute": [], "warned": False})
    assert hermes._agent_budget_take() is False
    assert hermes._agent_budget_take() is False
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "agent_budget_exhausted"]
    assert len(ev) == 1, "günde BİR kez uyarı (sessiz de değil, spam de değil)"


def test_h3b_budget_counts_up_and_resets_daily(sandbox_state):
    import datetime as dt
    store.write_json(hermes.AGENT_BUDGET_FILE,
                     {"date": (dt.date.today() - dt.timedelta(days=1)).isoformat(),
                      "day": hermes.AGENT_RPD, "minute": [], "warned": True})
    assert hermes._agent_budget_take() is True                 # yeni gün → kova sıfırlanır
    assert store.read_json(hermes.AGENT_BUDGET_FILE, {})["day"] == 1


def test_h3c_agent_call_without_binary_is_a_clean_none(monkeypatch):
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    assert hermes._agent_call("merhaba") is None               # fail-open, patlamaz


# ---------- kanıt paketi: LLM'e giden bilgi deterministik ve kaynaklı ----------
def test_evidence_pack_is_deterministic(sandbox_state):
    a, b = hermes.evidence_pack(), hermes.evidence_pack()
    assert a == b and isinstance(a, str)


def test_system_prompt_states_the_authority_boundary():
    assert "do NOT trade" in hermes.SYSTEM or "not trade" in hermes.SYSTEM.lower()
