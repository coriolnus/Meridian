"""mirror_stream.py — Olay-güdümlü YÜRÜTME-DURUMU katmanı (operatör mimari isteği, 2026-07-19).

Alpaca `trade_updates` WebSocket akışını dinler ve ayna emirlerinin YEREL DURUM MAKİNESİNİ anlık
besler: dolum/kısmi-dolum/ret/iptal artık bir sonraki döngünün uzlaştırmasını (300 sn+) beklemez.

FAZ 2 REFACTOR (2026-07-23): bayatlık/nabız/backoff/down-reassert/reconnect YASASI `streamhealth`e
ÇIKARILDI — mirror onu İÇE AKTARIR (aynı nesne), marketstream de aynı yasayı tüketir. `next_backoff`,
`set_stream`, `touch`, reconnect döngüsü artık TEK yerde; "aynı yasa iki uygulama, sessiz ayrışma"
kusuru (54→2 down) YAPISAL olarak imkânsız. Bu modülde YALNIZ emre-özgü olan kalır: emir durum makinesi
(`apply`/`pending_symbols`), paper host-kilidi (`_url`), devre-kesici (`_maybe_cancel_entries`) ve
`mirror_orders.json` kalıcılığı (yürütme gerçeği restart-güvenli olmalı). Davranış BİREBİR aynı —
mevcut v33/v68/v72 testleri sıfır düzenlemeyle geçer (davranış-koruma kanıtı).

SINIR ÇİZGİLERİ (bilinçli):
  * KARAR HATTI DOKUNULMAZ — sinyaller kapalı-bar EOD yasasıyla üretilir; bu katman yalnız YÜRÜTME
    durumunu taşır. bars/quotes akışına bilerek abone OLUNMAZ (o Faz 2 marketstream'in işidir; karar
    hattına ASLA sızmaz — look-ahead yasası).
  * Zamanlayıcı poll'u KALIR — akış koptuğunda uzlaştırma güvenlik ağıdır (kemer + pantolon askısı).
  * Hostname-kilitli PAPER akışı — gerçek-para stream'ine bu modülden çıkış yoktur.
  * Kopuş devre-kesicisi KORUMA BACAKLARINI ASLA iptal etmez; görünürlük sağlar (stream_ok=false → amber).
    İstenirse YALNIZ dolmamış GİRİŞ emirlerinin iptali MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES=1 ile
    açılır (varsayılan KAPALI)."""
from __future__ import annotations
import asyncio
import datetime as dt
import json
import threading

from . import store, obs, secrets, streamhealth
# ORTAK YASA — ad = AYNI nesne (streamhealth.next_backoff IS mirror_stream.next_backoff). Kopya YOK;
# test_streamhealth_parity_v84 bunu kimlik (`is`) + AST-yokluk ile kilitler.
from .streamhealth import (                                     # noqa: F401 (test yüzeyi + re-export)
    next_backoff, _now, _now_iso, _age_s, _fresh, _pause,
    HEARTBEAT_S, STALE_AFTER_S, DOWN_REASSERT_S, GRACE_SECONDS,
    BACKOFF_START, BACKOFF_MAX, DNS_BACKOFF_FLOOR, DNS_MARKERS)

STATE_FILE = "mirror_orders.json"
STREAM_PATH = "/stream"
PENDING_MAX_AGE_H = 24      # bu kadar eski 'bekleyen' kayıt güvenilmez (kaçan terminal olay →
                            # sembolün sonsuza dek karar dışı kalması yasak; denetim turu 18)
TERMINAL = {"filled", "canceled", "cancelled", "expired", "rejected", "done_for_day"}
PENDING = {"new", "accepted", "pending_new", "partially_filled", "held", "calculated",
           "accepted_for_bidding", "replaced"}


