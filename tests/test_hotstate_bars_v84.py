"""test_hotstate_bars_v84.py — Redis Stream dakikalık-bar primitifleri (Faz 2, 2026-07-23).

nodeid'de 'hotstate' geçer → conftest `_hotstate_off_by_default` bunu ATLAR, gerçek Redis kullanılır
(v83 deseni). Graceful yol Redis'siz de doğrulanır; roundtrip Redis varsa.
"""
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
    """Gerçek-Redis testlerini db 15'e İZOLE et + CÖMERT socket_timeout'lu client ver. İki sorunu birden
    kapar (çekişmeli-inceleme sonrası CANLI koşuda görüldü): (a) db 0 canlı sunucuyla flush çakışması/
    kontaminasyon, (b) hot-path'in 0.5s timeout'u canlı-sunucu kontensiyonu altında test op'larını
    kesip flake yapıyordu. Graceful/recovery testlerinin _client override'ı sonra çalışır (last-wins)."""
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


@pytest.fixture(autouse=True)
def _arsiv_sandbox(sandbox_state):
    """FAZ 5 (2026-07-27): `ingest_bars` artık başarılı yazımdan sonra çerçeveyi
    `state/intraday_bars/<UTC-gün>.jsonl` dosyasına da düşürüyor (bararchive). Bu modüldeki
    gerçek-Redis testleri o ana kadar HİÇ state yazmıyordu ve çoğu `sandbox_state` almıyordu —
    yani yeni yan etki doğrudan CANLI deftere düşerdi (conftest'in canlı-yazım muhafızı bunu
    yakaladı, ki tam olarak işi bu). Redis izolasyonunun disk karşılığı: tüm modül sandbox'ta."""
    yield


def test_bar_primitives_graceful_when_down(sandbox_state, monkeypatch):
    """Redis kapalı: her yazma no-op (None/False/0), okuma None, istisna YOK; down GÖRÜNÜR."""
    monkeypatch.setattr(hs, "_client", None)
    monkeypatch.setattr(hs, "_URL", "redis://127.0.0.1:6399/0")
    hs._HEALTH.update(ok=None, down_since=None)
    assert hs.append_bar("AAPL", {"c": 1, "t": "2026-07-23T13:45:00Z"}) is None
    assert hs.ingest_bar("AAPL", {"c": 1, "t": "2026-07-23T13:45:00Z"}) is False
    assert hs.ingest_bars({"AAPL": {"c": 1, "t": "2026-07-23T13:45:00Z"}}) == 0
    assert hs.read_bars("AAPL") is None
    assert hs.bars_len("AAPL") == 0
    assert hs.health()["ok"] is False


def test_input_error_does_not_mark_redis_down(sandbox_state):
    """KURT MASALI (çekişmeli inceleme): girdi hatası (float(None)) Redis'i 'down' sanmamalı."""
    hs._HEALTH.update(ok=True, down_since=None, fails=0)
    hs._note_down(TypeError("float() argument must be a string or a number"))
    assert hs._HEALTH["ok"] is True and hs._HEALTH["down_since"] is None   # sağlık DÜŞMEDİ
    assert hs._HEALTH["fails"] == 1                                        # yalnız sayaç arttı


def test_connectivity_error_resets_client_for_recovery(sandbox_state, monkeypatch):
    """#1 fix: bağlantı hatası client'ı BIRAKIR ki bir sonraki _redis() yeniden ping'lesin (ok toparlanır)."""
    monkeypatch.setattr(hs, "_client", object())     # sahte önbellekli client
    hs._HEALTH.update(ok=True, down_since=None)
    hs._note_down(ConnectionError("boom"))
    assert hs._client is None and hs._HEALTH["ok"] is False   # client bırakıldı, down görünür


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_ok_recovers_after_transient_blip(sandbox_state, monkeypatch):
    """#1 fix uçtan uca: geçici blip'ten sonra sağlık ÖMÜR BOYU False kalmaz — ilk gerçek op toparlar."""
    monkeypatch.setattr(hs, "_client", None)                   # temiz başla → ilk op ping'ler
    hs.flush()
    hs.set_price("AAPL", 1.0)
    assert hs.health()["ok"] is True
    hs._note_down(ConnectionError("transient"))                # blip → _client=None, ok=False
    assert hs.health()["ok"] is False and hs._client is None
    hs.set_price("AAPL", 2.0)                                   # _client None → _redis() yeniden ping
    assert hs.health()["ok"] is True                           # TOPARLANDI (kalıcı yanlış-kırmızı değil)
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_ingest_bars_requires_t_field():
    """#5 fix: `t`siz bar YAZILMAZ (look-ahead sözleşmesi close_ts=t+60s'e dayanır)."""
    hs.flush()
    assert hs.ingest_bars({"AAPL": {"c": 1.5}}) == 0            # t yok → atlanır
    assert hs.bars_len("AAPL") == 0
    assert hs.ingest_bars({"AAPL": {"c": 1.5, "t": "2026-07-23T13:45:00Z"}}) == 1   # t var → yazılır
    hs.flush()


