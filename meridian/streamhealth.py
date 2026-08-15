"""streamhealth.py — WS dinleyicilerinin ORTAK YASASI: bayatlık/nabız/backoff/down-reassert/reconnect.

NE YAPAR: bir WebSocket akışının sağlık disiplini burada TEK yerde yaşar ve hem `mirror_stream`
(yürütme: trade_updates) hem `marketstream` (piyasa verisi: dakikalık bar) onu İÇE AKTARARAK
kullanır — `mirror_stream.next_backoff IS streamhealth.next_backoff` (aynı nesne). Neden ayrı modül
(operatör kararı — ERADİKASYON, hafifletme değil): bu kod tabanının baskın kusuru "aynı yasanın iki
uygulaması, sessizce ayrışmış"tır; mirror'ın 54→2 `down` kusuru (kopuş saati her turda sıfırlanıyor,
"ne kadardır kopuk" yalnız son uykuyu ölçüyordu) tam da bu durumsal yasada yaşadı. İkinci akış onu
kopyalasaydı en riskli kodu korumasız ikiye bölerdik; tek nesne divergence'ı yapısal imkânsız kılar
(`test_streamhealth_parity_v84` bunu kimlik `is` + AST-yokluk taramasıyla kilitler).

KİLİT GİRİŞLER: StreamHealth (set_stream: durum KENARI, yalnız değişimde kayıt; touch: NABIZ —
damgayı tazeler + süregelen kopuşu DOWN_REASSERT_S'te bir yeniden basar; hydrate: bayat stream_ok
taze nabız yoksa false'a çekilir — "3 gün eski damgayla ilk saniyeden yeşil" kusuru),
run_stream(spec) (ortak reconnect sürücüsü; spec = stop_event/health/url()/session(ws, mark_alive)/
on_grace_exceeded()/pause()), next_backoff (saf; DNS düşmüşse taban DNS_BACKOFF_FLOOR),
health_snapshot / decay_stale_flag (ham bayrak × nabız tazeliği), sabitler: HEARTBEAT_S,
STALE_AFTER_S, DOWN_REASSERT_S, GRACE_SECONDS, BACKOFF_START/MAX.

DEĞİŞMEZLER: 'up' soket açılınca DEĞİL, sunucudan ilk KANITLI (auth'lı) veri gelince basılır —
kabul edilip hemen kapatılan soket canlı okunmaz. Kopuş saati tur başında sıfırlanmaz; kesinti
boyunca AYNI saat. Nabız bağımsız görevdedir (olay akışına bağlansa sakin bir gün "akış öldü"
okunurdu); damga donarsa okuyucular STALE_AFTER_S sonra bayrağı yeşil saymaz. Ham `stream_ok`
tek başına okunmaz — health_snapshot nabızla çarpar.

OKUR/YAZAR: store/disk BİLMEZ — kalıcılık StreamHealth'e enjekte edilen `persist` geri-çağrısıdır
(mirror'da write_json: yürütme gerçeği restart-güvenli; market'ta no-op: telemetri uçucu). Olaylar
`{prefix}_up/_down/_stale_flag/...` adlarıyla obs defterine yazılır; disk-vs-bellek farkı tek
parametre, yasa hâlâ tek.
"""
from __future__ import annotations
import asyncio
import datetime as dt
from typing import Callable

from . import obs

# --- SABİTLER (mirror_stream'den taşındı; mirror aynı nesneyi re-export eder) -------------------
HEARTBEAT_S = 20            # bağlıyken bu aralıkla tazelik damgası (ws ping_interval ile aynı mertebe)
STALE_AFTER_S = 90         # damga bundan eskiyse stream_ok ARTIK KANIT DEĞİL → false okunur
DOWN_REASSERT_S = 300      # kopuş sürerken bu aralıkla YENİDEN kayda geçer (tek kenar değil, süregelen)
GRACE_SECONDS = 60         # bu süreden uzun kopuş → stream_ok=false (şerit amber)
BACKOFF_START = 1.0
BACKOFF_MAX = 60.0
DNS_BACKOFF_FLOOR = 5.0    # ad çözümlemesi düşmüşse 1 sn denemeler saf gürültü — ağ yok
DNS_MARKERS = ("gaierror", "getaddrinfo", "name or service not known", "nodename nor servname",
               "temporary failure in name resolution", "network is unreachable",
               "no address associated")


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _age_s(iso) -> float | None:
    """iso damganın yaşı (sn); okunamıyorsa None = 'tazelik BİLİNMİYOR' (taze DEĞİL)."""
    if not iso:
        return None
    try:
        return (_now() - dt.datetime.fromisoformat(str(iso))).total_seconds()
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz damga zaten 'taze değil' — çağıran bunu bayat sayıp bayrağı düşürür
        return None


