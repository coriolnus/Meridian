"""marketstream.py — Alpaca dakikalık KAPANMIŞ bar WS dinleyicisi: piyasa verisi → mrd:bars + sıcak fiyat.

NE YAPAR: mirror_stream (yürütme) trade_updates taşırken BU katman AYRI bir hosttan
(stream.data.alpaca.markets, `alpaca.data_ws_url(FEED)`) dakikalık kapanmış barları dinler ve her
WS çerçevesini `hotstate.ingest_bars` ile Redis'e (mrd:bars akışları + mrd:price sıcak fiyat) yazar.
Bir WS frame'i birden çok mesaj taşıyabilir (karışık sembol/tip) — batched-array parse burada yaşar.
Reconnect/backoff/nabız/down-reassert YASASI `streamhealth.run_stream`ten gelir, KOPYA YOK (mirror
ile aynı nesne); bu modülde yalnız akışa-özgü olan vardır: data URL, auth+`bars` aboneliği, `b`→ingest.

KİLİT GİRİŞLER: start()/stop() (idempotent singleton görev), listener(), health() (hiç koşmamışsa
ok=None — 'unknown ≠ broken'), subscribed_symbols() (açık pozisyonlar → SPY → dataset._canli_
korunan_evren(); pozisyonlar en başta — izlenmeyen pozisyon sıcak-fiyat kör noktasıdır), FEED (MERIDIAN_DATA_FEED,
varsayılan iex), MAX_SYMBOLS (opsiyonel güvenlik valfi; iex `bars` kanalı sembol-sınırsız).

DEĞİŞMEZLER — WS dinleyici ortak yasası + kapalı-bar disiplini: abonelik YALNIZ `bars` kanalıdır ve
yalnız `T=="b"` (dakika kapanınca gelen TAMAMLANMIŞ bar) ingest edilir; `u`(düzeltme)/`d`(forming
günlük)/`t`/`q` ASLA — forming/partial fiyat mrd:price'a/mrd:bars'a yazılmaz. Bar `t` = dakika
BAŞLANGICI; close_ts = t+60s (hotstate sözleşmesi). mrd:bars backtest/recompute'a ASLA girmez —
kalıcı öğrenme kaynağı EOD immutable dosya barlarıdır. 'alive' yalnız KANITLI olayda (auth'lı /
abonelik / bar) işaretlenir; auth hatasında (401-404) yanlış anahtarla çekiçleme yok — uzun bekleme.
Sağlık UÇUCUDUR (persist=no-op, disk bayrağı yok): "ölü dinleyici diskte yeşil bırakır" alt-sınıfı
yapısal olarak yoktur; görev ölürse checked_at donar → ok False. iex hesap başına TEK data
bağlantısına izin verir (ikincisi 406) — idempotent singleton çift bağlantıyı yapısal önler.

OKUR/YAZAR: portfolio.json'ı (abonelik evreni için) okur; Redis'e yalnız hotstate.ingest_bars
üzerinden yazar (tek yazma yolu); diske hiçbir şey yazmaz.
"""
from __future__ import annotations
import asyncio
import json
import os

from . import streamhealth, hotstate, obs, secrets
from .adapters import alpaca
from .streamhealth import _pause, _now_iso   # ad = aynı nesne (test `streamhealth.py::_pause` monkeypatch'i)

FEED = os.environ.get("MERIDIAN_DATA_FEED", "iex")
# 0/unset = efektif sınırsız. iex bars kanalı sembol-SINIRSIZ (30-tavan yalnız t/q kanallarına ait) →
# tüm evren tek abonelikte. Bu yalnız opsiyonel bir güvenlik valfi.
MAX_SYMBOLS = int(os.environ.get("MERIDIAN_STREAM_MAX_SYMBOLS", "0")) or None
INDEX_SYMBOL = "SPY"


