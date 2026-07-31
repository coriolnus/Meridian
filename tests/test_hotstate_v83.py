"""test_hotstate_v83.py — Redis SICAK-DURUM katmanı (intraday, 2026-07-23).

İki ilke kilitli:
  1. GRACEFUL DEGRADATION — Redis yoksa/çökse okuma None (çağıran dosyaya düşer), yazma no-op,
     down durumu görünür. Sistem ASLA durmaz; kalıcı gerçek dosyada olduğu için kayıp da yok.
  2. DENETLENEBİLİRLİK KORUNUR — hotstate UÇUCU türev tutar; KALICI gerçeği (store.write_*) ASLA
     yazmaz. Yoksa Redis, dedektörlerin okuyamadığı bir yere kalıcı veri kaçırırdı.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from meridian import hotstate as hs

SRC = Path(__file__).resolve().parent.parent / "meridian" / "hotstate.py"


def _redis_up() -> bool:
    try:
        return hs.available()
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _isolate_redis_db(monkeypatch):
    """Gerçek-Redis testlerini db 15'e İZOLE et + CÖMERT socket_timeout'lu client — canlı sunucu (db 0)
    ile hem flush çakışması hem de 0.5s-timeout kontensiyon flake'i olmasın. Graceful testlerin _client
    override'ı sonra çalışır (last-wins)."""
    monkeypatch.setattr(hs, "_URL", "redis://127.0.0.1:6379/15")
    try:
        import redis
        c = redis.from_url("redis://127.0.0.1:6379/15", socket_connect_timeout=1.0,
                           socket_timeout=5.0, decode_responses=True)
        c.ping()
        monkeypatch.setattr(hs, "_client", c)
        monkeypatch.setattr(hs, "_blocking_client", c)
    except Exception:
        monkeypatch.setattr(hs, "_client", None)
        monkeypatch.setattr(hs, "_blocking_client", None)
    yield
    if hs._client is not None:
        hs.flush()
    hs._client = None
    hs._blocking_client = None


# ---------------- 1) GRACEFUL DEGRADATION (Redis'siz de koşar) ----------------
def test_reads_return_none_and_writes_noop_when_redis_is_down(sandbox_state, monkeypatch):
    """Kapalı porta bağla → her okuma None, her yazma False, sistem hiç istisna atmaz."""
    monkeypatch.setattr(hs, "_client", None)
    monkeypatch.setattr(hs, "_URL", "redis://127.0.0.1:6399/0")   # bağlanamaz
    hs._HEALTH.update(ok=None, down_since=None)

    assert hs.available() is False
    assert hs.get_price("AAPL") is None            # çağıran dosya/bar'a düşer
    assert hs.get_positions() is None
    assert hs.set_price("AAPL", 100.0) is False    # no-op, istisna YOK
    assert hs.set_prices({"A": 1.0, "B": 2.0}) == 0
    assert hs.cache_positions({"NVDA": {"qty": 1}}) is False


def test_down_state_is_visible_not_silent(sandbox_state, monkeypatch):
    """mirror_stream dersi: 'sahte güvenli-başarısızlık' değil — down health()'te GÖRÜNÜR."""
    monkeypatch.setattr(hs, "_client", None)
    monkeypatch.setattr(hs, "_URL", "redis://127.0.0.1:6399/0")
    hs._HEALTH.update(ok=None, down_since=None, fails=0)
    hs.get_price("X")
    h = hs.health()
    assert h["ok"] is False and h["down_since"] is not None and h["last_error"]


def test_url_password_is_masked_in_health():
    assert "***" in hs._mask("redis://user:supersecret@host:6379/0")
    assert "supersecret" not in hs._mask("redis://user:supersecret@host:6379/0")


# ---------------- 2) DENETLENEBİLİRLİK: KALICI GERÇEK YAZMAZ ----------------
def test_hotstate_never_writes_a_persistent_ledger():
    """MİMARİ SINIR (statik): hotstate yalnız UÇUCU Redis tutar. store.write_json/write_jsonl/
    append_jsonl ya da Path.write_* ÇAĞIRMAMALI — yoksa dedektörlerin göremediği bir yere kalıcı
    veri kaçar ve dürüstlük/denetlenebilirlik kimliği ölür."""
    tree = ast.parse(SRC.read_text())
    forbidden = {"write_json", "write_jsonl", "append_jsonl", "update_json",
                 "write_text", "write_bytes"}
    hits = [n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in forbidden]
    assert not hits, f"hotstate kalıcı defter yazıyor: {hits} — Redis yalnız uçucu olmalı"


# ---------------- 3) ROUNDTRIP (yalnız Redis varsa) ----------------
@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor — roundtrip testi atlandı")
def test_price_and_position_roundtrip_when_redis_is_up():
    hs.flush()
    hs.set_prices({"AAPL": 227.5, "NVDA": 178.2})
    assert hs.get_price("AAPL")["price"] == 227.5
    assert hs.get_price("ZZZZ") is None                    # olmayan sembol → None
    hs.cache_positions({"NVDA": {"qty": 100, "entry": 175.0}})
    assert hs.get_positions()["NVDA"]["qty"] == 100
    hs.flush()
    assert hs.get_positions() == {}                        # flush sonrası boş


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_price_carries_a_timestamp_for_staleness():
    """Intraday'de fiyatın YAŞI kritik: bayat sıcak fiyatla karar verilmemeli."""
    hs.flush()
    hs.set_price("SPY", 500.0)
    p = hs.get_price("SPY")
    assert p["price"] == 500.0 and p["ts"], "fiyat zaman damgasız — bayatlık ölçülemez"
    hs.flush()
