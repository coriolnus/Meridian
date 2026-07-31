"""test_guard_audit_v27.py — guard denetimi (2026-07-21, tur 12).

guard, "LLM'e söylenen her kuralın GERÇEKTEN uygulandığı" yer. 7. soru:
  GU1 "GOAL_KEYS/LIMIT_KEYS goal.yaml'ı kapsar" → elle bakımlı iki liste; goal.yaml yeni bir anahtar
     kazanınca liste sessizce eksik kalır (ve o anahtar bounds'ta da varsa DEĞİŞTİRİLEBİLİR olur)
  GU2 "iki yüzey aynı yasayı uygular"           → BULUNDU: ayrışmışlardı. check_trade zarfın ikinci
     bir KOPYASINI taşıyordu; classify_gate zamanla R:R tabanını ve ısı tavanını SERT'e çevirmiş,
     kopya geride kalmıştı — canlıda NO_GO olan bir plana "geçti" diyordu. check_trade artık
     classify_gate'i çağırıyor: ayrışma yapısal olarak imkânsız
  GU3 "canlı param'ı olmayan @regime reddedilir" → yazılıydı, kilitlensin (sessizce düşen override,
     kapıya SAHTE bir ölü-son kaydeder)
"""
from __future__ import annotations

import itertools
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, guard


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# ---------- GU1: değişmezlik listeleri goal.yaml ile senkron ----------
def test_gu1_every_goal_key_is_immutable(seeded):
    g = config.goal()
    top = {k for k in g if k != "limits"}
    missing = top - guard.GOAL_KEYS
    assert not missing, f"goal.yaml'da olup GOAL_KEYS'te olmayan: {missing} → Hermes'e açık kalabilir"


def test_gu1b_every_limit_key_is_immutable(seeded):
    missing = set(config.goal()["limits"]) - guard.LIMIT_KEYS
    assert not missing, f"limits'te olup LIMIT_KEYS'te olmayan: {missing}"


def test_gu1c_immutable_keys_are_actually_refused(seeded):
    for key in ("min_sample", "one_variable_only", "max_open_positions", "autonomy_level"):
        v = guard.validate_change({"variable": key, "new": 99}, {"entry.min_score": 60},
                                  config.bounds(), config.goal(), [], 0)
        assert v.ok is False and any("immutable" in r for r in v.reasons), key


# ---------- GU2: iki yüzey, tek yasa ----------
def _cases(goal):
    lim = goal["limits"]
    plans = [{"ticker": "AAA", "sector": "tech", "size_r": r, "r_multiple_expected": rr, "score": s}
             for r in (0.5, lim["max_position_r"], lim["max_position_r"] + 0.5)
             for rr in (1.0, 2.5) for s in (55, 80)]
    ports = [{"open_positions": n, "sector_counts": sc, "day_pnl_pct": p}
             for n in (0, lim["max_open_positions"] - 1, lim["max_open_positions"])
             for sc in ({}, {"tech": lim["max_open_positions"]})
             for p in (0.0, -lim["max_daily_loss_pct"] / 100.0)]
    regs = [{"exposure_budget_pct": 0}, {"exposure_budget_pct": 60}]
    return itertools.product(plans, ports, regs)


def test_gu2_hard_rules_agree_across_both_surfaces(seeded):
    """ASIL koruma: sert zarf iki ayrı fonksiyonda yazılı. Biri değişip diğeri kalırsa canlı
    davranış ile kapı ölçümü ayrışır — ve bunu hiçbir test söylemezdi."""
    goal = config.goal()
    checked = 0
    for plan, port, reg in _cases(goal):
        old_ok = guard.check_trade(plan, port, reg, goal).ok
        verdict, _ = guard.classify_gate(plan, port, reg, goal)
        assert old_ok == (verdict != "NO_GO"), f"ayrışma: {plan} {port} {reg} → {old_ok} vs {verdict}"
        checked += 1
    assert checked >= 100, "senaryo üretimi bozuldu"


def test_gu2b_low_rr_is_a_hard_veto_on_both_surfaces(seeded):
    """R:R tabanı SERT (plan başına değişen hedef sığ-bazlı kurulumu eler). Önemli olan: İKİ yüzey de
    aynı şeyi desin — eskiden classify_gate NO_GO derken check_trade 'geçti' diyordu."""
    goal = config.goal()
    plan = {"ticker": "AAA", "sector": "tech", "size_r": 0.5, "r_multiple_expected": 1.0, "score": 61}
    port = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0}
    verdict, _ = guard.classify_gate(plan, port, {"exposure_budget_pct": 60}, goal)
    assert verdict == "NO_GO"
    assert guard.check_trade(plan, port, {"exposure_budget_pct": 60}, goal).ok is False

    ok_plan = {**plan, "r_multiple_expected": 2.5}
    assert guard.classify_gate(ok_plan, port, {"exposure_budget_pct": 60}, goal)[0] in ("GO", "REVIEW")
    assert guard.check_trade(ok_plan, port, {"exposure_budget_pct": 60}, goal).ok is True


# ---------- GU3: sessizce düşen override reddedilir ----------
def test_gu3_regime_override_needs_the_base_knob(seeded):
    v = guard.validate_change({"variable": "exit.trail_atr_mult@chop", "new": 3.0},
                              {"entry.min_score": 60}, config.bounds(), config.goal(), [], 0)
    assert v.ok is False and any("silently ignored" in r for r in v.reasons)


def test_gu3b_regime_detection_knob_cannot_be_regime_scoped(seeded):
    v = guard.validate_change({"variable": "regime.min_exposure_score@chop", "new": 50},
                              {"regime.min_exposure_score": 40}, config.bounds(), config.goal(), [], 0)
    assert v.ok is False and any("rejim tespitinin kendisini" in r for r in v.reasons)


def test_gu3c_unknown_regime_refused(seeded):
    v = guard.validate_change({"variable": "entry.min_score@risk_off", "new": 65},
                              {"entry.min_score": 60}, config.bounds(), config.goal(), [], 0)
    assert v.ok is False and any("unknown regime" in r for r in v.reasons)


# ---------- tek değişken yasası + bounds kapsaması ----------
def test_one_variable_only_is_enforced(seeded):
    v = guard.validate_change({"changes": {"a": 1, "b": 2}}, {}, config.bounds(), config.goal(), [], 0)
    assert v.ok is False and "one_variable_only" in v.reasons[0]


def test_every_live_param_is_tunable_or_deliberately_frozen(seeded):
    """Bounds'ta olmayan bir param HİÇ ayarlanamaz (sessizce dondurulmuş olur). Bu bir hata olmak
    zorunda değil ama GÖRÜNÜR olmalı — liste burada, sürprizi kapatır."""
    params = set(config.default_strategy()["params"])
    tunable = set(config.bounds())
    frozen = sorted(params - tunable)
    assert frozen == [], f"bounds.yaml'da olmayan param'lar sessizce dondurulmuş: {frozen}"
