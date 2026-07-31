"""test_api_intraday_wiring_v91.py — Faz 4 kablolama: intraday_cycle barfeed'e start()'tan ÖNCE register."""
import pytest

from meridian import api, marketstream as mk, barfeed as bf, intraday_cycle as ic
from meridian.adapters import alpaca


@pytest.fixture(autouse=True)
def _reset(sandbox_state, monkeypatch):
    ic._CONSUMER = None
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(api.secrets_mod, "present", lambda n: True)
    monkeypatch.setenv("MERIDIAN_MARKET_STREAM", "1")
    monkeypatch.setenv("MERIDIAN_MIRROR_STREAM", "0")     # ayna görevini kurma (test izolasyonu)
    monkeypatch.setattr(mk, "start", lambda *a, **k: None)
    yield
    bf.stop()
    ic._CONSUMER = None
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    bf._CONSUMER = None
    bf._THREAD = None


def test_intraday_registered_before_barfeed_start(monkeypatch):
    order = []
    monkeypatch.setattr(bf, "register", lambda cb: order.append("register"))
    monkeypatch.setattr(bf, "start", lambda *a, **k: order.append("bf_start"))
    monkeypatch.setenv("MERIDIAN_INTRADAY", "1")
    api._autostart()
    assert "register" in order and "bf_start" in order
    assert order.index("register") < order.index("bf_start")   # register ÖNCE (kayıp-olay penceresi kapalı)


def test_intraday_disabled_not_registered(monkeypatch):
    order = []
    monkeypatch.setattr(bf, "register", lambda cb: order.append("register"))
    monkeypatch.setattr(bf, "start", lambda *a, **k: order.append("bf_start"))
    monkeypatch.setenv("MERIDIAN_INTRADAY", "0")           # kapalı
    api._autostart()
    assert "register" not in order and "bf_start" in order  # barfeed yine başlar, register YOK


def test_diagnostics_exposes_intraday_health():
    """KANONİK YÜZEY /api/diagnostics (K1, 2026-07-30 — bu test eskiden /api/hermes'i sorguyordu).

    NEDEN TAŞINDI: aynı gerçek İKİ uçtan servis ediliyordu ve panonun intraday paneli verisini
    /api/diagnostics'ten alıyordu — /api/hermes'teki kopya HİÇ okunmuyordu. api.py'nin kendi kuralı:
    "iki uç aynı alanı farklı şekilde servis edemez". Kopya emekli edildi; KAPSAM KAYBOLMADI, bu
    test kanonik yüzeyi çiviliyor (kardeş dosya test_api_marketstream_wiring_v84 aynı deseni
    2026'dan beri böyle kuruyordu: hermes değil diagnostics)."""
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    d = c.get("/api/diagnostics").json()
    assert "intraday" in d
    for k in ("ok", "armed", "mode", "decisions_written", "enabled"):
        assert k in d["intraday"]
    assert d["intraday"]["mode"] == "observe"    # default gözlem


def test_hermes_yuku_intraday_kopyasini_SERVIS_ETMEZ():
    """EMEKLİLİK MUHAFIZI: ölü kopya sessizce geri dönerse iki yüzey yeniden ayrışmaya başlar
    (aynı sınıf: guard.check_trade'in "iki yüzey sessizce ayrıştı" dersi). Kopya geri gelirse
    burada patlar."""
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    d = c.get("/api/hermes").json()
    assert "intraday" not in d, \
        "/api/hermes intraday sağlığını yine servis ediyor — kanonik kaynak /api/diagnostics"
