"""barfeed.py — DAYANIKLI bar-tetiği tüketicisi (Faz 3, 2026-07-23).

marketstream her dakikalık frame'i `hotstate.ingest_bars` ile yazarken `mrd:barfeed` akışına tek bir
"yeni bar geldi" olayı da XADD eder. BU modül o akışı bir CONSUMER-GROUP ile (XREADGROUP + ACK) okur ve
kayıtlı bir geri-çağrıyı (Faz 4 intraday_cycle buraya bağlanır) uyandırır.

NEDEN consumer-group (bare pub/sub DEĞİL): pub/sub fire-and-forget'tir — tüketici o an düşükse mesaj
KAYBOLUR. Consumer-group teslim edilen ama ACK'lenmemiş olayları tutar; süreç/görev bir an yeniden
başlarsa tetik DÜŞMEZ, son ACK'ten devam eder. "Yeni bar → karar uyandır" kancasının dayanıklı hâli.

NEDEN THREAD (asyncio DEĞİL): redis-py senkron; XREADGROUP block=Nms çağrısı thread'i bloklar. asyncio
görevinde koşarsa uvicorn event-loop'unu (marketstream/mirror/API dahil) dondururdu. Bu yüzden ayrı bir
daemon thread'de koşar — event-loop'a dokunmaz.

Faz 3 KAPSAMI: dayanıklı tetik mekanizması + görünürlük (events_read/lag). Kayıtlı geri-çağrı yoksa
olaylar yalnız SAYILIR ve ACK'lenir (mekanizmanın çalıştığının kanıtı, panoda görünür). Faz 4 gerçek
intraday_cycle'ı `register()` ile bağlar.
"""
from __future__ import annotations
import os
import threading

from . import hotstate, obs
from .streamhealth import _now_iso, _age_s

GROUP = "meridian-intraday"
CONSUMER = os.environ.get("MERIDIAN_BARFEED_CONSUMER", "c1")
_BLOCK_MS = 2000
_IDLE_SLEEP_S = 0.2


class BarfeedConsumer:
    """Tek tüketici. `run()` bir daemon thread'de sürer; `register(cb)` ile Faz 4 kancası takılır."""

    def __init__(self):
        self._stop = threading.Event()
        self.callback = None            # Faz 4 intraday_cycle: fn(fields: dict) -> None
        self.events_read = 0
        self.frames_seen = 0            # olaylardaki toplam 'n' (kaç bar tetikledi)
        self.stale_dropped = 0          # XAUTOCLAIM ile düşürülen bayat PEL girişi (churn kalıntısı vb.)
        self.last_read_at: str | None = None
        self.last_error: str = ""
        self.started_at: str | None = None

    def register(self, callback) -> None:
        self.callback = callback

    def run(self) -> None:
        self.started_at = _now_iso()
        hotstate.ensure_barfeed_group(GROUP)
        _iter = 0
        while not self._stop.is_set():
            _iter += 1
            if _iter % 30 == 1:     # ~60s'te bir (30 × 2s block): bayat PEL girişlerini XAUTOCLAIM+ACK ile düş
                dropped = hotstate.claim_and_drop_stale_barfeed(GROUP, CONSUMER)
                if dropped:
                    self.stale_dropped += dropped
            batch = hotstate.read_barfeed(GROUP, CONSUMER, count=50, block_ms=_BLOCK_MS)
            if batch is None:
                # Redis down / hata: hotstate zaten görünür kıldı; nazikçe bekle ve grup kur (Redis dönerse)
                self._stop.wait(1.0)
                hotstate.ensure_barfeed_group(GROUP)
                continue
            if not batch:
                continue                # block süresi doldu, yeni olay yok — döngüye devam
            ids = []
            for _id, fields in batch:
                ids.append(_id)
                self.events_read += 1
                self.last_read_at = _now_iso()
                try:
                    self.frames_seen += int(fields.get("n", 0) or 0)
                except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek sayaç alanı; olay yine işlenir/ACK'lenir, kayıp yok
                    pass
                cb = self.callback
                if cb is not None:
                    try:
                        cb(fields)
                    except Exception as e:
                        self.last_error = f"{type(e).__name__}: {e}"[:160]
                        obs.warn("barfeed_callback_failed", error=self.last_error,
                                 detail="intraday tetik geri-çağrısı hata verdi — olay yine ACK'lenir "
                                        "(sonsuz yeniden-teslim kilidi yok); tüketici kararı düşüremez")
            hotstate.ack_barfeed(GROUP, ids)   # işlendi → ACK (restart'ta yeniden teslim edilmez)

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> dict:
        return {"events_read": self.events_read, "frames_seen": self.frames_seen,
                "stale_dropped": self.stale_dropped,
                "last_read_at": self.last_read_at, "last_read_age_s": _age_s(self.last_read_at),
                "pending": hotstate.barfeed_pending(GROUP), "group": GROUP,
                "has_consumer": self.callback is not None, "last_error": self.last_error or None,
                "started_at": self.started_at}


_CONSUMER: BarfeedConsumer | None = None
_THREAD: threading.Thread | None = None


def consumer() -> BarfeedConsumer:
    global _CONSUMER
    if _CONSUMER is None:
        _CONSUMER = BarfeedConsumer()
    return _CONSUMER


def register(callback) -> None:
    """Faz 4 kancası: her yeni-bar olayında çağrılacak fonksiyonu bağla (fn(fields)->None)."""
    consumer().register(callback)


def start() -> threading.Thread:
    """IDEMPOTENT: thread zaten canlıysa no-op. Daemon thread — süreç ölünce kendisi de ölür."""
    global _THREAD
    if _THREAD is not None and _THREAD.is_alive():
        return _THREAD
    _THREAD = threading.Thread(target=consumer().run, daemon=True, name="barfeed")
    _THREAD.start()
    return _THREAD


def stop() -> None:
    if _CONSUMER is not None:
        _CONSUMER.stop()


def health() -> dict:
    """Pano/API görünürlüğü. Hiç başlamamışsa (Redis yok / bayrak kapalı) ok=None üçüncü hâli."""
    if _CONSUMER is None:
        return {"ok": None, "running": False, "events_read": 0, "frames_seen": 0,
                "stale_dropped": 0, "last_read_at": None, "last_read_age_s": None, "pending": 0,
                "group": GROUP, "has_consumer": False, "last_error": None}
    running = _THREAD is not None and _THREAD.is_alive()
    snap = _CONSUMER.snapshot()
    # ok: thread canlı VE (Redis erişilebilir). read_barfeed None dönüyorsa Redis down → ok False.
    snap["running"] = running
    snap["ok"] = bool(running) and hotstate.available()
    return snap