def _fresh(iso) -> bool:
    age = _age_s(iso)
    return age is not None and age <= STALE_AFTER_S


def next_backoff(current: float, error: str = "") -> float:
    """Bir sonraki yeniden-deneme aralığı. Saf fonksiyon — testler gerçek beklemeden doğrular.

    DNS düşmüşse (gaierror) taban DNS_BACKOFF_FLOOR: ÇÖZÜLEMEYEN bir hostu 1-2-4 sn sorgulamak ne
    bağlantıyı hızlandırır ne bilgi üretir, yalnız kaydı doldurup asıl sinyali gömer."""
    nxt = min(BACKOFF_MAX, max(BACKOFF_START, float(current)) * 2.0)
    if any(m in (error or "").lower() for m in DNS_MARKERS):
        nxt = max(nxt, DNS_BACKOFF_FLOOR)
    return min(BACKOFF_MAX, nxt)


async def _pause(seconds: float) -> None:
    """Yeniden-deneme beklemesi tek bir yerden geçer — testler burayı değiştirip GERÇEK backoff
    dizisini ölçer (uyku taklidi değil, çağrılan değerler)."""
    await asyncio.sleep(seconds)


def _ssl_context():
    """macOS framework Python'un varsayılan bağlamı CA'sızdır — certifi varsa onu kullan (httpx'in
    çalışma sebebi de certifi)."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # sessiz-yutma: certifi isteğe bağlı; yokluğunda sistemin varsayılan CA bağlamına düşülür
        return ssl.create_default_context()


def health_snapshot(st: dict) -> dict:
    """DÜRÜST akış sağlığı — panonun/uzlaştırmanın okuması gereken tek şekil. Ham `stream_ok` boole'si
    TEK BAŞINA yalan söyleyebilir (dinleyici ölse dosyada `true` donar); burada NABIZLA çarpılır:
    nabız bayatsa ok=False."""
    checked = st.get("stream_checked_at")
    stale = not _fresh(checked)
    flag = bool(st.get("stream_ok", False))
    return {"ok": flag and not stale, "flag": flag, "stale": stale,
            "checked_at": checked, "checked_age_s": _age_s(checked),
            "down_since": st.get("down_since"), "last_error": st.get("last_error"),
            "last_event_ts": st.get("last_event_ts")}


def decay_stale_flag(st: dict, prefix: str) -> tuple[bool, dict | None]:
    """Bayat `stream_ok: true`yu FALSE'a çekmeli mi? `(changed, güncellenmiş_st)` döner; YAZMA çağırana
    ait (bu modül disk bilmez). Süreç ölmüşse bayrağı düşürecek yazar da ölmüştür — bu yüzden düzeltme,
    dosyaya her tur DOKUNAN canlı okuyucudan tetiklenir."""
    h = health_snapshot(st)
    if not (h["flag"] and h["stale"]):
        return False, None
    st = dict(st)
    st["stream_ok"] = False
    st["down_since"] = st.get("down_since") or _now_iso()
    st["last_error"] = "nabız bayat — akış canlı sayılamaz"
    st["updated"] = _now_iso()
    obs.warn(f"{prefix}_flag_decayed", checked_at=h["checked_at"], age_s=int(h["checked_age_s"] or 0),
             detail="pano 'canlı' okuyordu ama akışın nabzı yoktu — bayrak düşürüldü")
    return True, st


class StreamHealth:
    """Bir WS akışının bayatlık-damgalı sağlık DURUMU. mirror'da MirrorOrderStateMachine'in sağlık
    yarısıydı; çıkarıldı ki marketstream KOPYALAMASIN. `persist` enjekte edilir (mirror=write_json,
    market=no-op); `prefix` olay adlarını türetir (`{prefix}_up/_down/_stale_flag`); `role` yalnız
    insan metnidir. Yapısal alanlar iki akışta ÖZDEŞtir."""

    def __init__(self, prefix: str, role: str, persist: Callable[[], None], lock=None):
        import threading
        self.prefix = prefix
        self.role = role
        self._persist_cb = persist
        self._lock = lock or threading.Lock()
        self.stream_ok = False
        self.checked_at: str | None = None
        self.down_since: str | None = None
        self.last_error: str = ""
        self._last_reassert: float = 0.0

    def hydrate(self, st: dict) -> None:
        """Diskten diriltme. v68 yasası: `stream_ok` OLDUĞU GİBİ diriltilmez — TAZE bir nabız yoksa
        false'a çekilir (canlıda `stream_ok:true` + 3 gün eski `checked_at` 'WS canlı' diyordu; süreç
        yeniden başlasa bile ilk saniyeden yeşil). Bayrak ancak taze nabızla birlikte geçerli."""
        self.checked_at = st.get("stream_checked_at")
        self.down_since = st.get("down_since")
        self.last_error = st.get("last_error") or ""
        was_ok = bool(st.get("stream_ok", False))
        if was_ok and not _fresh(self.checked_at):
            import time as _t
            self.stream_ok = False
            self.down_since = self.down_since or _now_iso()
            self.last_error = "bayat stream_ok bayrağı (nabız yok) — false'a çekildi"
            # `_last_reassert`i ŞİMDİ tohumla (çekişmeli inceleme bulgusu): yoksa 0.0 kalır ve İLK touch()
            # `monotonic()-0 >= DOWN_REASSERT_S` ile HEMEN sahte bir `{prefix}_down` (down_for_s=0) basardı —
            # bağlantı gelmeden ~1 sn önce. Canlı defterde 5 kez görüldü; kurt masalı, honest-down sayacını kirletir.
            self._last_reassert = _t.monotonic()
            self._persist_cb()
            obs.warn(f"{self.prefix}_stale_flag", checked_at=self.checked_at,
                     detail="diskteki stream_ok'in arkasında taze nabız yoktu — pano yanlış yeşildi")
        else:
            self.stream_ok = was_ok

    def to_dict(self) -> dict:
        return {"stream_ok": self.stream_ok, "stream_checked_at": self.checked_at,
                "down_since": self.down_since, "last_error": self.last_error}

    def set_stream(self, ok: bool, error: str = "") -> None:
        """Durum KENARI. Yalnız değişimde kayıt basar; kesintinin SÜREKLİ görünürlüğü touch() işidir.

        `last_error` GEÇMİŞ DEĞİL, ŞU ANKİ durumun nedenidir. Toparlanmada temizlenmezse sağlıklı
        akışın üstünde eski hata asılı kalır ve okuyan 'şu an bozuk' sanar. Kaybolan bilgi YOK: kesinti
        events.jsonl'da `{prefix}_down` satırlarıyla, toparlanma da adıyla durur."""
        import time as _t
        with self._lock:
            self.checked_at = _now_iso()
            onceki_hata = self.last_error
            if ok:
                self.last_error = ""              # "ok" bir durumdur; durumun güncel hatası olmaz
            elif error:
                self.last_error = error[:160]
            # `down_since is None` de bir KENARDIR: hiç bağlanamamış bir dinleyici eskiden tek satır bile
            # basmazdı — "hiç açılmadı" ile "kopuk" aynı sessizlik.
            if self.stream_ok != ok or (not ok and not self.down_since):
                self.stream_ok = ok
                self.down_since = None if ok else _now_iso()
                self._last_reassert = _t.monotonic() if not ok else 0.0
                self._persist_cb()
                if ok:
                    obs.log(f"{self.prefix}_up", recovered_from=onceki_hata or None)
                else:
                    obs.warn(f"{self.prefix}_down", error=self.last_error or None)
            else:
                self._persist_cb()

    def touch(self, error: str = "") -> bool:
        """NABIZ — mevcut durumu DEĞİŞTİRMEDEN tazelik damgasını yeniler. İki iş: (1) `checked_at`i
        tazeler (damga donarsa okuyucular STALE_AFTER_S sonra yeşil saymaz — 'ölü akış, yeşil şerit'
        tam buydu), (2) kopuş SÜRERKEN DOWN_REASSERT_S'te bir `{prefix}_down` YENİDEN basar. Kararı
        (up/down) bilerek vermez — o, reconnect döngüsünün ve GRACE_SECONDS'ın işi."""
        import time as _t
        with self._lock:
            self.checked_at = _now_iso()
            if error:
                self.last_error = error[:160]
            self._persist_cb()
            due = (not self.stream_ok) and bool(self.down_since) and \
                (_t.monotonic() - self._last_reassert) >= DOWN_REASSERT_S
            if due:
                self._last_reassert = _t.monotonic()
        if due:
            obs.warn(f"{self.prefix}_down", error=self.last_error or None,
                     down_for_s=int(_age_s(self.down_since) or 0),
                     detail="kopuş SÜRÜYOR — görünürlük hâlâ yok")
        return due


