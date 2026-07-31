"""Secret entry surface — the operator pastes keys through the dashboard. These lock the security
contract: whitelist-only writes, env precedence, 0600 file perms, masked-only status (never a full
value), and that setting data/paper keys does NOT flip any live/autonomy flag."""
import os
import shutil
import stat
from pathlib import Path

import pytest

from meridian import secrets, config


def _seed_goal(sandbox):
    """Copy the real immutable goal.yaml/bounds.yaml into a sandbox so config.goal()/limits() work."""
    real = Path(config.__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy(real / f, sandbox / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()


def test_set_get_delete_roundtrip(sandbox_state):
    secrets.clear_cache()
    assert secrets.get("FMP_API_KEY") is None
    secrets.set("FMP_API_KEY", "fmp_live_1234567890")
    assert secrets.get("FMP_API_KEY") == "fmp_live_1234567890"
    secrets.delete("FMP_API_KEY")
    assert secrets.get("FMP_API_KEY") is None


def test_whitelist_blocks_arbitrary_names(sandbox_state):
    for bad in ("PATH", "MERIDIAN_MODE", "MERIDIAN_I_ACCEPT_RISK", "autonomy_level"):
        with pytest.raises(ValueError):
            secrets.set(bad, "x")


def test_env_takes_precedence_over_file(sandbox_state, monkeypatch):
    secrets.clear_cache()
    secrets.set("FMP_API_KEY", "from_file")
    monkeypatch.setenv("FMP_API_KEY", "from_env")
    secrets.clear_cache()
    assert secrets.get("FMP_API_KEY") == "from_env"          # env wins
    assert secrets.status()["FMP_API_KEY"]["source"] == "env"


def test_file_is_chmod_0600(sandbox_state):
    secrets.set("HERMES_API_KEY", "sk-ant-verysecretvalue")
    mode = stat.S_IMODE(os.stat(secrets._path()).st_mode)
    assert mode == 0o600                                     # owner read/write only


def test_status_is_masked_never_full(sandbox_state):
    secrets.clear_cache()
    secrets.set("FMP_API_KEY", "abcdefghij0000wxyz")
    st = secrets.status()["FMP_API_KEY"]
    assert st["set"] is True and st["source"] == "file"
    assert st["hint"] == "••••wxyz"                          # only last 4, masked
    assert "abcdefghij" not in str(st)                       # the real value never appears
    # short values reveal nothing at all
    secrets.set("TELEGRAM_CHAT_ID", "12345")
    assert secrets.status()["TELEGRAM_CHAT_ID"]["hint"] == "••••"


def test_empty_value_clears(sandbox_state):
    secrets.set("MERIDIAN_WEBHOOK_URL", "https://x")
    secrets.set("MERIDIAN_WEBHOOK_URL", "   ")               # blank -> clear
    assert secrets.get("MERIDIAN_WEBHOOK_URL") is None


# ---------------- HTTP surface ----------------
def _client():
    from fastapi.testclient import TestClient
    from meridian.api import app
    return TestClient(app)


def test_endpoint_rejects_unknown_name(sandbox_state):
    c = _client()
    r = c.post("/api/secrets/PATH", json={"value": "/evil"})
    assert r.status_code == 400
    assert "PATH" not in secrets._read_file()                 # never written to the store


def test_endpoint_sets_and_status_masks(sandbox_state):
    _seed_goal(sandbox_state)
    c = _client()
    r = c.post("/api/secrets/FMP_API_KEY", json={"value": "fmp_secret_abcd1234"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["status"]["set"] and body["status"]["hint"] == "••••1234"
    assert "fmp_secret" not in r.text                          # response never echoes the value
    # GET status is masked too
    g = c.get("/api/secrets").json()
    assert g["secrets"]["FMP_API_KEY"]["hint"] == "••••1234"
    assert g["live_enabled"] is False and g["autonomy_level"] == 0   # setting a key did NOT flip live


def test_endpoint_missing_value_is_400(sandbox_state):
    c = _client()
    assert c.post("/api/secrets/FMP_API_KEY", json={}).status_code == 400
    assert c.post("/api/secrets/FMP_API_KEY", json={"value": "  "}).status_code == 400
