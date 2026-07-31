"""FMP stable-API adapter — base URL, query-style apikey auth, and the connection self-test. httpx is
mocked so these never touch the network."""
import pytest

from meridian.adapters import fmp
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



@pytest.fixture(autouse=True)
def _sandbox_all(sandbox_state):
    """Bu dosyadaki her test kum havuzunda koşar (2026-07-22, sızıntı bekçisi): FMP yolları her
    çağrıda `fmp_usage.json` (kota/429 telemetrisi) yazıyor ve fikstürsüz testler operatörün CANLI
    kota sayacını eziyordu."""
    fmp._KEY_BLOCKED.clear()                 # anahtar-başına 429 bloğu testler arası sızmasın
    yield
    fmp._KEY_BLOCKED.clear()


def _mock(monkeypatch, payload, capture=None, status=200):
    def fake_get(url, params=None, timeout=None):
        if capture is not None:
            capture["url"], capture["params"] = url, params
        return _Resp(payload, status)
    monkeypatch.setattr(fmp.httpx, "get", fake_get)


def test_quote_hits_stable_base_with_apikey_query(monkeypatch, sandbox_state):
    monkeypatch.setenv("FMP_API_KEY", "testkey12345678")
    secrets.clear_cache()
    cap = {}
    _mock(monkeypatch, [{"symbol": "AAPL", "price": 150.0}], cap)
    out = fmp.quote(["AAPL", "MSFT"])
    assert out and out[0]["symbol"] == "AAPL"
    assert cap["url"] == "https://financialmodelingprep.com/stable/quote"   # stable base, not /api/v3
    assert cap["params"]["symbol"] == "AAPL,MSFT"                            # query style, comma-joined
    assert cap["params"]["apikey"] == "testkey12345678"                     # key as a query param


def test_profile_and_income_use_symbol_query(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "k")
    secrets.clear_cache()
    cap = {}
    _mock(monkeypatch, [{"companyName": "Apple"}], cap)
    assert fmp.profile("AAPL")["companyName"] == "Apple"
    assert cap["url"].endswith("/stable/profile") and cap["params"]["symbol"] == "AAPL"


def test_ping_ok(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "k")
    secrets.clear_cache()
    _mock(monkeypatch, [{"symbol": "AAPL", "price": 199.5}])
    r = fmp.ping()
    assert r["ok"] is True and "199.5" in r["detail"]


def test_ping_reports_bad_key_on_401(monkeypatch):
    monkeypatch.setenv("FMP_API_KEY", "wrong")
    secrets.clear_cache()
    _mock(monkeypatch, {"Error Message": "Invalid API KEY"}, status=401)
    r = fmp.ping()
    assert r["ok"] is False and "geçersiz" in r["detail"]


def test_unavailable_without_key(sandbox_state):
    secrets.clear_cache()                     # sandbox has no secrets.json and no env key
    assert fmp.available() is False
    assert fmp.ping()["ok"] is False and "girilmemiş" in fmp.ping()["detail"]


# ---------- YEDEK ANAHTAR ROTASYONU (2026-07-23) ----------
def test_backup_key_rotates_in_on_primary_429(monkeypatch, sandbox_state):
    """Birincil 429 (kota) yeyince motor YEDEK anahtara geçmeli — 'çalışmıyor'un ana sebebi kota."""
    monkeypatch.setenv("FMP_API_KEY", "primary_dead")
    monkeypatch.setenv("FMP_API_KEY_2", "backup_live")
    secrets.clear_cache()
    fmp._KEY_BLOCKED.clear()
    seen = []

    def fake_get(url, params=None, timeout=None):
        seen.append(params["apikey"])
        if params["apikey"] == "primary_dead":
            return _Resp({"Error Message": "Limit Reach"}, status=429)
        return _Resp([{"symbol": "AAPL", "price": 150.0}], status=200)

    monkeypatch.setattr(fmp.httpx, "get", fake_get)
    out = fmp.quote(["AAPL"])
    assert out and out[0]["price"] == 150.0               # YEDEKTEN döndü
    assert seen == ["primary_dead", "backup_live"]        # önce birincil (429), sonra yedeğe rotasyon
    assert fmp._key_blocked("FMP_API_KEY") is True        # birincil kota-bloğunda
    assert fmp.quota_blocked() is False                   # yedek açık → 'tümü bloklu' DEĞİL


def test_quota_blocked_only_when_all_keys_exhausted(monkeypatch, sandbox_state):
    """Yedek açıkken quota_blocked False olmalı — bulk tüketici yedekle ilerlesin (kota ikiye katlandı)."""
    monkeypatch.setenv("FMP_API_KEY", "k1")
    monkeypatch.setenv("FMP_API_KEY_2", "k2")
    secrets.clear_cache()
    fmp._KEY_BLOCKED.clear()
    fmp._block_key("FMP_API_KEY")
    assert fmp.quota_blocked() is False                   # yedek hâlâ açık
    fmp._block_key("FMP_API_KEY_2")
    assert fmp.quota_blocked() is True                    # ikisi de bloklu → gerçekten kota doldu


def test_identical_backup_key_is_not_double_tried(monkeypatch, sandbox_state):
    """Operatör yanlışlıkla aynı anahtarı ikisine de girerse boş yere ikinci 429 çağrısı yapılmaz."""
    monkeypatch.setenv("FMP_API_KEY", "same")
    monkeypatch.setenv("FMP_API_KEY_2", "same")
    secrets.clear_cache()
    fmp._KEY_BLOCKED.clear()
    n = []

    def fake_get(url, params=None, timeout=None):
        n.append(1)
        return _Resp({"Error Message": "Limit"}, status=429)

    monkeypatch.setattr(fmp.httpx, "get", fake_get)
    with pytest.raises(Exception):
        fmp._get("quote", {"symbol": "AAPL"})
    assert len(n) == 1                                    # aynı değer iki kez DENENMEDİ (dedup)


def test_backup_ping_targets_the_backup_key(monkeypatch, sandbox_state):
    """Ayarlar'daki yedek 'Test et' YALNIZ yedek anahtarı doğrular (rotasyon yok)."""
    monkeypatch.setenv("FMP_API_KEY", "primary")
    monkeypatch.setenv("FMP_API_KEY_2", "backup")
    secrets.clear_cache()
    fmp._KEY_BLOCKED.clear()
    used = {}

    def fake_get(url, params=None, timeout=None):
        used["apikey"] = params["apikey"]
        return _Resp([{"symbol": "AAPL", "price": 1.0}], status=200)

    monkeypatch.setattr(fmp.httpx, "get", fake_get)
    r = fmp.ping(which="FMP_API_KEY_2")
    assert r["ok"] is True and used["apikey"] == "backup"   # birincil değil, YEDEK test edildi