def subscribed_symbols() -> list[str]:
    """Abone olunacak evren: açık POZİSYONLAR → SPY → `dataset._canli_korunan_evren()`,
    tekilleştirilmiş. Pozisyonlar EN BAŞTA — izlenmeyen bir pozisyon sıcak-fiyat kör noktasıdır.

    TSK-116 düzeltme turu 3 (2026-09-03, Rol-1 kararı — review Bulgu 4): kuyruk artık DOĞRUDAN
    `data.LIVE_UNIVERSE` DEĞİL, `dataset._canli_korunan_evren()` — TEK KAYNAK, `dataset.py`nin
    canlı bar yükleyicisiyle AYNI yardımcı. Önceki tasarım yalnız `positions`i (bu fonksiyonun kendi
    manuel öneki üzerinden) koruyordu; `armed` (onaylı, henüz dolmamış plan) bir endeks-çıkışı
    sembolde WS aboneliği hiç olmadan kalabiliyordu — modülün kendi uyardığı sınıf ("izlenmeyen
    pozisyon sıcak-fiyat kör noktasıdır") ama "izlenmeyen ARMED plan" için. `dataset -> marketstream`
    yönünde mevcut bir importlinter sözleşmesi yok (`pyproject.toml`: `meridian.marketstream` hiçbir
    sözleşmede source/target olarak geçmiyor; `meridian.dataset` yalnız çekirdek-altyapının {store,
    storage, config, obs} import ETMEMESİ gereken bir HEDEF — bu YÖN `marketstream -> dataset`i
    yasaklamıyor) — statik okumayla doğrulandı, `lint-imports` KOŞULMADI (pytest-dışı araç, ajan
    kapsamı dışı). Varsayılan kırpma YOK (iex sınırsız)."""
    from . import dataset, store
    pf = store.read_json("portfolio.json", {}) or {}
    out: list[str] = []
    seen: set[str] = set()
    for t in list((pf.get("positions") or {}).keys()) + [INDEX_SYMBOL] + list(dataset._canli_korunan_evren()):
        t = str(t).strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    if MAX_SYMBOLS:
        out = out[:MAX_SYMBOLS]
    return out


class MarketState:
    """UÇUCU süreç-içi durum: sağlık (ortak StreamHealth, persist=no-op) + bar telemetrisi. hydrate
    ÇAĞRILMAZ — disk yok, her süreç taze başlar."""

    def __init__(self):
        """Bar sayacını/son bar damgasını sıfırlar ve ORTAK sağlık nesnesini persist=no-op ile kurar
        (piyasa-verisi telemetrisi UÇUCU: diske yeşil bayrak donmaz)."""
        self.bars_seen = 0
        self.last_bar_at: str | None = None
        # persist=no-op → market sağlığı DİSKE yazmaz (mirror'da diske yazar). Yasa yine tek.
        self.health = streamhealth.StreamHealth("marketstream", "piyasa verisi", persist=lambda: None)


STATE: MarketState | None = None


def state() -> MarketState:
    """Süreç-içi TEKİL MarketState'i döndürür (ilk çağrıda kurar). Disk yok — her süreç taze başlar."""
    global STATE
    if STATE is None:
        STATE = MarketState()
    return STATE