def test_bar_primitives_never_write_a_persistent_ledger():
    """MİMARİ SINIR (statik): yeni primitifler eklendi ama hotstate HÂLÂ kalıcı defter YAZMAZ
    (write_json/write_* yok; `xadd` yasak DEĞİL — o UÇUCU Redis stream'idir, dosya değil)."""
    tree = ast.parse(SRC.read_text())
    forbidden = {"write_json", "write_jsonl", "append_jsonl", "update_json", "write_text", "write_bytes"}
    hits = [n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in forbidden]
    assert not hits, f"hotstate kalıcı defter yazıyor: {hits}"


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor — roundtrip atlandı")
def test_ingest_bar_roundtrip_and_hot_price_single_write_path():
    """TEK YAZMA YOLU KANITI: bir kapanmış bar ingest edilince hem mrd:bars'a düşer hem sıcak fiyat
    (mrd:price) bar KAPANIŞINA (`c`) + damgaya (`t`) çekilir. 'Her kapanmış bar sıcak fiyatı günceller'
    yasası burada tek çağrıda karşılanır."""
    hs.flush()
    hs.ingest_bar("AAPL", {"o": 1, "h": 2, "l": 0.5, "c": 227.5, "v": 1000,
                           "vw": 1.4, "n": 10, "t": "2026-07-23T13:45:00Z"})
    bars = hs.read_bars("AAPL")
    assert bars and bars[-1]["c"] == 227.5 and bars[-1]["t"] == "2026-07-23T13:45:00Z"
    assert hs.get_price("AAPL")["price"] == 227.5      # kapanmış bar → sıcak fiyat, TEK yolda
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_barfeed_event_and_consumer_group_roundtrip():
    """Faz 3: ingest_bars mrd:barfeed'e olay YAZAR; consumer-group (XREADGROUP+ACK) onu dayanıklı okur.
    Grup 'her yeni-bar frame'ini tek olay olarak görür; ACK sonrası pending 0 (yeniden teslim yok)."""
    hs.flush()
    hs.ensure_barfeed_group("g1")     # MKSTREAM boş akış + grup id=$ (yalnız SONRAKİ olaylar)
    hs.ingest_bars({"NVDA": {"c": 9.0, "t": "2026-07-23T13:46:00Z"},
                    "AMD": {"c": 4.0, "t": "2026-07-23T13:46:00Z"}})
    batch = hs.read_barfeed("g1", "c", block_ms=500)
    assert batch and len(batch) == 1                    # bir frame = bir olay
    _id, fields = batch[0]
    assert fields["n"] == "2" and "NVDA" in fields["syms"] and "AMD" in fields["syms"]
    assert hs.barfeed_pending("g1") == 1                 # okundu ama ACK'lenmedi
    assert hs.ack_barfeed("g1", [_id]) == 1
    assert hs.barfeed_pending("g1") == 0                 # ACK sonrası temiz
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_claim_and_drop_stale_barfeed():
    """Faz 4: bayat PEL girişleri (okundu ama ACK'lenmedi — ör. churn kalıntısı) XAUTOCLAIM+ACK ile düşer."""
    hs.flush()
    hs.ensure_barfeed_group("g")
    hs.ingest_bars({"AAPL": {"c": 1.0, "t": "2026-07-23T13:45:00Z"}})
    batch = hs.read_barfeed("g", "c", block_ms=300)         # okundu, ACK YOK → PEL'de
    assert batch and hs.barfeed_pending("g") == 1
    dropped = hs.claim_and_drop_stale_barfeed("g", "c", min_idle_ms=0)   # 0 = hemen bayat
    assert dropped == 1 and hs.barfeed_pending("g") == 0
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_ensure_barfeed_group_is_idempotent():
    hs.flush()
    assert hs.ensure_barfeed_group("g2") is True
    assert hs.ensure_barfeed_group("g2") is True         # BUSYGROUP → yine True (idempotent)
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_read_bars_is_oldest_to_newest_and_count_capped():
    hs.flush()
    for i in range(5):
        hs.append_bar("QQQ", {"c": float(i), "t": f"2026-07-23T13:0{i}:00Z"})
    assert [b["c"] for b in hs.read_bars("QQQ")] == [0.0, 1.0, 2.0, 3.0, 4.0]     # eskiden-yeniye
    assert [b["c"] for b in hs.read_bars("QQQ", count=2)] == [3.0, 4.0]           # son 2, sırayla
    hs.flush()


@pytest.mark.skipif(not _redis_up(), reason="Redis çalışmıyor")
def test_append_bar_passes_maxlen_ring_to_xadd(monkeypatch):
    """RING: append_bar XADD'e MAXLEN~ (approximate) geçirir → stream sonsuz büyümez. Gerçek trimming
    Redis'in işi; burada BİZİM kodun ring parametresini geçtiğini DETERMİNİSTİK doğrularız (2000-append
    yükü + canlı-sunucu kontensiyon flake'i yok — çekişmeli-inceleme sonrası bu test ağır+flaky'di)."""
    hs.flush()
    r = hs._redis()
    seen = {}
    orig = r.xadd

    def spy(key, fields, **kw):
        seen["maxlen"] = kw.get("maxlen")
        seen["approx"] = kw.get("approximate")
        return orig(key, fields, **kw)

    monkeypatch.setattr(r, "xadd", spy)
    hs.append_bar("ZZZ", {"c": 1.0, "t": "2026-07-23T14:00:00Z"}, maxlen=123)
    assert seen["maxlen"] == 123 and seen["approx"] is True   # ring parametresi geçiyor
    hs.flush()
