"""Alpaca paper adapter — the read-only connection self-test. httpx mocked (no network). The live
ORDER path is not exercised here; ping() only reads /v2/account and never arms an order."""
import pytest

from meridian.adapters import alpaca
from meridian import secrets


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._p


def _mock(monkeypatch, payload, capture=None, status=200):
    def fake_get(url, timeout=None, headers=None):
        if capture is not None:
            capture["url"], capture["headers"] = url, headers
        return _Resp(payload, status)
    monkeypatch.setattr(alpaca.httpx, "get", fake_get)


def _both_keys(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_KEY", "PKtestid")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "secretval")
    secrets.clear_cache()


def test_ping_hits_paper_account_with_headers(sandbox_state, monkeypatch):
    _both_keys(monkeypatch)
    cap = {}
    _mock(monkeypatch, {"status": "ACTIVE"}, cap)
    r = alpaca.ping()
    assert r["ok"] is True and "ACTIVE" in r["detail"]
    assert cap["url"] == "https://paper-api.alpaca.markets/v2/account"     # paper endpoint, read-only
    assert cap["headers"]["APCA-API-KEY-ID"] == "PKtestid"
    assert cap["headers"]["APCA-API-SECRET-KEY"] == "secretval"


def test_ping_key_only_uses_bearer(sandbox_state, monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_KEY", "PKonlykey")   # no secret — operator's "endpoint + key" case
    secrets.clear_cache()
    cap = {}
    _mock(monkeypatch, {"status": "ACTIVE"}, cap)
    assert alpaca.ping()["ok"] is True
    assert cap["headers"] == {"Authorization": "Bearer PKonlykey"}         # falls back to Bearer


def test_endpoint_with_v2_is_not_doubled(sandbox_state, monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_KEY", "PK")
    monkeypatch.setenv("ALPACA_PAPER_ENDPOINT", "https://paper-api.alpaca.markets/v2")  # already has /v2
    secrets.clear_cache()
    cap = {}
    _mock(monkeypatch, {"status": "ACTIVE"}, cap)
    alpaca.ping()
    assert cap["url"] == "https://paper-api.alpaca.markets/v2/account"     # NOT /v2/v2/account


def test_ping_reports_bad_key_on_401(sandbox_state, monkeypatch):
    _both_keys(monkeypatch)
    _mock(monkeypatch, {"message": "forbidden"}, status=401)
    r = alpaca.ping()
    assert r["ok"] is False and "geçersiz" in r["detail"]


def test_ping_unavailable_without_keys(sandbox_state):
    secrets.clear_cache()
    assert alpaca.paper_available() is False
    assert alpaca.ping()["ok"] is False and "girilmemiş" in alpaca.ping()["detail"]