class MarketStreamListener:
    """asyncio dinleyicisi — `streamhealth.run_stream(spec)` protokolünü uygular; reconnect/backoff
    BEDAVA gelir. `session` emre-özgü: auth + `bars` aboneliği + batched-array parse + `b`→ingest."""

    connect_kwargs = {"ping_interval": 20, "ping_timeout": 20}

    def __init__(self):
        """Dinleyiciyi süreç-içi MarketState'e bağlar (sağlık nesnesi ondan ödünç), dur-olayı/KANITLI
        canlılık bayrağı/kopuş saatini sıfırlar ve abonelik evrenini KURULUM ANINDA dondurur."""
        self.state = state()
        self.health = self.state.health
        self._stop = asyncio.Event()
        self._alive = False
        self._down_since = None
        self._cancel_fired = False
        self._subs = subscribed_symbols()

    # --- run_stream(spec) protokolü ---
    @property
    def stop_event(self) -> asyncio.Event:
        """run_stream protokolü: sürücünün her turda yokladığı durdurma olayı."""
        return self._stop

    @staticmethod
    def _url() -> str:
        """Seçili feed'in (FEED) Alpaca data WS adresi — yürütme hostundan AYRI bir hosttur."""
        return alpaca.data_ws_url(FEED)

    def url(self) -> str:
        """run_stream protokolü: bağlanılacak data WS adresi."""
        return self._url()

    async def pause(self, s: float) -> None:
        """run_stream protokolü: backoff beklemesi; modül-global `_pause`a devreder (test monkeypatch'i
        görünür kalsın)."""
        return await _pause(s)

    def on_grace_exceeded(self) -> None:
        """run_stream protokolü: kopuş grace'i aşınca çağrılır — burada BİLİNÇLİ no-op (bu yolda emir
        yok, iptal edilecek koruma bacağı yok; devre-kesici mirror'a özgüdür)."""
        # BİLİNÇLİ no-op: piyasa-verisi kesintisinde iptal edilecek koruma bacağı YOK (bu yolda emir
        # yok). Görünürlük set_stream/touch'tan gelir; devre-kesici mirror'a özgüdür.
        pass

    async def session(self, ws, mark_alive) -> None:
        """Emre-özgü oturum: auth + YALNIZ `bars` aboneliği + batched-array parse. Bir WS frame'i
        BİRDEN ÇOK mesaj taşıyabilir (karışık sembol/tip) → dizi üzerinde döngü şart."""
        await ws.send(json.dumps({"action": "auth",
                                  "key": secrets.get("ALPACA_PAPER_KEY") or "",
                                  "secret": secrets.get("ALPACA_PAPER_SECRET") or ""}))
        await ws.send(json.dumps({"action": "subscribe", "bars": self._subs}))   # YALNIZ kapalı-bar kanalı
        async for raw in ws:
            if self._stop.is_set():
                break
            try:
                msgs = json.loads(raw)
            except (json.JSONDecodeError, TypeError):  # sessiz-yutma: yardımcı G/Ç; çağıran yokluğu yedekle karşılar
                continue
            batch = {}
            for m in (msgs if isinstance(msgs, list) else [msgs]):
                T = m.get("T")
                # v68/D2: alive YALNIZ KANITLI olayda (auth'lı / abonelik / bar) — 'connected' (auth
                # öncesi) alive YAPMAZ. mark_alive idempotent.
                if (T == "success" and m.get("msg") == "authenticated") or T == "subscription" or T == "b":
                    mark_alive()
                if T == "b":
                    s = m.get("S")
                    if s:
                        batch[s] = {"o": m.get("o"), "h": m.get("h"), "l": m.get("l"), "c": m.get("c"),
                                    "v": m.get("v", 0), "vw": m.get("vw"), "n": m.get("n"), "t": m.get("t")}
                elif T == "error":
                    self._on_error(m)
                    if int(m.get("code", 0) or 0) in (401, 402, 403, 404):
                        # AUTH BAŞARISIZ: yanlış anahtarla çekiçleme yok (mirror'ın unauth disiplini).
                        # run_stream backoff'u 60s'te tavan yapar; auth hatası kalıcıdır, o yüzden
                        # burada uzun bir bekleme koyup oturumu bitiriyoruz (Alpaca'yı ≤60s'te dövmeyelim).
                        await _pause(300)
                        return
                # 'u'/'d'/'t'/'q' → look-ahead/kapsam gereği YOK SAYILIR (batch'e girmez)
            if batch:
                self.state.bars_seen += len(batch)
                self.state.last_bar_at = _now_iso()
                hotstate.ingest_bars(batch)          # append + set_price, TEK pipeline (tek yazma yolu)

    def _on_error(self, m: dict) -> None:
        """Sunucudan gelen `T=="error"` mesajını koda göre AYIRT EDİLEBİLİR bir uyarıya çevirir:
        406 tek-bağlantı ihlali, 401-404 kimlik, 405/409/410 feed/kota kısıtı, kalanı genel hata."""
        code = int(m.get("code", 0) or 0)
        if code == 406:
            obs.warn("marketstream_conn_limit",
                     detail="data akışında zaten bir bağlantı var — tek-sahip ihlali (ikinci soket kapanır)")
        elif code in (401, 402, 403, 404):
            obs.warn("marketstream_unauthorized", code=code)
        elif code in (405, 409, 410):
            obs.warn("marketstream_subscription_limited", code=code,
                     detail="feed/kota kısıtı — MERIDIAN_DATA_FEED=iex varsayılanına dönülebilir")
        else:
            obs.warn("marketstream_error", error=f"code={code}: {str(m.get('msg'))[:80]}")

    async def run(self) -> None:
        """Dinleyiciyi başlatır: reconnect/backoff/nabız/down-saati ORTAK sürücüde
        (streamhealth.run_stream) koşar; bu sınıf yalnız `spec` protokolünü sağlar."""
        await streamhealth.run_stream(self)

    def stop(self) -> None:
        """Dur-olayını basar: ortak sürücü ile nabız görevi bir sonraki yoklamada temiz çıkar."""
        self._stop.set()

    def snapshot(self) -> dict:
        """StreamHealth üstüne market ekleri. `ok` ORTAK yasadan (flag × nabız tazeliği) — mirror ile
        aynı hesap; görev ölürse checked_at donar → ok False (disk bayrağı yok, donmuş-yeşil alt-sınıf yok)."""
        base = streamhealth.health_snapshot(self.health.to_dict())
        return {**base, "alive": bool(self._alive), "feed": FEED,
                "bars_seen": self.state.bars_seen, "last_bar_at": self.state.last_bar_at,
                "last_bar_age_s": streamhealth._age_s(self.state.last_bar_at),
                "subscribed": len(self._subs)}


