"""test_mirror_health_v68.py — yürütme-görünürlüğü katmanının DÜRÜSTLÜĞÜ (2026-07-22).

CANLI KANIT (state/events.jsonl + state/mirror_orders.json):
  * 54x `mirror_stream_error` (çoğu `gaierror`) karşısında YALNIZ 2x `mirror_stream_down`;
  * dosyada `stream_ok: true` dururken `last_event_ts` ÜÇ GÜN eski — pano "WS canlı" diyordu.
Kesintinin sebebi yanlış hostname değildi: aynı dakikalarda `bar_sources_all_empty` tüm evren için
düşüyor ve kayıtta 15-35 dakikalık boşluklar var → makinenin ağı/uykusu. Kod ağı geri getiremez;
bu dosya ağın gittiğini GÖRÜNÜR kılmanın testidir.

Dört yasa:
  H1 DNS/bağlantı hatası kesintinin TAMAMI boyunca 'ok değil' okunmalı — bir kez değil, SÜREKLİ.
  H2 Yeniden bağlanma dönmemeli: gerçek backoff dizisi ölçülür (DNS'te taban daha yüksek).
  H3 Düzelen akış 'ok'a döner ama BAYAT dolumları yeniden uygulamaz (terminal emici).
  H4 Pozitif kontrol: sağlık kontrolü boş yere yeşil değil — gerçekten canlı akış True okunur.

Tüm taşıma taklittir; hiçbir gerçek soket açılmaz, hiçbir emir gönderilmez, fikstürde sır yoktur.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import socket

import pytest

from meridian import mirror_stream as ms, store


# ---------- taklit taşıma (ağ YOK) ----------
class _FakeWS:
    """Sunucudan gelen mesajları sırayla veren asenkron bağlam; `send` sessizce yutulur."""

    def __init__(self, messages):
        self._messages = list(messages)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def send(self, payload):
        self.sent.append(payload)

    def __aiter__(self):
        async def gen():
            for m in self._messages:
                yield m
        return gen()


class _Transport:
    """websockets.connect yerine geçer. `script` her bağlantı denemesi için ya fırlatılacak bir
    istisna ya da sunucudan dönecek mesaj listesi verir."""

    def __init__(self, script):
        self.script = list(script)
        self.attempts = 0

    def connect(self, url, **kw):
        self.attempts += 1
        step = self.script.pop(0) if self.script else socket.gaierror(8, "nodename nor servname")
        if isinstance(step, BaseException):
            raise step
        return _FakeWS(step)


def _run(coro):
    """pytest-asyncio kurulu değil — döngüyü elle sürüyoruz (bağımlılık eklemeden asenkron kilit)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _install(monkeypatch, transport):
    import sys
    import types
    mod = types.ModuleType("websockets")
    mod.connect = transport.connect
    monkeypatch.setitem(sys.modules, "websockets", mod)


def _sm(_sandbox):
    ms.MACHINE = None
    return ms.MirrorOrderStateMachine()


def _events(name):
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == name]


def _order(coid="P-2026-07-22-AAA", sym="AAA", status="filled", filled="10"):
    return {"client_order_id": coid, "symbol": sym, "status": status, "qty": "10",
            "filled_qty": filled, "filled_avg_price": "12.5", "id": "o1"}


def _tu(event, order):
    return '{"stream": "trade_updates", "data": {"event": "%s", "order": %s}}' % (
        event, __import__("json").dumps(order))


# ---------- H2: backoff DÖNMEZ ----------
def test_h2_backoff_actually_grows_and_is_capped():
    """Saf fonksiyon: 54 hatanın ilk yarısı 1-2-4 sn aralıklarla ÇÖZÜLEMEYEN bir hostu sorgulamaktı."""
    seq, b = [], ms.BACKOFF_START
    for _ in range(9):
        b = ms.next_backoff(b, "ConnectionClosedError: keepalive ping timeout")
        seq.append(b)
    assert seq[:5] == [2.0, 4.0, 8.0, 16.0, 32.0], seq
    assert seq[-1] == ms.BACKOFF_MAX and max(seq) == ms.BACKOFF_MAX, "tavan aşılmamalı"
    assert all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1)), "backoff geri gitmemeli"