async def _heartbeat_loop(spec) -> None:
    """Bağımsız NABIZ görevi. `async for ws` saatlerce sessiz kalabilir; nabzı olay akışına bağlarsak
    sakin bir gün 'akış öldü' okunur. Ters yönü daha önemli: bu görev run ile ölürse damga donar ve
    okuyucular bayrağı yeşil saymaz (STALE_AFTER_S sonra)."""
    while not spec.stop_event.is_set():
        try:
            spec.health.touch()
        except Exception as e:
            obs.warn(f"{spec.health.prefix}_heartbeat_failed", error=f"{type(e).__name__}: {e}"[:120])
        try:
            await asyncio.wait_for(spec.stop_event.wait(), timeout=HEARTBEAT_S)
        except asyncio.TimeoutError:  # sessiz-yutma: zaman aşımı BEKLENEN akış — nabız aralığı doldu demek
            pass


async def run_stream(spec) -> None:
    """ORTAK reconnect sürücüsü — mirror ile market AYNI koddan koşar. `spec` emre-özgü parçaları
    sağlar (url/session/on_grace_exceeded/pause); backoff/down-saati/grace/reassert YASASI burada
    TEK yerde. `spec` protokolü:
        stop_event, health(StreamHealth), _alive, _down_since, _cancel_fired, connect_kwargs,
        url()->str, async session(ws, mark_alive), on_grace_exceeded(), async pause(s)

    v68 çekirdek düzeltmesi (down-saati tur BAŞINDA sıfırlanmaz) burada TEK yerde yaşar:
    `spec._down_since = spec._down_since or _now()` — kesinti boyunca AYNI saat. 54→2 `down` kusuru
    bunun eksikliğindendi; ikinci bir akış kopyalasaydı yeniden ekmiş olurduk."""
    import websockets
    _ssl = _ssl_context()
    backoff = BACKOFF_START
    hb = asyncio.ensure_future(_heartbeat_loop(spec))

    def mark_alive():
        """KANITLANMIŞ çift-yönlü/auth'lı canlılık. 'up' ARTIK soket açılınca değil, sunucudan İLK
        (kimliği kanıtlanmış) veri gelince basılır — kabul edilip hemen kapatılan soket 'canlı'
        okunmasın (v68 kusuru). İdempotent: her mesajda güvenle çağrılır."""
        nonlocal backoff
        if not spec._alive:
            spec._alive = True
            spec._cancel_fired = False
            spec._down_since = None
            backoff = BACKOFF_START
            spec.health.set_stream(True)

    try:
        while not spec.stop_event.is_set():
            err = ""
            try:
                async with websockets.connect(spec.url(), ssl=_ssl, **spec.connect_kwargs) as ws:
                    await spec.session(ws, mark_alive)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                err = f"{type(e).__name__}: {e}"[:160]
                obs.warn(f"{spec.health.prefix}_error", error=err)
            spec._alive = False
            if spec.stop_event.is_set():
                break
            # KOPUŞ SAATİ — v68'in çekirdek düzeltmesi. Eskiden tur BAŞINDA None'lanıyordu, yani "ne
            # kadardır kopuk" ölçüsü yalnız SON uykuyu ölçüyordu ve eşik pratikte "backoff>=60"a
            # dönüşüyordu (54 hataya 2 down). Saat artık kesinti boyunca AYNI saat.
            spec._down_since = spec._down_since or _now()
            down_for = (_now() - spec._down_since).total_seconds()
            if down_for >= GRACE_SECONDS:
                spec.health.set_stream(False, err)   # kenar; sürerken touch() yeniden kayda geçirir
                if not spec._cancel_fired:
                    spec._cancel_fired = True         # kesinti başına BİR kez
                    spec.on_grace_exceeded()
            else:
                spec.health.touch(err)                # damga tazelensin, karar (grace) değişmesin
            await spec.pause(backoff)
            backoff = next_backoff(backoff, err)
    finally:
        hb.cancel()
        spec._alive = False
        spec.health.set_stream(False)
