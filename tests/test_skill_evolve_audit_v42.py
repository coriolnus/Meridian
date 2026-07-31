"""test_skill_evolve_audit_v42.py — skill_evolve denetimi (2026-07-21, tur 29).

Bu modül REPO DOSYASI değiştiren tek yer (SKILL.md'leri). 7. soru:
  SK1 "korunan skill'ler asla değişmez" → koruma YALNIZ taslak üretiminde vardı; apply_revision
     hiçbir kontrol yapmıyordu. Elde bir taslak dosyası bulunan korunan bir skill (kapı skill'i
     dahil) onaylandığında EZİLİRDİ. Savunma tek uçtaydı.
  SK2 "skill adı bir dizin adıdır" → ad doğrudan os.path.join'e giriyordu: '../../..' içeren bir ad
     skills/ DIŞINDA dosya değiştirebilirdi (os.replace ile).
  SK3 "otomatik hiçbir şey uygulanmaz" → taslak yazılır, uygulama İNSAN kararıdır
"""
from __future__ import annotations

import inspect
import os

import pytest

from meridian import skill_evolve as se, store


# ---------- SK2: ad doğrulama / yol kaçışı ----------
@pytest.mark.parametrize("bad", ["../../etc", "../evil", "a/b", ".hidden", "", "x\x00y", "..%2f.."])
def test_sk2_path_escapes_are_refused(bad):
    with pytest.raises(ValueError):
        se._repo_skill_dir(bad)


def test_sk2b_apply_and_reject_refuse_bad_names(sandbox_state):
    assert se.apply_revision("../../../tmp/evil")["ok"] is False
    assert se.reject_revision("../../../tmp/evil")["ok"] is False


def test_sk2c_valid_name_resolves_inside_skills():
    p = se._repo_skill_dir("vcp-screener")
    assert p.startswith(os.path.realpath(se._skills_root()) + os.sep)


# ---------- SK1: koruma her iki uçta ----------
def test_sk1_protected_skills_cannot_be_applied(sandbox_state):
    for name in sorted(se.CORE_NEVER):
        res = se.apply_revision(name)
        assert res["ok"] is False and "korumalı" in res["detail"]
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "skill_revision_refused"]
    assert len(ev) >= len(se.CORE_NEVER)


def test_sk1b_protected_set_includes_the_gate_skill():
    from meridian import skills as sk
    protected = set(getattr(sk, "PROTECTED", ()) or ()) | se.CORE_NEVER
    assert "pre-trade-discipline-gate" in protected


def test_sk1c_weak_candidates_never_include_protected():
    src = inspect.getsource(se.weak_skills)
    assert "protected" in src and "CORE_NEVER" in src


# ---------- SK3: uygulama insan kararı ----------
def test_sk3_nothing_is_applied_automatically():
    """Haftalık iş YALNIZ taslak üretir; apply çağrısı otomatik yollarda geçmemeli."""
    src = inspect.getsource(se.weekly_draft) + inspect.getsource(se.draft_revision)
    assert "apply_revision" not in src
    from meridian import scheduler
    sched_src = inspect.getsource(scheduler)
    assert "apply_revision" not in sched_src, "zamanlayıcı taslağı KENDİ uyguluyor olabilir"


def test_sk3b_missing_draft_is_a_clean_refusal(sandbox_state):
    res = se.apply_revision("vcp-screener")
    assert res["ok"] is False and res["detail"] == "taslak yok"


def test_sk3c_thresholds_are_evidence_based():
    assert se.MIN_REAL_N >= 10 and se.MAX_AVG_R < 0     # "ölçülmüş-zayıf" gerçekten ölçüme dayanır