def test_h2b_dns_failure_backs_off_harder_than_a_normal_drop():
    dns = "gaierror: [Errno 8] nodename nor servname provided, or not known"
    assert ms.next_backoff(1.0, dns) >= ms.DNS_BACKOFF_FLOOR
    assert ms.next_backoff(1.0, dns) > ms.next_backoff(1.0, "ConnectionClosedError: x"), \
        "ad çözülemiyorken saniyede bir denemek bilgi üretmez, yalnız kaydı doldurur"


def test_h2c_reconnect_loop_sleeps_the_backoff_it_promises(sandbox_state, monkeypatch):
    """DAVRANIŞSAL kilit: döngü GERÇEKTEN backoff kadar bekliyor mu (dönüyor mu)?"""
    sm = _sm(sandbox_state)
    tr = _Transport([socket.gaierror(8, "nodename nor servname provided") for _ in range(6)])
    _install(monkeypatch, tr)
    slept = []

    async def fake_pause(s):
        slept.append(s)
        if len(slept) >= 5:
            lis.stop()
    monkeypatch.setattr(ms, "_pause", fake_pause)
    lis = ms.MirrorStreamListener(sm)
    _run(lis.run())
    assert len(slept) >= 5
    assert slept == sorted(slept) and slept[-1] > slept[0], f"backoff büyümüyor: {slept}"
    assert slept[0] >= ms.BACKOFF_START and max(slept) <= ms.BACKOFF_MAX
    assert tr.attempts == len(slept), "her uykuda tam bir deneme — sıkı döngü yok"
    assert slept[1] >= ms.DNS_BACKOFF_FLOOR, f"DNS kesintisinde taban uygulanmadı: {slept}"


# ---------- H1: kesinti SÜREKLİ görünür ----------
def test_h1_dns_outage_marks_stream_not_ok_for_the_whole_outage(sandbox_state, monkeypatch):
    sm = _sm(sandbox_state)
    sm.set_stream(True)                       # kesintiden önce akış canlıydı
    assert ms.stream_health()["ok"] is True

    tr = _Transport([socket.gaierror(8, "nodename nor servname provided") for _ in range(8)])
    _install(monkeypatch, tr)

    async def fake_pause(s):
        # kesintiyi HIZLANDIR: saat ileri sarılır, uyku sıfır maliyet
        lis._down_since = lis._down_since - dt.timedelta(seconds=s * 30)
        if tr.attempts >= 4:
            lis.stop()
    monkeypatch.setattr(ms, "_pause", fake_pause)
    lis = ms.MirrorStreamListener(sm)
    _run(lis.run())

    assert sm.stream_ok is False
    assert _events("mirror_stream_down"), "kesinti hiç kayda geçmedi"
    # ve panonun okuduğu DOSYA da yalan söylemiyor
    h = ms.stream_health()
    assert h["ok"] is False and h["flag"] is False
    assert h["down_since"] and h["last_error"], "kopuşun ne zaman ve neden olduğu dosyada durmalı"


def test_h1b_outage_is_re_asserted_not_signalled_once(sandbox_state):
    """54 hataya 2 satır düşmesinin sebebi: `set_stream` yalnız KENAR basıyordu. Kesinti sürerken
    sinyal de sürmeli, yoksa şerit uzun kesintide sessizleşir."""
    sm = _sm(sandbox_state)
    sm.set_stream(True)
    sm.set_stream(False, "gaierror: nodename nor servname")
    assert len(_events("mirror_stream_down")) == 1
    sm.touch()                                  # aralık dolmadan: tekrar YOK (log seli olmaz)
    assert len(_events("mirror_stream_down")) == 1
    import time
    sm._last_reassert = time.monotonic() - ms.DOWN_REASSERT_S - 1
    assert sm.touch() is True                   # aralık doldu: kesinti YENİDEN kayda geçer
    evs = _events("mirror_stream_down")
    assert len(evs) == 2 and evs[-1].get("down_for_s") is not None, \
        "yeniden bildirim kesintinin SÜRESİNİ taşımalı"


