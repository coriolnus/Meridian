"""test_config_audit_v25.py — config denetimi (2026-07-21, tur 10).

7. soru:
  G1 "boş/bozuk strategy.yaml varsayılana düşer" → `safe_load(f) or {}` **{}** döndürüyordu, yani
     motor params={} ile koşabilirdi: her eşik kaybolur, kapı parametresiz aday ölçer, hata görünmez
  G2 "goal.yaml değişikliği görülür"             → lru_cache(maxsize=1) uzun ömürlü süreçte dosyayı
     SONSUZA dondurur; operatörün elle değiştirdiği limit yeniden başlatmaya kadar yok sayılırdı
  G3 "VALID_REGIMES == regime.py etiketleri"     → yorumda "must match exactly" yazıyor ama hiçbir
     yerde kontrol edilmiyordu; kayarsa var@regime bilgisi sessizce ölü knob'a yazılır
  G4 "rejim override'ı yeni knob İCAT EDEMEZ"    → yasa yazılıydı, testi yoktu
"""
from __future__ import annotations

import inspect

import pytest
import yaml

from meridian import config, regime


# ---------- G1: bozuk/boş strateji dosyası ----------
def test_g1_empty_strategy_file_falls_back_to_defaults(sandbox_state):
    (sandbox_state / "strategy.yaml").write_text("")
    s = config.load_strategy()
    assert s["params"], "boş dosya params={} ile motoru parametresiz bırakıyordu"
    assert s == config.default_strategy()


def test_g1b_corrupt_yaml_falls_back(sandbox_state):
    (sandbox_state / "strategy.yaml").write_text("{{{ bu geçerli yaml değil")
    assert config.load_strategy()["params"] == config.default_strategy()["params"]


def test_g1c_schemaless_doc_falls_back(sandbox_state):
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump({"version": 9, "note": "params yok"}))
    assert config.load_strategy()["params"] == config.default_strategy()["params"]


def test_g1d_valid_file_is_used_as_is(sandbox_state):
    doc = {"version": 7, "params": {"entry.min_score": 99}, "parent": None}
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(doc))
    got = config.load_strategy()
    assert got["version"] == 7 and got["params"]["entry.min_score"] == 99


# ---------- G2: donmuş goal önbelleği ----------
def test_g2_reload_config_picks_up_edited_goal(sandbox_state):
    import shutil
    from pathlib import Path
    repo = Path(__file__).resolve().parent.parent / "state"
    shutil.copy2(repo / "goal.yaml", sandbox_state / "goal.yaml")
    shutil.copy2(repo / "bounds.yaml", sandbox_state / "bounds.yaml")
    config.reload_config()
    first = config.limits()["max_open_positions"]

    doc = yaml.safe_load((sandbox_state / "goal.yaml").read_text())
    doc["limits"]["max_open_positions"] = first + 3
    (sandbox_state / "goal.yaml").write_text(yaml.safe_dump(doc))

    assert config.limits()["max_open_positions"] == first, "önbellek beklendiği gibi donuk"
    config.reload_config()
    assert config.limits()["max_open_positions"] == first + 3, "yeniden yükleme değişikliği görmeli"
    config.reload_config()


def test_g2b_daily_cycle_reloads_config():
    from meridian import loop
    assert "config.reload_config()" in inspect.getsource(loop.daily_cycle)


# ---------- G3: rejim etiketleri tek kaynak ----------
def test_g3_valid_regimes_match_regime_module():
    emitted = {regime.TREND_UP, regime.TREND_DOWN, regime.CHOP, regime.HIGH_VOL}
    assert set(config.VALID_REGIMES) == emitted, \
        "config.VALID_REGIMES ile regime.py etiketleri ayrıştı → var@regime knob'ları sessizce ölür"


def test_g3b_default_strategy_has_a_map_per_regime():
    m = config.default_strategy()["params_by_regime"]
    assert set(m) == set(config.VALID_REGIMES) and all(v == {} for v in m.values())


# ---------- G4: override yeni knob icat edemez ----------
def test_g4_override_cannot_invent_a_knob():
    base = {"entry.min_score": 60, "stop_loss_atr_mult": 2.0}
    eff = config.resolve_params(base, {"chop": {"entry.min_score": 75, "uydurma_knob": 1}}, "chop")
    assert eff["entry.min_score"] == 75
    assert "uydurma_knob" not in eff, "override var olmayan bir knob'u YARATAMAZ"


def test_g4b_no_overrides_is_byte_identical():
    base = {"a": 1.0, "b": 2.0}
    assert config.resolve_params(base, None, "trend_up") == base
    assert config.resolve_params(base, {"trend_up": {}}, "trend_up") == base


def test_g4c_unknown_regime_leaves_base_untouched():
    base = {"a": 1.0}
    assert config.resolve_params(base, {"chop": {"a": 9.0}}, "risk_off") == base


# ---------- canlı kilit: paper varsayılanı ----------
def test_live_requires_both_flags(monkeypatch):
    monkeypatch.setattr(config, "MODE", "paper")
    monkeypatch.setattr(config, "I_ACCEPT_RISK", True)
    assert config.live_enabled() is False
    monkeypatch.setattr(config, "MODE", "live")
    monkeypatch.setattr(config, "I_ACCEPT_RISK", False)
    assert config.live_enabled() is False
