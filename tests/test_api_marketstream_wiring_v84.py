"""test_api_marketstream_wiring_v84.py — /api/hermes marketstream anahtarı + autostart kapısı (Faz 2)."""
import pytest
from fastapi.testclient import TestClient

from meridian import api, marketstream as mk, barfeed as bf
from meridian.adapters import alpaca


@pytest.fixture(autouse=True)
def _reset(sandbox_state):
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    yield
    bf.stop()                    # _autostart barfeed thread'i başlatmış olabilir — sızmasın
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    bf._CONSUMER = None
    bf._THREAD = None


def test_hermes_yuku_marketstream_kopyasini_SERVIS_ETMEZ():
    """EMEKLİLİK MUHAFIZI (K1, 2026-07-30): bu test eskiden /api/hermes'in marketstream sağlığını
    servis ettiğini çiviliyordu. Ama HEMEN AŞAĞIDAKİ test aynı gerçeği /api/diagnostics'te de
    çiviliyordu — yani iki uç aynı alanı servis ediyor, biri (hermes) panoda HİÇ okunmuyordu.
    Kopya emekli edildi; alan sözleşmesi aşağıdaki kanonik testte AYNEN duruyor.
    Bu muhafız, kopyanın sessizce geri gelmesini engeller."""
    c = TestClient(api.app)
    d = c.get("/api/hermes").json()
    assert "marketstream" not in d, \
        "/api/hermes marketstream sağlığını yine servis ediyor — kanonik kaynak /api/diagnostics"


def test_diagnostics_marketstream_alan_sozlesmesi():
    """Kanonik yüzeyin ALAN sözleşmesi — emekli edilen hermes testinden buraya taşındı."""
    c = TestClient(api.app)
    ms = c.get("/api/diagnostics").json()["marketstream"]
    for k in ("ok", "alive", "feed", "bars_seen", "down_since"):
        assert k in ms
    assert ms["ok"] is None       # koşmadı → üçüncü hâl


def test_diagnostics_exposes_marketstream_health():
    c = TestClient(api.app)
    d = c.get("/api/diagnostics").json()
    assert "marketstream" in d and "ok" in d["marketstream"]


def test_autostart_gate_no_paper_does_not_start(monkeypatch):
    called = []
    monkeypatch.setattr(mk, "start", lambda *a, **k: called.append(1))
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    api._autostart()
    assert not called             # paper yok → marketstream.start ÇAĞRILMAZ


def test_autostart_gate_starts_when_paper_and_secret(monkeypatch):
    called = []
    monkeypatch.setattr(mk, "start", lambda *a, **k: called.append(1))
    monkeypatch.setattr(bf, "start", lambda *a, **k: called.append("barfeed"))   # gerçek thread SPAWN etme
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(api.secrets_mod, "present", lambda n: True)
    monkeypatch.setenv("MERIDIAN_MARKET_STREAM", "1")
    monkeypatch.setenv("MERIDIAN_MIRROR_STREAM", "0")                             # ayna görevini de kurma
    api._autostart()
    assert 1 in called and "barfeed" in called   # paper + secret + bayrak → marketstream + barfeed başlar


def test_autostart_gate_flag_off_does_not_start(monkeypatch):
    called = []
    monkeypatch.setattr(mk, "start", lambda *a, **k: called.append(1))
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(api.secrets_mod, "present", lambda n: True)
    monkeypatch.setenv("MERIDIAN_MARKET_STREAM", "0")
    api._autostart()
    assert not called             # MERIDIAN_MARKET_STREAM=0 → kapalı