def test_h1c_dead_listener_cannot_leave_a_green_flag_on_disk(sandbox_state):
    """CANLI KUSURUN BİREBİR KOPYASI: dosyada `stream_ok: true` + nabız yok. Dinleyici öldüyse
    düzeltmeyi yapacak yazar da ölmüştür; okuyucu tarafı yeşili düşürmek zorunda."""
    stale = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(seconds=ms.STALE_AFTER_S * 20)).isoformat(timespec="seconds")
    store.write_json(ms.STATE_FILE, {"orders": {}, "stream_ok": True,
                                     "last_event_ts": "2026-07-19T17:15:15+00:00",
                                     "stream_checked_at": stale, "updated": stale})
    assert ms.stream_health()["ok"] is False, "nabızsız bayrak kanıt değildir"
    assert ms.decay_stale_stream_flag() is True
    # api.py HAM boole'yi okuyor → diskteki değerin kendisi düzelmiş olmalı
    assert store.read_json(ms.STATE_FILE, {})["stream_ok"] is False
    assert _events("mirror_stream_flag_decayed")
    # döngünün her turda çağırdığı kanca da aynı düzeltmeyi tetikler
    store.write_json(ms.STATE_FILE, {"orders": {}, "stream_ok": True, "stream_checked_at": stale})
    ms.pending_symbols_snapshot()
    assert store.read_json(ms.STATE_FILE, {})["stream_ok"] is False


def test_h1d_restart_does_not_resurrect_a_stale_green_flag(sandbox_state):
    stale = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(hours=6)).isoformat(timespec="seconds")
    store.write_json(ms.STATE_FILE, {"orders": {}, "stream_ok": True, "stream_checked_at": stale})
    sm = _sm(sandbox_state)                     # = süreç yeniden başladı
    assert sm.stream_ok is False, "hiç bağlantı kurmamış bir süreç 'WS canlı' diyemez"
    assert store.read_json(ms.STATE_FILE, {})["stream_ok"] is False
    assert _events("mirror_stream_stale_flag")


# ---------- H4: POZİTİF KONTROL — kontrol boş yere yeşil değil ----------
def test_h4_positive_control_a_genuinely_live_stream_reads_ok(sandbox_state):
    sm = _sm(sandbox_state)
    sm.set_stream(True)
    h = ms.stream_health()
    assert h["ok"] is True and h["stale"] is False and h["flag"] is True
    assert h["checked_age_s"] is not None and h["checked_age_s"] < ms.STALE_AFTER_S
    # ve nabız attıkça yeşil KALIR (sessiz bir gün 'akış öldü' diye okunmamalı)
    sm.touch()
    assert ms.stream_health()["ok"] is True


def test_h4b_positive_control_health_is_not_hardwired(sandbox_state):
    """Aynı fonksiyon aynı girdi sınıfında HAYIR da diyebiliyor mu? (vakum kontrolü)"""
    sm = _sm(sandbox_state)
    sm.set_stream(True)
    assert ms.stream_health()["ok"] is True
    sm.set_stream(False, "gaierror")
    assert ms.stream_health()["ok"] is False


def test_h4c_socket_that_never_speaks_is_not_reported_live(sandbox_state, monkeypatch):
    """'up' soket AÇILINCA değil, sunucudan İLK VERİ gelince basılmalı: kabul edilip hemen kapanan
    bir bağlantı eskiden 'WS canlı' okunurdu."""
    sm = _sm(sandbox_state)
    tr = _Transport([[]])                       # bağlanır, tek kelime etmez, kapanır
    _install(monkeypatch, tr)

    async def fake_pause(s):
        lis.stop()
    monkeypatch.setattr(ms, "_pause", fake_pause)
    lis = ms.MirrorStreamListener(sm)
    _run(lis.run())
    assert sm.stream_ok is False
    assert not _events("mirror_stream_up"), "veri gelmeden 'canlı' denemez"


