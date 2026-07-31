"""test_barfeed_v85.py — DAYANIKLI bar-tetiği tüketicisi (Faz 3, 2026-07-23).

Consumer LOGIC'i (dispatch/ACK/idempotent/üçüncü-hâl) sahte hotstate ile sürer — gerçek Redis gerekmez.
Redis primitiflerinin roundtrip'i test_hotstate_bars_v84.py'de (gerçek Redis).
"""
import pytest

from meridian import barfeed as bf


@pytest.fixture(autouse=True)
def _reset():
    bf._CONSUMER = None
    bf._THREAD = None
    yield
    bf.stop()
    bf._CONSUMER = None
    bf._THREAD = None


def test_consumer_dispatches_to_callback_and_acks(monkeypatch):
    """Yeni-bar olayı → kayıtlı geri-çağrı çağrılır, sonra olay ACK'lenir (restart'ta yeniden teslim yok)."""
    c = bf.consumer()
    got = []
    c.register(lambda fields: got.append(fields))
    monkeypatch.setattr(bf.hotstate, "ensure_barfeed_group", lambda g: True)
    calls = {"n": 0}

    def fake_read(g, cons, count=50, block_ms=2000):
        calls["n"] += 1
        if calls["n"] == 1:
            return [("1-0", {"ts": "t", "n": "3", "syms": "AAPL,MSFT,NVDA"})]
        c.stop()
        return []

    monkeypatch.setattr(bf.hotstate, "read_barfeed", fake_read)
    acked = []
    monkeypatch.setattr(bf.hotstate, "ack_barfeed", lambda g, ids: (acked.append(list(ids)), len(ids))[1])
    c.run()      # senkron; ikinci read'te stop → döngü biter
    assert got == [{"ts": "t", "n": "3", "syms": "AAPL,MSFT,NVDA"}]
    assert c.events_read == 1 and c.frames_seen == 3
    assert acked == [["1-0"]]


def test_callback_error_still_acks_no_redelivery_lock(monkeypatch):
    """Geri-çağrı patlasa da olay ACK'lenir (sonsuz yeniden-teslim kilidi yok); hata kaydedilir."""
    c = bf.consumer()
    c.register(lambda f: (_ for _ in ()).throw(ValueError("boom")))
    monkeypatch.setattr(bf.hotstate, "ensure_barfeed_group", lambda g: True)
    monkeypatch.setattr(bf.obs, "warn", lambda *a, **k: None)
    calls = {"n": 0}

    def fake_read(g, cons, count=50, block_ms=2000):
        calls["n"] += 1
        if calls["n"] == 1:
            return [("1-0", {"n": "1"})]
        c.stop()
        return []

    monkeypatch.setattr(bf.hotstate, "read_barfeed", fake_read)
    acked = []
    monkeypatch.setattr(bf.hotstate, "ack_barfeed", lambda g, ids: acked.append(list(ids)))
    c.run()
    assert acked == [["1-0"]] and c.last_error       # ACK yine yapıldı, hata görünür


def test_redis_down_is_graceful(monkeypatch):
    """read_barfeed None (Redis down) → tüketici DURMAZ, nazikçe bekleyip grup kurmayı dener."""
    c = bf.consumer()
    monkeypatch.setattr(bf.hotstate, "ensure_barfeed_group", lambda g: False)
    calls = {"n": 0}

    def fake_read(g, cons, count=50, block_ms=2000):
        calls["n"] += 1
        c.stop()
        return None       # Redis down

    monkeypatch.setattr(bf.hotstate, "read_barfeed", fake_read)
    monkeypatch.setattr(c._stop, "wait", lambda s: None)   # beklemeyi hızlandır
    c.run()               # istisna ATMAMALI
    assert calls["n"] >= 1


def test_health_third_state_when_never_started():
    assert bf.health()["ok"] is None     # hiç başlamadı → unknown ≠ broken


def test_start_is_idempotent(monkeypatch):
    monkeypatch.setattr(bf.BarfeedConsumer, "run", lambda self: self._stop.wait(5))
    t1 = bf.start()
    t2 = bf.start()
    assert t1 is t2                        # ikinci start YENİ thread yaratmaz (çift tüketici yok)
    bf.stop()
    t1.join(timeout=2)