# ---------------- SINGLETON (406 zorunluluğu: iex hesap başına TEK data bağlantısı) ----------------
_LISTENER: MarketStreamListener | None = None
_TASK = None


def listener() -> MarketStreamListener:
    """Süreç-içi TEKİL dinleyiciyi döndürür (ilk çağrıda kurar). Tekillik zorunludur: iex hesap başına
    TEK data bağlantısına izin verir (ikinci soket 406 alır)."""
    global _LISTENER
    if _LISTENER is None:
        _LISTENER = MarketStreamListener()
    return _LISTENER


def start(loop=None):
    """IDEMPOTENT: _TASK canlıysa no-op → çift bağlantı (=406) YAPISAL önlenir. uvicorn'un event
    loop'unda görev olarak koşar (mirror ile aynı desen)."""
    global _TASK
    if _TASK is not None and not _TASK.done():
        return _TASK
    loop = loop or asyncio.get_event_loop()
    _TASK = loop.create_task(listener().run())
    return _TASK


def stop() -> None:
    """Tekil dinleyiciye dur der (hiç kurulmamışsa no-op) — görevi kendisi beklemez/iptal etmez."""
    if _LISTENER is not None:
        _LISTENER.stop()


def health() -> dict:
    """Pano/API görünürlüğü. Dinleyici HİÇ koşmamışsa (paper yok / bayrak kapalı) listener KURMADAN
    `ok=None` döner — 'unknown ≠ broken' üçüncü hâli (mirror'ın h5c ikizi); pano '—' der, 'KOPUK' değil."""
    if _LISTENER is None:
        return {"ok": None, "flag": False, "stale": True, "alive": False, "feed": FEED,
                "bars_seen": 0, "last_bar_at": None, "last_bar_age_s": None,
                "checked_at": None, "checked_age_s": None, "down_since": None,
                "last_error": None, "last_event_ts": None, "subscribed": 0}
    return _LISTENER.snapshot()