# ---------- H3: düzelen akış + BAYAT DOLUM TEKRARI YOK ----------
def test_h3_recovered_stream_returns_to_ok(sandbox_state, monkeypatch):
    sm = _sm(sandbox_state)
    tr = _Transport([socket.gaierror(8, "nodename nor servname"),
                     [_tu("fill", _order())]])
    _install(monkeypatch, tr)

    async def fake_pause(s):
        await asyncio.sleep(0)          # olay döngüsüne sıra ver — gerçek beklemeyi taklit etme
    monkeypatch.setattr(ms, "_pause", fake_pause)
    lis = ms.MirrorStreamListener(sm)

    async def main():
        async def stopper():
            for _ in range(500):
                await asyncio.sleep(0)
                if sm.stream_ok:
                    lis.stop()
                    return
        await asyncio.gather(lis.run(), stopper())
    _run(main())
    assert _events("mirror_stream_up"), "düzelen akış 'ok'a dönmeli"
    assert sm.orders["P-2026-07-22-AAA"]["status"] == "filled"


def test_h3b_replayed_fill_is_not_applied_twice(sandbox_state):
    """GÜVENLİK: yeniden bağlanan akış aynı dolumu TEKRAR yollarsa iç kayıt bozulmamalı ve İKİNCİ
    bir sinyal doğmamalı. (Bu sınıf emir GÖNDERMEZ; tekrar mükerrer emre dönüşemez — aşağıdaki
    test_h3d bunu yapısal olarak da kilitliyor.)"""
    sm = _sm(sandbox_state)
    sm.apply("fill", _order())
    before = dict(sm.orders["P-2026-07-22-AAA"])
    n_ev = len(_events("mirror_stream_event"))
    sm.apply("fill", _order())                      # birebir tekrar
    assert sm.orders["P-2026-07-22-AAA"] == before, "tekrar defteri değiştirmemeli"
    assert len(_events("mirror_stream_event")) == n_ev, "tekrar ikinci bir sinyal üretmemeli"


