"""test_secrets_audit_v41.py — secrets denetimi (2026-07-21, tur 28).

Sistemdeki tüm anahtarların tek kapısı. 7. soru:
  SE1 "yalnız ALLOWED yazılabilir" → panodan gelen bir POST'un PATH/MERIDIAN_MODE gibi bir adı
     ekleyememesi güvenliğin temeli; testi vardı ama sınır davranışları (silme, boş değer) yoktu
  SE2 "dosya 0600'dür" → YAZARKEN uyguluyorduk, OKURKEN hiç bakmıyorduk: kopyalama/geri yükleme
     sonrası dünyaya açık bir sır dosyası sessizce kullanılmaya devam ederdi
  SE3 "değer asla loglanmaz" → repo genelinde statik kontrol (bir gün biri f-string'e koyarsa kırılsın)
  SE4 "env dosyayı ezer" → sıralama sözleşmesi
"""
from __future__ import annotations

import os
import pathlib
import re

import pytest

from meridian import secrets, store


@pytest.fixture(autouse=True)
def _fresh(sandbox_state, monkeypatch):
    secrets.clear_cache()
    secrets._PERM_WARNED = False
    for n in list(secrets.ALLOWED):
        monkeypatch.delenv(n, raising=False)
    yield
    secrets.clear_cache()


# ---------- SE1: yazma izin listesi ----------
def test_se1_only_allowed_names_are_writable():
    with pytest.raises(ValueError):
        secrets.set("PATH", "/evil")
    with pytest.raises(ValueError):
        secrets.set("MERIDIAN_MODE", "live")          # canlı moda pano üzerinden geçilemez
    with pytest.raises(ValueError):
        secrets.delete("MERIDIAN_I_ACCEPT_RISK")
    secrets.set("FMP_API_KEY", "abc12345678")
    assert secrets.get("FMP_API_KEY") == "abc12345678"


def test_se1b_empty_value_clears_and_delete_is_idempotent():
    secrets.set("FMP_API_KEY", "abc12345678")
    secrets.set("FMP_API_KEY", "")
    assert secrets.get("FMP_API_KEY") is None
    secrets.delete("FMP_API_KEY")                     # yoksa da patlamaz
    assert secrets.present("FMP_API_KEY") is False


def test_se1c_execution_flags_are_not_in_the_allowlist():
    for forbidden in ("MERIDIAN_MODE", "MERIDIAN_I_ACCEPT_RISK", "MERIDIAN_BROKER",
                      "PATH", "autonomy_level"):
        assert forbidden not in secrets.ALLOWED


# ---------- SE2: dosya izinleri ----------
def test_se2_written_file_is_owner_only():
    secrets.set("FMP_API_KEY", "abc12345678")
    mode = (secrets._path().stat().st_mode & 0o777)
    assert mode == 0o600, f"sır dosyası izni {oct(mode)}"


def test_se2b_loose_permissions_are_reported_once(sandbox_state):
    secrets.set("FMP_API_KEY", "abc12345678")
    os.chmod(secrets._path(), 0o644)                  # kopyalama/geri yükleme sonrası tipik hal
    secrets.clear_cache(); secrets._PERM_WARNED = False
    secrets.get("FMP_API_KEY")
    secrets.clear_cache(); secrets.get("FMP_API_KEY")
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "secrets_file_permissions"]
    assert len(ev) == 1 and "644" in ev[0]["mode"]    # bir kez uyarır, sonra susar
    assert secrets.get("FMP_API_KEY") == "abc12345678"   # ama ÇALIŞMAYI engellemez


# ---------- SE3: değer asla loglanmıyor ----------
def test_se3_no_module_interpolates_a_secret_into_a_log():
    """Statik güvenlik ağı: bir gün biri obs.log(f"key={secrets.get('X')}") yazarsa burada patlasın."""
    root = pathlib.Path("meridian")
    bad = []
    pat = re.compile(r"(obs\.(log|warn|alarm)|print|console\.print)\([^)]*secrets\.get\(", re.S)
    for f in root.rglob("*.py"):
        if pat.search(f.read_text()):
            bad.append(str(f))
    assert not bad, f"sır değeri doğrudan loga gidiyor olabilir: {bad}"


def test_se3b_mask_never_returns_the_full_value():
    assert secrets.mask("abcdefghijkl") == "••••ijkl"
    assert secrets.mask("short") == "••••"            # kısa sır tamamen gizlenir
    assert secrets.mask(None) is None


def test_se3c_status_exposes_only_hints():
    secrets.set("FMP_API_KEY", "abcdefghijkl")
    st = secrets.status()["FMP_API_KEY"]
    assert st["set"] is True and st["source"] == "file" and st["hint"] == "••••ijkl"
    assert "abcdefghijkl" not in str(secrets.status())


# ---------- SE4: kaynak sırası ----------
def test_se4_env_beats_the_file(monkeypatch):
    secrets.set("FMP_API_KEY", "dosyadan")
    monkeypatch.setenv("FMP_API_KEY", "envden")
    secrets.clear_cache()
    assert secrets.get("FMP_API_KEY") == "envden"
    assert secrets.status()["FMP_API_KEY"]["source"] == "env"


def test_se4b_cache_is_cleared_on_write():
    secrets.set("FMP_API_KEY", "eski12345678")
    assert secrets.get("FMP_API_KEY") == "eski12345678"
    secrets.set("FMP_API_KEY", "yeni12345678")
    assert secrets.get("FMP_API_KEY") == "yeni12345678", "rotasyon TTL boyunca görünmez kalıyor"