class MirrorOrderStateMachine:
    """client_order_id-anahtarlı yerel emir durum makinesi. Saf ve senkron — WebSocket olaylarıyla
    beslenir, atomik anlık görüntüsü state/mirror_orders.json'a yazılır. 'Bekleyen emir varken yeni
    karar üretme' kuralının ANLIK veri kaynağı budur (uzlaştırma anlık görüntüsü artık yedek).

    FAZ 2: sağlık YARISI `streamhealth.StreamHealth`e delege — `stream_ok/checked_at/down_since/
    last_error/_last_reassert` ve `set_stream/touch` artık ortak yasadan. `_persist` (disk) mirror'a
    özgü kalır (yürütme gerçeği restart-güvenli); StreamHealth'e `persist` geri-çağrısı olarak enjekte
    edilir."""

    def __init__(self):
        st = store.read_json(STATE_FILE, {})
        self.orders: dict = st.get("orders", {})          # coid -> {status, symbol, filled_qty, ...}
        self.last_event_ts: str | None = st.get("last_event_ts")
        self._lock = threading.Lock()
        # Sağlık durumu ORTAK yasadan; disk kalıcılığı (mirror'a özgü) persist geri-çağrısıyla enjekte.
        self.health = streamhealth.StreamHealth("mirror_stream", "yürütme",
                                                persist=self._persist, lock=self._lock)
        self.health.hydrate(st)     # v68: bayat `stream_ok` bayrağını taze nabız yoksa false'a çeker

    # --- Sağlık alanları ORTAK yasaya proxy (test yüzeyi korunur: sm.stream_ok/last_error/... ) ---
    @property
    def stream_ok(self) -> bool:
        return self.health.stream_ok

    @stream_ok.setter
    def stream_ok(self, v):
        self.health.stream_ok = v

    @property
    def last_error(self) -> str:
        return self.health.last_error

    @last_error.setter
    def last_error(self, v):
        self.health.last_error = v

    @property
    def down_since(self):
        return self.health.down_since

    @down_since.setter
    def down_since(self, v):
        self.health.down_since = v

    @property
    def checked_at(self):
        return self.health.checked_at

    @checked_at.setter
    def checked_at(self, v):
        self.health.checked_at = v

    @property
    def _last_reassert(self) -> float:
        return self.health._last_reassert

    @_last_reassert.setter
    def _last_reassert(self, v):
        self.health._last_reassert = v

    def set_stream(self, ok: bool, error: str = "") -> None:
        self.health.set_stream(ok, error)

    def touch(self, error: str = "") -> bool:
        return self.health.touch(error)

    def _persist(self) -> None:
        # canlı olmayan (terminal) emirleri en son 100 ile sınırla — dosya sonsuz büyümesin
        term = [(k, v) for k, v in self.orders.items() if str(v.get("status", "")).lower() in TERMINAL]
        if len(term) > 100:
            for k, _ in sorted(term, key=lambda kv: str(kv[1].get("updated", "")))[:-100]:
                self.orders.pop(k, None)
        # `stream_ok` bundan böyle TEK BAŞINA okunmamalı — okuyucu stream_health()'i kullanmalı.
        store.write_json(STATE_FILE, {"orders": self.orders, "last_event_ts": self.last_event_ts,
                                      **self.health.to_dict(), "updated": _now_iso()})

    def apply(self, event: str, order: dict) -> None:
        """Bir trade_updates olayını işle. Bilinmeyen olaylar da kaydedilir (dürüstlük: gizleme yok).

        YENİDEN-BAĞLANMA GÜVENLİĞİ (v68): yeniden bağlanan bir akış aynı olayları TEKRAR yollarsa iki
        somut zarar olurdu: (a) TERMİNAL bir emir daha eski 'new/accepted' ile geri sarılır ve sembol
        yeniden 'bekleyen' sayılır — karar hattı o hisseyi kilitler; (b) aynı `rejected` ikinci kez
        BROKER_REJECT alarmı basar. Kural: terminal EMİCİDİR (geri sarılmaz) ve birebir aynı olay ikinci
        kez sinyal üretmez. Emir GÖNDERME yolu yok — bu sınıf yalnız okur; tekrar mükerrer emre dönüşemez."""
        coid = order.get("client_order_id")
        if not coid:
            return
        incoming = str(order.get("status", event)).lower()
        with self._lock:
            rec = self.orders.get(coid, {})
            prev = str(rec.get("status", "")).lower()
            if prev in TERMINAL and incoming not in TERMINAL:
                obs.warn("mirror_stream_stale_event", ticker=order.get("symbol"),
                         coid=str(coid)[:24], had=prev, got=incoming,
                         detail="terminal emir geri sarılamaz — bayat/tekrarlı olay yok sayıldı")
                return
            if prev == incoming and rec.get("event") == event and \
                    rec.get("filled_qty") == order.get("filled_qty"):
                return                       # birebir tekrar: yeni bilgi yok, ikinci sinyal de yok
            rec.update({"status": incoming, "event": event,
                        "symbol": order.get("symbol"), "side": order.get("side"),
                        "filled_qty": order.get("filled_qty"), "qty": order.get("qty"),
                        "filled_avg_price": order.get("filled_avg_price"),
                        "order_id": order.get("id"),
                        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
            self.orders[coid] = rec
            self.last_event_ts = rec["updated"]
            self._persist()
        lvl = {"fill": "fill", "partial_fill": "partial_fill", "rejected": "REJECT",
               "canceled": "canceled"}.get(event, event)
        if event == "rejected":
            obs.alarm(obs.ALARM_BROKER_REJECT, f"akıştan anlık RET: {order.get('symbol')}",
                      ticker=order.get("symbol"), plan_id=coid)
        else:
            obs.log("mirror_stream_event", ev=lvl, ticker=order.get("symbol"),
                    coid=str(coid)[:24], status=rec["status"], filled=order.get("filled_qty"))

    def pending_symbols(self) -> set:
        """BEKLEYEN emirlerin sembolleri — 'bu hissede zaten canlı emir var, yeni karar üretme'
        kuralının anlık kaynağı.

        BAYATLIK UFKU (denetim turu 18): akış koparsa ya da tek bir terminal olay kaçarsa kayıt
        SONSUZA KADAR 'pending' kalır ve o sembol kalıcı olarak karar dışı olur — sessiz, alarmsız bir
        açlık. PENDING_MAX_AGE_H'ten eski kayıtlar güvenilmez sayılır; gerçeği uzlaştırma zaten söylüyor."""
        cutoff = (dt.datetime.now(dt.timezone.utc)
                  - dt.timedelta(hours=PENDING_MAX_AGE_H)).isoformat(timespec="seconds")
        out, stale = set(), []
        with self._lock:
            for coid, v in self.orders.items():
                if str(v.get("status", "")).lower() not in PENDING or not v.get("symbol"):
                    continue
                if str(v.get("updated") or "") < cutoff:
                    stale.append((coid, v.get("symbol")))
                    continue
                out.add(v.get("symbol"))
        for coid, sym in stale[:5]:
            obs.warn("mirror_pending_stale", ticker=sym, coid=str(coid)[:24],
                     detail=f">{PENDING_MAX_AGE_H} sa terminal olay gelmedi — bekleyen sayılmıyor")
        return out


# tek süreç-içi makine (uvicorn süreci); testler kendi örneğini kurar
MACHINE: MirrorOrderStateMachine | None = None


def machine() -> MirrorOrderStateMachine:
    global MACHINE
    if MACHINE is None:
        MACHINE = MirrorOrderStateMachine()
    return MACHINE


def stream_health(st: dict | None = None) -> dict:
    """DÜRÜST akış sağlığı — panonun/uzlaştırmanın okuması gereken tek kaynak. Ham `stream_ok` boole'si
    dinleyici öldüğünde diskte donar; ORTAK yasa (streamhealth.health_snapshot) onu NABIZLA çarpar."""
    st = store.read_json(STATE_FILE, {}) if st is None else st
    return streamhealth.health_snapshot(st)


def decay_stale_stream_flag() -> bool:
    """Bayat `stream_ok: true`yu diskte FALSE'a çeker; düzeltildiyse True döner. Yazma mirror'a ait
    (streamhealth disk bilmez): panonun okuduğu dosya BAŞKA bir sürecin ölmesiyle donmuş olabilir."""
    st = store.read_json(STATE_FILE, {})
    changed, new_st = streamhealth.decay_stale_flag(st, "mirror_stream")
    if changed:
        store.write_json(STATE_FILE, new_st)
    return changed


def pending_symbols_snapshot() -> set:
    """Süreç-dışı okuyucular (döngü ayrı süreçte koşarsa) için dosyadan anlık bekleyen kümesi.
    v68: burası döngünün (loop.py) HER turda bu modüle giren tek kancası; bayat yeşil bayrağı burada
    düşürüyoruz ki pano, dinleyici süreci ölmüş olsa bile gerçeği göstersin."""
    decay_stale_stream_flag()
    st = store.read_json(STATE_FILE, {})
    cutoff = (dt.datetime.now(dt.timezone.utc)
              - dt.timedelta(hours=PENDING_MAX_AGE_H)).isoformat(timespec="seconds")
    return {v.get("symbol") for v in (st.get("orders") or {}).values()
            if str(v.get("status", "")).lower() in PENDING and v.get("symbol")
            and str(v.get("updated") or "") >= cutoff}        # aynı bayatlık ufku (turu 18)


class MirrorStreamListener:
    """asyncio dinleyicisi — uvicorn'un mevcut event-loop'unda görev olarak koşar. Kimlik doğrular,
    trade_updates'e abone olur, olayları durum makinesine akıtır. Reconnect/backoff/down-saati YASASI
    artık `streamhealth.run_stream`ten (kopya YOK); bu sınıf `spec` protokolünü sağlar (url/session/
    on_grace_exceeded). v68 düzeltmeleri (down-saati tur başında sıfırlanmaz; 'up' ilk KANITLI veride)
    ortak sürücüde tek yerde yaşar.

    Kopuşun kaynağı yanlış hostname DEĞİLDİ: aynı dakikalarda tüm bar kaynakları da boş dönüyordu —
    makine ağı gitmişti (uyku/wifi). Kod ağı geri getiremez; GÖRÜNÜR kılar."""

    connect_kwargs = {"ping_interval": 20, "ping_timeout": 20}

    def __init__(self, sm: MirrorOrderStateMachine | None = None):
        self.sm = sm or machine()
        self.health = self.sm.health          # ortak sağlık nesnesi (run_stream `spec.health` bekler)
        self._stop = asyncio.Event()
        self._alive = False          # KANITLANMIŞ çift yönlü bağlantı (sunucudan veri geldi mi?)
        self._down_since: dt.datetime | None = None
        self._cancel_fired = False   # devre-kesici kesinti BAŞINA bir kez (her denemede değil)

    # --- run_stream(spec) protokolü ---
    @property
    def stop_event(self) -> asyncio.Event:
        return self._stop

    def url(self) -> str:
        return self._url()

    async def pause(self, s: float) -> None:
        # modül-global _pause'u ÇAĞRI ANINDA çözer (test `ms._pause` monkeypatch'i görünür)
        return await _pause(s)

    def on_grace_exceeded(self) -> None:
        self._maybe_cancel_entries()

    async def session(self, ws, mark_alive) -> None:
        """Emre-özgü oturum: auth + trade_updates aboneliği + `apply` akıtımı. Reconnect/backoff bu
        fonksiyonda DEĞİL — o ortak `run_stream`'te. `mark_alive` ilk KANITLI (auth'lı) veride çağrılır."""
        await ws.send(json.dumps({"action": "auth",
                                  "key": secrets.get("ALPACA_PAPER_KEY") or "",
                                  "secret": secrets.get("ALPACA_PAPER_SECRET") or ""}))
        await ws.send(json.dumps({"action": "listen", "data": {"streams": ["trade_updates"]}}))
        async for raw in ws:
            if self._stop.is_set():
                break
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, TypeError):  # sessiz-yutma: yardımcı G/Ç; çağıran yokluğu yedekle karşılar
                continue
            unauth = msg.get("stream") == "authorization" and \
                (msg.get("data") or {}).get("status") == "unauthorized"
            if not unauth:
                # v68: 'up' soket açılınca değil, sunucudan İLK veri gelince. mark_alive idempotent.
                mark_alive()
            if msg.get("stream") == "trade_updates":
                d = msg.get("data") or {}
                self.sm.apply(str(d.get("event", "")), d.get("order") or {})
            elif unauth:
                obs.warn("mirror_stream_unauthorized")
                await _pause(300)   # yanlış anahtarla çekiçleme yok
                break

    async def run(self) -> None:
        await streamhealth.run_stream(self)

    @staticmethod
    def _url() -> str:
        from .adapters.alpaca import _paper_base
        base = _paper_base()
        if base.startswith("https://"):
            return "wss://" + base[len("https://"):] + STREAM_PATH
        if base.startswith("wss://"):
            return base + STREAM_PATH
        # Şemasız/bozuk taban gaierror'un EN SİNSİ kaynağıdır: yarım bir hostname çözülmeye çalışılır ve
        # hata kayıtta "ağ yok"tan ayırt edilemez. Kilitli PAPER hostuna dön, söyle. Kimlik sızdırmadan
        # yalnız BİÇİM basılır: şema://host/yol — kullanıcı-adı/parola ve sorgu dizesi ASLA girmez.
        try:
            from urllib.parse import urlparse
            _p = urlparse(base if "://" in base else f"//{base}")
            _bicim = f"{_p.scheme or 'ŞEMA-YOK'}://{_p.hostname or '?'}{_p.path or ''}"
        except Exception:  # sessiz-yutma: teşhis etiketi üretilemedi — uyarının KENDİSİ düşmeli, süslemesi için susulmaz
            _bicim = "çözümlenemedi"
        obs.warn("mirror_stream_bad_base", gorulen=_bicim,
                 detail="uç nokta şemasız/bozuk — kilitli PAPER hostuna dönüldü (anahtar basılmaz)")
        return "wss://paper-api.alpaca.markets" + STREAM_PATH

    def _maybe_cancel_entries(self) -> None:
        """Kopuş devre-kesicisi (OPSİYONEL, varsayılan KAPALI): yalnız DOLMAMIŞ GİRİŞ emirleri iptal
        edilir. Koruma (stop/TP) bacaklarına ASLA dokunulmaz — açık pozisyonu korumasız bırakmak
        güvenli-başarısızlık değildir."""
        import os
        if os.environ.get("MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES") != "1":
            return
        # DENETİM turu 18: burada iptal mantığının İKİNCİ bir kopyası vardı (sahiplik yok + partially_filled
        # dahil). Tek yasa: adaptörün denetlenmiş yolu (önek süzgeci + filled_qty<=0 + koruma bacağı
        # dokunulmazlığı). Kopya silindi.
        try:
            from .adapters import alpaca
            res = alpaca.cancel_open_entries()
            for c in res.get("cancelled", []):
                obs.warn("disconnect_entry_canceled", ticker=c.get("symbol"),
                         coid=str(c.get("coid", ""))[:24])
            if res.get("kept") or res.get("foreign"):
                obs.log("disconnect_cancel_spared", kept=len(res.get("kept", [])),
                        foreign=len(res.get("foreign", [])))
        except Exception as e:
            obs.warn("disconnect_cancel_failed", error=f"{type(e).__name__}: {e}"[:120])

    def stop(self) -> None:
        self._stop.set()