def test_h3c_terminal_order_cannot_be_rewound_by_a_stale_event(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("fill", _order())
    sm.apply("new", _order(status="new", filled="0"))       # bayat/sıra-dışı olay
    assert sm.orders["P-2026-07-22-AAA"]["status"] == "filled"
    assert sm.pending_symbols() == set(), "geri sarılan emir sembolü yeniden kilitlerdi"
    assert _events("mirror_stream_stale_event"), "yok sayma SESSİZ olamaz"


def test_h3d_replayed_reject_does_not_re_alarm(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("rejected", _order(status="rejected", filled="0"))
    n = len([e for e in store.read_jsonl("events.jsonl") if "BROKER_REJECT" in str(e)])
    sm.apply("rejected", _order(status="rejected", filled="0"))
    assert len([e for e in store.read_jsonl("events.jsonl")
                if "BROKER_REJECT" in str(e)]) == n, "aynı ret ikinci kez operatörü uyandıramaz"


def test_h3e_reconnect_has_no_order_submitting_path():
    """Yapısal kilit: yeniden bağlanma yolunda emir GÖNDEREN hiçbir çağrı olamaz."""
    import inspect
    src = inspect.getsource(ms)
    for forbidden in ("submit_plan", "submit_order", "httpx.post", "httpx.put", "close_all"):
        assert forbidden not in src, f"akış katmanında emir yolu: {forbidden}"


def test_h3f_circuit_breaker_fires_once_per_outage(sandbox_state, monkeypatch):
    """Kesinti başına BİR kez: eskiden grace aşıldıktan sonra HER denemede tetikleniyordu — broker'a
    kesinti boyunca tekrar tekrar iptal çağrısı (varsayılan kapalı olsa da yanlış)."""
    sm = _sm(sandbox_state)
    fired = []
    tr = _Transport([socket.gaierror(8, "nodename nor servname") for _ in range(8)])
    _install(monkeypatch, tr)
    monkeypatch.setattr(ms.MirrorStreamListener, "_maybe_cancel_entries",
                        lambda self: fired.append(1))

    async def fake_pause(s):
        lis._down_since = lis._down_since - dt.timedelta(seconds=ms.GRACE_SECONDS * 2)
        if tr.attempts >= 5:
            lis.stop()
    monkeypatch.setattr(ms, "_pause", fake_pause)
    lis = ms.MirrorStreamListener(sm)
    _run(lis.run())
    assert len(fired) == 1, f"kesinti başına bir kez olmalı, {len(fired)} kez tetiklendi"


# ---------- DNS teşhisi: URL'nin kendisi çözülebilir olmalı ----------
def test_url_is_a_resolvable_wss_paper_url(monkeypatch, sandbox_state):
    """`gaierror`ın en sinsi sebebi boş/şemasız hostname'dir. Kilit: URL her zaman şemalı ve
    PAPER hostuna sabitli. (Anahtar/sır BASILMAZ — yalnız host doğrulanır.)

    `sandbox_state` (2026-07-22): bu test şemasız bir uç nokta besliyor; düzeltmeden ÖNCE bu
    `_url()` içinde gerçek bir `obs.warn` tetikliyordu ve yazım CANLI `state/events.jsonl`e
    düşüyordu — uygulama koşarken conftest'in sızıntı bekçisi kendini kapattığı için sessizce.
    Panodaki 33 `mirror_stream_bad_base` üretimden değil BU testten geliyordu (bkz. v72)."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "get",
                        lambda n, *a, **k: "paper-api.alpaca.markets" if n == "ALPACA_PAPER_ENDPOINT" else "k")
    url = ms.MirrorStreamListener._url()
    assert url == "wss://paper-api.alpaca.markets/stream", url
    from urllib.parse import urlparse
    assert urlparse(url).hostname == "paper-api.alpaca.markets", "boş/yarım hostname = gaierror"


# ---------- H5: DONMUŞ BAYRAK UÇLARDA DİRİLMEZ (2026-07-22) ----------
# mirror_stream dürüstleşse bile api.py ham `stream_ok`ı okumaya devam ediyordu: yalan modülde değil
# SUNUM KATMANINDA hayatta kalıyordu. Panonun gördüğü tek şey bu uçlar olduğuna göre, denetlenmesi
# gereken de bu uçlardır — modülün doğru olması panonun doğru olduğunu KANITLAMAZ.
def _frozen_flag_state(sandbox_state, days_old: int = 3) -> None:
    """Canlıda bulunan dosyanın birebir şekli: bayrak `true`, nabız YOK, son olay günler öncesi."""
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_old)).isoformat(timespec="seconds")
    store.write_json("mirror_orders.json", {"orders": {}, "stream_ok": True, "last_event_ts": old})


def _api(path: str):
    from fastapi.testclient import TestClient
    from meridian.api import app
    with TestClient(app) as client:
        r = client.get(path)
    assert r.status_code == 200, r.text
    return r.json()


def test_h5_endpoints_do_not_serve_the_frozen_flag(sandbox_state):
    """Üç uç da (hud · reconcile · /api/alpaca) donmuş `true`yu DÜRÜST `false` olarak servis eder."""
    _frozen_flag_state(sandbox_state)
    assert store.read_json("mirror_orders.json", {})["stream_ok"] is True, "fikstür yalanı kurmalı"

    d = _api("/api/diagnostics")
    alp = _api("/api/alpaca")
    for ad, blok in (("hud", d["hud"]), ("reconcile", d["reconcile"]), ("alpaca.stream", alp["stream"])):
        assert blok["stream_ok"] is False, f"{ad}: ölü akış canlı gösterildi (ham bayrak dirildi)"
        assert blok["stream_flag"] is True and blok["stream_stale"] is True, \
            f"{ad}: bayrağın DÜŞÜRÜLDÜĞÜ görünmüyor — operatör 'neden kopuk' diye soramaz"
    # ve üç uç AYNI gerçeği söyler: tek yanıtta iki farklı hikâye olamaz
    assert d["hud"]["stream_ok"] == d["reconcile"]["stream_ok"] == alp["stream"]["stream_ok"]


def test_h5b_endpoints_expose_how_long_the_stream_has_been_down(sandbox_state):
    """"Kopuk" bir bayrak, "43 dakikadır kopuk" bir karardır — pano ikincisini yazabilmeli."""
    sm = _sm(sandbox_state)
    sm.set_stream(True)
    sm.set_stream(False)                       # kopuş ANI dosyaya düşer
    d = _api("/api/diagnostics")["hud"]
    assert d["stream_ok"] is False and d["stream_down_since"], "kopuşun başlangıcı uçta yok"
    assert d["stream_checked_age_s"] is not None, "nabzın yaşı uçta yok"


def test_h5c_never_run_mirror_reads_unknown_not_broken(sandbox_state):
    """Üçüncü hâl: ayna hiç koşmamışsa (kanıt YOK) uç `null` der. `false` demek de bir yalandır —
    ayna kullanmayan kurulumda pano kalıcı 'WS KOPUK' gösterirdi ve alarm anlamını yitirirdi."""
    assert _api("/api/diagnostics")["hud"]["stream_ok"] is None
    assert _api("/api/alpaca")["stream"]["stream_ok"] is None


# ---------- H6: TOPARLANMA HATAYI TEMİZLER, DEFTER UNUTMAZ (2026-07-22) ----------
def test_h6_recovery_clears_the_error_but_the_ledger_keeps_it(sandbox_state):
    """CANLI KUSUR: akış toparlandıktan sonra `down_since` siliniyordu ama `last_error` KALIYORDU.
    Sonuç: sağlıklı yeşil akışın üstünde eski kesintinin hatası — "şu an bozuk" diye okunur.
    Yanlış alarmın en sinsi türü, çünkü doğru görünür ve kimse sorgulamaz.

    İki yönlü yasa: durum dosyası ANI anlatır (hata temizlenir), defter GEÇMİŞİ tutar (kayıp yok)."""
    sm = _sm(sandbox_state)
    sm.set_stream(False, "gaierror: nodename nor servname")
    kopuk = ms.stream_health()
    assert kopuk["ok"] is False and kopuk["last_error"], "kopukken neden dosyada DURMALI"

    sm.set_stream(True)                                   # akış toparlandı
    saglikli = ms.stream_health()
    assert saglikli["ok"] is True and not saglikli["down_since"]
    assert not saglikli["last_error"], \
        f"toparlanan akışta eski hata asılı kaldı: {saglikli['last_error']!r} — pano 'şu an bozuk' der"

    # ...ama KANIT KAYBOLMADI: kesinti de, neyden çıkıldığı da defterde
    assert _events("mirror_stream_down"), "kesinti defterden silinmiş — temizlik kanıt kaybına dönmüş"
    up = _events("mirror_stream_up")
    assert up and "gaierror" in str(up[-1].get("recovered_from") or ""), \
        "toparlanma satırı neyden çıkıldığını ADIYLA yazmalı, yoksa temizlik bir unutuştur"


def test_h6b_a_healthy_stream_never_carries_an_error(sandbox_state):
    """Süreç yeniden başlarken bayat bayrak düşürülür ve hata yazılır; dinleyici bağlanınca o hata
    GİTMELİ. Canlıda tam bu dizi yaşandı (13:02 yeniden başlatma → 14:04'te hâlâ eski hata)."""
    eski = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).isoformat(timespec="seconds")
    store.write_json(ms.STATE_FILE, {"orders": {}, "stream_ok": True, "last_event_ts": eski})
    sm = _sm(sandbox_state)                               # bayat bayrak → düşer + hata yazılır
    assert sm.last_error and sm.stream_ok is False

    sm.set_stream(True)                                   # dinleyici gerçekten bağlandı
    h = ms.stream_health()
    assert h["ok"] is True and not h["last_error"], \
        "yeniden başlatma hatası canlı akışın üstünde kaldı — panoda 3 gün asılı duran şey buydu"


# ---------- H7: DOĞRULANAN DEĞER İLE DÖNDÜRÜLEN DEĞER AYNI OLMALI (2026-07-22) ----------
# `_paper_base()` host denetimi için geçici bir "https://" uydurup değeri OLDUĞU GİBİ döndürüyordu.
# Şemasız bir taban her yolda AYRI arıza üretir (REST protokolü tanımaz · WS her yeniden bağlanmada
# `bad_base` basar · http'de anahtarlar açık metin gider) — hiçbiri diğerine benzemediği için kök
# neden görünmez olur. Kilit ZAYIFLAMAZ: yabancı host hâlâ PAPER_BASE'e zorlanır.
def _ep(monkeypatch, deger):
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "get",
                        lambda n, *a, **k: deger if n == "ALPACA_PAPER_ENDPOINT" else "k")
    return alpaca


def test_h7_schemeless_endpoint_is_normalised_not_passed_through(sandbox_state, monkeypatch):
    a = _ep(monkeypatch, "paper-api.alpaca.markets/v2")          # şemasız — operatörün yazabileceği hâl
    assert a._paper_base() == "https://paper-api.alpaca.markets", a._paper_base()
    assert ms.MirrorStreamListener._url() == "wss://paper-api.alpaca.markets/stream"


def test_h7b_plain_http_endpoint_is_forced_to_https_and_says_so(sandbox_state, monkeypatch):
    """`http://` doğru hosttur ama AÇIK METİNDİR: `_headers()` API anahtarlarını o bağlantıya koyar.
    Doğru makineye açık metinle anahtar göndermek, yanlış makineye göndermenin daha sessiz hâlidir.

    İki yasa birden: taşıma YÜKSELTİLİR (güvenlik) ve bu SÖYLENİR (görünürlük). Sessiz düzeltme,
    yanlış yapılandırmayı kalıcılaştırır — kimse düzeltmez çünkü kimse bilmez."""
    a = _ep(monkeypatch, "http://paper-api.alpaca.markets")
    monkeypatch.setattr(a, "_SCHEME_WARNED", False)
    assert a._paper_base() == "https://paper-api.alpaca.markets"
    ev = _events("alpaca_endpoint_scheme_upgraded")
    assert ev, "taşıma sessizce yükseltildi — operatör yanlış yapılandırmayı asla öğrenemez"
    assert "http://paper-api.alpaca.markets" in str(ev[-1].get("gorulen") or "")

    a._paper_base(); a._paper_base()                  # süreç başına BİR kez: kayıt seli olmaz
    assert len(_events("alpaca_endpoint_scheme_upgraded")) == 1


def test_h7c_the_host_lock_is_not_weakened_by_normalisation(sandbox_state, monkeypatch):
    """Normalizasyon kilidi DELMEZ: yabancı host (şemalı ya da şemasız) hâlâ PAPER_BASE'e düşer."""
    from meridian.adapters import alpaca
    for kotu in ("https://paper-api.alpaca.markets.evil.example.com",
                 "paper-api.alpaca.markets.evil.example.com",     # şemasız kandırma denemesi
                 "https://api.alpaca.markets/v2"):                # CANLI para ucu
        _ep(monkeypatch, kotu)
        assert alpaca._paper_base() == alpaca.PAPER_BASE, f"kilit delindi: {kotu}"


def test_h7d_a_healthy_endpoint_emits_no_bad_base_warning(sandbox_state, monkeypatch):
    """CANLI KUSUR: `bad_base` günde 32 kez düşüyordu. Sağlıklı uçta HİÇ düşmemeli."""
    _ep(monkeypatch, "https://paper-api.alpaca.markets/v2")
    ms.MirrorStreamListener._url()
    assert not _events("mirror_stream_bad_base"), "sağlıklı uçta yanlış alarm"


def test_h7e_when_it_does_fire_the_warning_names_what_it_saw(sandbox_state, monkeypatch):
    """Teşhis edilemeyen uyarı gürültüdür: 32 kez düştü, hangi değer olduğunu kimse bilemedi.
    Uyarı artık GÖRDÜĞÜ biçimi yazar — ama kimlik bilgisi (kullanıcı:parola) ASLA sızmaz."""
    monkeypatch.setattr(ms, "_paper_base", None, raising=False)
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "ftp://gizli:parola@paper-api.alpaca.markets/x")
    ms.MirrorStreamListener._url()
    ev = _events("mirror_stream_bad_base")
    assert ev, "bozuk taban sessizce yutuldu"
    gorulen = str(ev[-1].get("gorulen") or "")
    assert "ftp" in gorulen and "paper-api.alpaca.markets" in gorulen, gorulen
    assert "parola" not in gorulen and "gizli" not in gorulen, f"kimlik bilgisi sızdı: {gorulen}"
