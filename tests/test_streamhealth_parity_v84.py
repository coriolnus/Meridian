"""test_streamhealth_parity_v84.py — ANTİ-KOPYA / kusur-sınıfı YAPISAL bekçisi (Faz 2, 2026-07-23).

Operatörün eradike ettiği baskın kusur: "aynı yasanın İKİ uygulaması, sessizce ayrışmış". mirror'ın
54→2 `down` kusuru tam bu DURUMSAL yasada (down-saati/reconnect) yaşadı. streamhealth.py çıkarımı bunu
YAPISAL olarak imkânsız kılar: mirror ve market ORTAK yasayı İÇE AKTARIR (aynı nesne), kopyalamaz.
Bu test kopyanın yeniden girmesini kimlik (`is`) + AST-yokluk ile yakalar; bir gün biri yasayı
kopyalarsa bu test KIRILIR — ayrışma dikilmeden önce.
"""
import ast
import inspect

from meridian import streamhealth, mirror_stream, marketstream

_SHARED = ["next_backoff", "_now", "_now_iso", "_age_s", "_fresh", "_pause",
           "HEARTBEAT_S", "STALE_AFTER_S", "DOWN_REASSERT_S", "GRACE_SECONDS",
           "BACKOFF_START", "BACKOFF_MAX", "DNS_BACKOFF_FLOOR", "DNS_MARKERS"]


def test_mirror_shares_the_exact_same_law_objects():
    """mirror_stream.next_backoff IS streamhealth.next_backoff (kopya değil, AYNI nesne). İki tanım
    olmadığı için sapamazlar — parity artık bir kimlik testidir."""
    for name in _SHARED:
        assert getattr(mirror_stream, name) is getattr(streamhealth, name), \
            f"mirror_stream.{name} KOPYA olmuş — streamhealth ile AYNI nesne olmalı (divergence riski)"


def _func_defs(mod):
    tree = ast.parse(inspect.getsource(mod))
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_neither_stream_redefines_the_reconnect_law():
    """Ne mirror ne market kendi `next_backoff`/`_heartbeat_loop`/`run_stream`ini TANIMLAR — reconnect
    yasası yalnız streamhealth'te. (mirror'ın set_stream/touch'u ayrı testte 'ince proxy' olarak kilitli.)"""
    forbidden = {"next_backoff", "_heartbeat_loop", "run_stream"}
    for mod in (mirror_stream, marketstream):
        leak = forbidden & _func_defs(mod)
        assert not leak, f"{mod.__name__} yasayı YENİDEN tanımlıyor: {leak} — kopya = ayrışma riski"


def test_delegating_proxies_are_thin_not_reimplementations():
    """mirror'ın set_stream/touch'u ORTAK yasaya delege eden İNCE proxy'dir; edge/`monotonic` mantığını
    (yasanın içini) İÇERMEZ — yoksa kopya olurdu."""
    for name in ("set_stream", "touch"):
        src = inspect.getsource(getattr(mirror_stream.MirrorOrderStateMachine, name))
        assert "self.health." in src and "monotonic" not in src, \
            f"mirror.{name} yasayı yeniden uyguluyor gibi görünüyor — tek satırlık proxy olmalı"


def test_run_bodies_delegate_and_have_no_reconnect_loop():
    """Her iki dinleyicinin `run`ı `run_stream`e delege eder; kendi `while` reconnect döngüsü YOK."""
    for mod, cls in ((mirror_stream, "MirrorStreamListener"), (marketstream, "MarketStreamListener")):
        src = inspect.getsource(getattr(mod, cls).run)
        assert "run_stream" in src and "while" not in src


def test_positive_control_scanner_is_not_blind():
    """POZİTİF kontrol: yasayı yeniden-tanımlayan SENTETİK kaynağı tarayıcı İŞARETLER (kör değil)."""
    synthetic = "async def _heartbeat_loop(spec):\n    return 1\ndef next_backoff(x):\n    return x\n"
    names = {n.name for n in ast.walk(ast.parse(synthetic))
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_heartbeat_loop" in names and "next_backoff" in names   # tarayıcı gerçekten görüyor
