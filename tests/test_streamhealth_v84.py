"""test_streamhealth_v84.py — çıkarılan ORTAK yasa, İZOLE (Faz 2, 2026-07-23).

StreamHealth'i sahte `persist` ile sürer. mirror ve market AYNI yasadan koştuğu için buradaki her
kilit İKİSİNİ birden korur — 54→2 down kusuru bu durumsal yasada yaşadı, tek yerde kilitleniyor.
"""
import time

from meridian import streamhealth as sh


def _sh():
    return sh.StreamHealth("test", "rol", persist=lambda: None)


def test_set_stream_edge_dedup(monkeypatch):
    """set_stream KENARDIR: aynı 'down' durumu ikinci kez `test_down` KAYDI basmaz (kesintinin
    süregelen görünürlüğü touch()'un işi). Up bir kez `test_up` loglar."""
    events = []
    monkeypatch.setattr(sh.obs, "warn", lambda ev, **k: events.append(("warn", ev)))
    monkeypatch.setattr(sh.obs, "log", lambda ev, **k: events.append(("log", ev)))
    h = _sh()
    h.set_stream(False, "boom")
    h.set_stream(False, "boom")
    assert [e for e in events if e == ("warn", "test_down")] == [("warn", "test_down")]  # tek kenar
    h.set_stream(True)
    assert ("log", "test_up") in events


def test_touch_reassert_after_interval(monkeypatch):
    """touch NABIZDIR: kopuş sürerken DOWN_REASSERT_S geçince `test_down` YENİDEN basar (True döner)."""
    monkeypatch.setattr(sh.obs, "warn", lambda *a, **k: None)
    h = _sh()
    h.set_stream(False, "boom")
    h._last_reassert = time.monotonic() - (sh.DOWN_REASSERT_S + 1)
    assert h.touch() is True
    h._last_reassert = time.monotonic()
    assert h.touch() is False


def test_hydrate_rejects_stale_flag(monkeypatch):
    """v68 yasası: taze nabız yoksa diskteki `stream_ok:true` dirilmez (false'a çekilir)."""
    monkeypatch.setattr(sh.obs, "warn", lambda *a, **k: None)
    h = _sh()
    h.hydrate({"stream_ok": True, "stream_checked_at": "2020-01-01T00:00:00+00:00"})
    assert h.stream_ok is False


def test_hydrate_keeps_fresh_flag():
    h = _sh()
    h.hydrate({"stream_ok": True, "stream_checked_at": sh._now_iso()})
    assert h.stream_ok is True


def test_hydrate_decay_does_not_immediately_reassert(monkeypatch):
    """#6 fix (çekişmeli inceleme): bayat-bayrak decay'inden sonra İLK touch() sahte `_down` (down_for_s=0)
    basmamalı. `_last_reassert` decay'de tohumlandığı için hemen 'due' olmaz — kurt masalı önlendi."""
    monkeypatch.setattr(sh.obs, "warn", lambda *a, **k: None)
    h = _sh()
    h.hydrate({"stream_ok": True, "stream_checked_at": "2020-01-01T00:00:00+00:00"})
    assert h.stream_ok is False
    assert h.touch() is False        # HEMEN reassert etmez (bağlantı gelmeden sahte down yok)


def test_health_snapshot_multiplies_by_heartbeat():
    assert sh.health_snapshot({"stream_ok": True, "stream_checked_at": sh._now_iso()})["ok"] is True
    stale = {"stream_ok": True, "stream_checked_at": "2020-01-01T00:00:00+00:00"}
    assert sh.health_snapshot(stale)["ok"] is False   # bayrak true ama nabız bayat → ok False


def test_decay_stale_flag(monkeypatch):
    monkeypatch.setattr(sh.obs, "warn", lambda *a, **k: None)
    changed, new = sh.decay_stale_flag(
        {"stream_ok": True, "stream_checked_at": "2020-01-01T00:00:00+00:00"}, "test")
    assert changed and new["stream_ok"] is False
    changed2, _ = sh.decay_stale_flag({"stream_ok": True, "stream_checked_at": sh._now_iso()}, "test")
    assert changed2 is False


def test_next_backoff_and_dns_floor():
    assert sh.next_backoff(1.0) == 2.0
    assert sh.next_backoff(40.0) == sh.BACKOFF_MAX
    assert sh.next_backoff(1.0, "gaierror: getaddrinfo failed") >= sh.DNS_BACKOFF_FLOOR


def test_next_backoff_positive_control():
    """POZİTİF kontrol: DNS-DIŞI hata floor UYGULAMAZ — test kör değil."""
    assert sh.next_backoff(1.0, "ConnectionClosed") == 2.0


def test_noop_persist_writes_nothing_and_does_not_raise(monkeypatch):
    """Market modu: persist=no-op → set_stream/touch DİSK yazmaz ve istisna atmaz (uçucu yol)."""
    monkeypatch.setattr(sh.obs, "warn", lambda *a, **k: None)
    monkeypatch.setattr(sh.obs, "log", lambda *a, **k: None)
    h = sh.StreamHealth("m", "rol", persist=lambda: None)
    h.set_stream(True)
    h.touch()
    h.set_stream(False, "x")


def test_identical_structural_fields_for_both_prefixes():
    """Yasa TEK: iki prefix ÖZDEŞ yapısal alan üretir; yalnız olay adı (prefix) ve rol metni farklı."""
    a = sh.StreamHealth("mirror_stream", "yürütme", persist=lambda: None)
    b = sh.StreamHealth("marketstream", "piyasa verisi", persist=lambda: None)
    assert set(a.to_dict()) == set(b.to_dict())
