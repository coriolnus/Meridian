"""test_marketstream_v84.py — piyasa-verisi dinleyicisi (Faz 2, 2026-07-23).

Ortak yasa (backoff/nabız/reconnect/down-saati) streamhealth'te kilitli (test_streamhealth_*). Burada
YALNIZ emre-özgü: batched-array parse, LOOK-AHEAD (yalnız `b`/`bars`), D2 alive yasası, host/feed,
singleton, üçüncü-hâl, yapısal sınırlar (emir/disk yolu YOK).
"""
import asyncio
import inspect
import json

import pytest

from meridian import marketstream as mk


@pytest.fixture(autouse=True)
def _reset_singleton():
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None
    yield
    mk._LISTENER = None
    mk._TASK = None
    mk.STATE = None


class FakeWS:
    """async-iterable sahte websocket: verilen frame'leri sırayla verir, gönderilenleri yakalar."""

    def __init__(self, frames):
        self.frames = frames
        self.sent = []

    async def send(self, data):
        self.sent.append(data)

    def __aiter__(self):
        async def _gen():
            for f in self.frames:
                yield f
        return _gen()


def _drive(listener, frames, monkeypatch):
    got = []
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: (got.append(dict(b)), len(b))[1])
    alive = []
    ws = FakeWS(frames)
    asyncio.run(listener.session(ws, lambda: alive.append(1)))
    return ws, got, alive


def test_batched_array_only_b_bars_ingested(sandbox_state, monkeypatch):
    """Bir WS frame'i BİRDEN ÇOK karışık mesaj taşır. Yalnız `b` (kapanmış bar) ingest edilir;
    `t`/`q`/`u`/`d` (tick/quote/düzeltme/forming-günlük) LOOK-AHEAD gereği YOK SAYILIR."""
    lis = mk.MarketStreamListener()
    frames = [json.dumps([
        {"T": "success", "msg": "authenticated"},
        {"T": "subscription", "bars": ["AAPL"]},
        {"T": "b", "S": "AAPL", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 100, "vw": 1.4, "n": 9,
         "t": "2026-07-23T13:45:00Z"},
        {"T": "b", "S": "MSFT", "o": 3, "h": 4, "l": 2, "c": 3.5, "v": 200, "vw": 3.4, "n": 8,
         "t": "2026-07-23T13:45:00Z"},
        {"T": "t", "S": "AAPL", "p": 1.51},   # tick → YOK SAYILIR
        {"T": "q", "S": "AAPL", "bp": 1.5},   # quote → YOK SAYILIR
        {"T": "u", "S": "AAPL", "c": 1.6},    # düzeltilmiş bar → YOK SAYILIR
        {"T": "d", "S": "AAPL", "c": 1.7},    # forming günlük → YOK SAYILIR
    ])]
    _ws, got, alive = _drive(lis, frames, monkeypatch)
    assert len(got) == 1
    ingested = got[0]
    assert set(ingested.keys()) == {"AAPL", "MSFT"}    # yalnız b'ler
    assert ingested["AAPL"]["c"] == 1.5 and ingested["AAPL"]["t"] == "2026-07-23T13:45:00Z"
    assert alive                                        # authenticated/subscription/b → alive
    assert lis.state.bars_seen == 2


def test_subscribe_payload_is_bars_only(sandbox_state):
    """LOOK-AHEAD KİLİDİ: abonelik YALNIZ `bars`; forming/tick kanalları ASLA."""
    lis = mk.MarketStreamListener()
    sent = []

    class WS:
        async def send(self, d):
            sent.append(json.loads(d))

        def __aiter__(self):
            async def _g():
                if False:
                    yield
            return _g()

    asyncio.run(lis.session(WS(), lambda: None))
    subs = [m for m in sent if m.get("action") == "subscribe"]
    assert subs and "bars" in subs[0]
    for forbidden in ("quotes", "trades", "updatedBars", "dailyBars"):
        assert forbidden not in subs[0], f"look-ahead ihlali: {forbidden} kanalına abone olunmamalı"


def test_d2_connected_before_auth_does_not_mark_alive(sandbox_state, monkeypatch):
    """D2: `success/connected` (auth ÖNCESİ) alive YAPMAZ — kabul edilip kapanan soket 'canlı'
    okunmasın (v68 kusuru). Yalnız `authenticated`/`subscription`/`b` alive yapar."""
    lis = mk.MarketStreamListener()
    _, _, alive = _drive(lis, [json.dumps([{"T": "success", "msg": "connected"}])], monkeypatch)
    assert not alive
    lis2 = mk.MarketStreamListener()
    _, _, alive2 = _drive(lis2, [json.dumps([{"T": "success", "msg": "authenticated"}])], monkeypatch)
    assert alive2


def test_url_per_feed(sandbox_state, monkeypatch):
    monkeypatch.setattr(mk, "FEED", "iex")
    assert mk.MarketStreamListener._url() == "wss://stream.data.alpaca.markets/v2/iex"
    monkeypatch.setattr(mk, "FEED", "bogus")
    assert mk.MarketStreamListener._url() == "wss://stream.data.alpaca.markets/v2/iex"   # bilinmeyen → iex


def test_singleton_listener_identity(sandbox_state):
    assert mk.listener() is mk.listener()


def test_third_state_health_when_never_run():
    """Dinleyici HİÇ koşmamışsa health()['ok'] None — 'unknown ≠ broken' (pano '—' der, 'KOPUK' değil)."""
    assert mk.health()["ok"] is None


def test_auth_error_throttles_and_ends_session(sandbox_state, monkeypatch):
    """#3 fix (çekişmeli inceleme): auth hatası (402) → 300s bekle + oturumu bitir. Yanlış anahtarla
    Alpaca'yı ≤60s'te dövmek yok; hatadan sonraki bar da işlenmez (oturum döndü)."""
    lis = mk.MarketStreamListener()
    paused = []

    async def fake_pause(s):
        paused.append(s)

    monkeypatch.setattr(mk, "_pause", fake_pause)
    monkeypatch.setattr(mk.obs, "warn", lambda *a, **k: None)
    got = []
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: got.append(b) or len(b))
    frames = [json.dumps([{"T": "error", "code": 402, "msg": "auth failed"},
                          {"T": "b", "S": "AAPL", "c": 1, "t": "2026-07-23T13:45:00Z"}])]
    asyncio.run(lis.session(FakeWS(frames), lambda: None))
    assert 300 in paused        # auth throttle
    assert not got              # error'dan SONRAKİ bar işlenmedi (session return etti)


def test_on_error_maps_codes_to_events(sandbox_state, monkeypatch):
    lis = mk.MarketStreamListener()
    events = []
    monkeypatch.setattr(mk.obs, "warn", lambda ev, **k: events.append(ev))
    lis._on_error({"code": 406})
    lis._on_error({"code": 402})
    lis._on_error({"code": 409})
    assert events == ["marketstream_conn_limit", "marketstream_unauthorized",
                      "marketstream_subscription_limited"]


def test_structural_no_order_or_disk_paths():
    """Veri katmanı emir gönderemez / disk defteri yazamaz (UÇUCU). Kaynakta bu yollar GEÇMEZ."""
    src = inspect.getsource(mk)
    for forbidden in ("submit_plan", "httpx", "close_all", "cancel_open_entries",
                      "close_engine_position", "replace_order_stop", "cancel_order",
                      "write_json", "write_jsonl", "append_jsonl", "write_text"):
        assert forbidden not in src, f"marketstream '{forbidden}' içeremez (emir/disk yolu yok)"
