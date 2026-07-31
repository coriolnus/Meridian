"""test_alpaca_audit_v16.py — adapters.alpaca dönüşümlü bütünlük denetimi (2026-07-21).

docs/INTEGRITY-AUDIT.md protokolü: 6 desen + 7. soru ("neyi VARSAYIYOR ama hiçbir yerde İDDİA
ETMİYOR?"). Bulunan 4 yazısız varsayım (A1-A4) burada teste çevrildi. Dürüstlük kuralı gereği
kapsam ancak bu testler yeşilken 'covered' sayılır.
"""
from __future__ import annotations

import inspect

import httpx
import pytest

from meridian import loop
from meridian.adapters import alpaca


class _Boom(httpx.ConnectError):
    def __init__(self):
        super().__init__("network down")


@pytest.fixture(autouse=True)
def _reset_transport(monkeypatch):
    # asset_tradable() GERÇEK bir ağ çağrısıdır (LULD vekili); testler ağa çıkmasın diye sabitlenir.
    monkeypatch.setattr(alpaca, "asset_tradable", lambda s: True)
    alpaca._note(True)
    yield
    alpaca._note(True)


# ---------- A1: KORUNUM/ÜRETKENLİK — "ulaşılamadı" ile "hiç emir yok" ayrılabilmeli ----------
def test_a1_swallowed_error_is_visible_in_transport(monkeypatch):
    """orders()/positions()/account() istisna YUTAR ve []/None döner. Yutulan hata görünmezse
    API arızası 'hiç emir yok' gibi okunur. Taşıma kaydı ayrımı taşımalı."""
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(_Boom()))
    assert alpaca.orders() == []
    assert alpaca.transport()["ok"] is False          # boş liste ARIZA'dan geldi
    assert "orders" in alpaca.transport()["error"]
    assert alpaca.positions() == []
    assert alpaca.account() is None
    assert alpaca.transport()["consecutive_fails"] >= 3


def test_a1_success_clears_transport(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(_Boom()))
    alpaca.orders()
    assert alpaca.transport()["ok"] is False

    class _R:
        status_code = 200

        def raise_for_status(self): pass

        def json(self): return []

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R())
    assert alpaca.orders() == []
    assert alpaca.transport()["ok"] is True          # gerçekten 'emir yok'
    assert alpaca.transport()["consecutive_fails"] == 0


def test_a1_reconcile_does_not_alarm_on_api_outage():
    """ASIL HATA: alpaca.orders() istisna fırlatmadığı için mutabakattaki except ÖLÜ KOD'du; arıza
    anında a_by_sym boş kalıp AÇIK HER POZİSYON 'Alpaca'da kayıp' split-brain alarmı üretiyordu."""
    src = inspect.getsource(loop.reconcile_broker_state)
    assert 'alpaca.transport()["ok"]' in src, "arıza tespiti taşıma kaydına bağlı olmalı"
    # emir VE pozisyon okumalarının ikisi de korunmalı
    assert src.count('alpaca.transport()["ok"]') >= 2


def test_a1_unreachable_broker_keeps_plans_armed():
    """Ağ hatası ile broker reddi ayrılmazsa geçici bir kesinti GEÇERLİ bir silahlı planı kalıcı
    olarak düşürüyordu (31 sessiz kayıp sınıfının aynısı)."""
    src = inspect.getsource(loop.daily_cycle)
    assert 'res.get("reachable") is False' in src
    assert "_MirrorUnreachable" in src


def test_a1_submit_marks_reachability():
    """4xx = broker ULAŞILABİLİR (gerçek ret). Ağ istisnası = ulaşılamadı."""
    class _R:
        status_code = 422

        def json(self): return {"message": "insufficient buying power"}

    import meridian.adapters.alpaca as A
    orig = A.httpx.post
    try:
        A.httpx.post = lambda *a, **k: _R()
        res = A.submit_bracket("X", 1, 10.0, 12.0, 9.0, client_order_id="P-1")
        assert res["ok"] is False and res["reachable"] is True
        A.httpx.post = lambda *a, **k: (_ for _ in ()).throw(_Boom())
        res = A.submit_bracket("X", 1, 10.0, 12.0, 9.0, client_order_id="P-1")
        assert res["ok"] is False and res["reachable"] is False
        assert A.transport()["ok"] is False
    finally:
        A.httpx.post = orig


# ---------- A2: TUTARLILIK — birleştirme anahtarı (client_order_id) gerçekten gidiyor mu ----------
def test_a2_client_order_id_round_trips(monkeypatch):
    """Mutabakat coid == plan kimliği ile eşleşir. Gitmezse: emir dolar, iç defterle eşleşmez,
    'motor yetimi' bile sayılmaz — operatörün kendi varlığı gibi 'external' altına düşer."""
    seen = {}

    class _R:
        status_code = 200

        def json(self): return {"id": "o1"}

    def _post(url, headers=None, json=None, timeout=None):
        seen.update(json or {})
        return _R()

    monkeypatch.setattr(httpx, "post", _post)
    plan = {"id": "P-2026-07-21-NVDA", "ticker": "NVDA", "entry_trigger": 100.0,
            "stop": 95.0, "profit_target": 110.0, "size_r": 1.0}
    res = alpaca.submit_plan(plan, equity=100_000)
    assert res["ok"] is True
    assert seen["client_order_id"] == plan["id"]
    assert seen["client_order_id"].startswith(alpaca.ENGINE_COID_PREFIX)


def test_a2_engine_prefix_matches_loop_plan_ids():
    """Önek İKİ yerde ayrı yazılıysa sessizce kayar; loop.py'deki kimlik üretimi ile aynı olmalı."""
    assert alpaca.ENGINE_COID_PREFIX == "P-"
    assert 'f"P-{dstr}-' in inspect.getsource(loop.daily_cycle)
    assert alpaca.is_engine_order({"client_order_id": "P-2026-07-21-NVDA"}) is True
    assert alpaca.is_engine_order({"client_order_id": "a1b2-uuid"}) is False
    assert alpaca.is_engine_order({}) is False


# ---------- A3: SAHİPLİK — motor, sahibi olmadığı emre/pozisyona dokunamaz ----------
def test_a3_cancel_open_entries_spares_operator_orders(monkeypatch):
    """Panodaki 'Cancel-Open' tuşu, operatörün ELLE girdiği emirleri de iptal ediyordu."""
    rows = [{"id": "1", "symbol": "AAPL", "status": "new", "filled_qty": "0",
             "client_order_id": "P-2026-07-21-AAPL"},
            {"id": "2", "symbol": "NVDA", "status": "new", "filled_qty": "0",
             "client_order_id": "operator-manual-1"},
            {"id": "3", "symbol": "TSLA", "status": "new", "filled_qty": "0"}]
    monkeypatch.setattr(alpaca, "orders", lambda **k: rows)
    killed = []
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: killed.append(oid) or {"ok": True})
    out = alpaca.cancel_open_entries()
    assert killed == ["1"]                                   # yalnız motorun emri
    assert {f["symbol"] for f in out["foreign"]} == {"NVDA", "TSLA"}


def test_a3_close_all_requires_confirm_token(monkeypatch):
    """close_all operatörün KENDİ varlığını da düzleştirir → hiçbir otomatik yol kazayla çağıramaz."""
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "NVDA"}, {"symbol": "AAPL"}])
    monkeypatch.setattr(alpaca, "orders", lambda **k: [{"symbol": "AAPL",
                                                       "client_order_id": "P-x"}])
    deleted = []
    monkeypatch.setattr(httpx, "delete", lambda *a, **k: deleted.append(a) or None)

    res = alpaca.close_all()                                 # jetonsuz → KURU KOŞU
    assert res["ok"] is False and res["dry_run"] is True
    assert res["foreign"] == ["NVDA"]                        # operatörün varlığı açıkça uyarılır
    assert deleted == [], "jetonsuz çağrı hiçbir şey silmemeli"


def test_a3_close_all_token_is_not_guessable_by_loop():
    """Motorun hiçbir otonom yolu jetonu taşımamalı (yalnız api.py insan uç noktası)."""
    for mod in (loop, __import__("meridian.mirror_stream", fromlist=["x"])):
        assert alpaca.CLOSE_ALL_CONFIRM not in inspect.getsource(mod)


# ---------- A4: MONOTONLUK — koruma asla gevşetilmez ----------
def test_a4_stop_never_loosened(monkeypatch):
    patched = []
    monkeypatch.setattr(httpx, "patch", lambda *a, **k: patched.append(k) or _ok())
    res = alpaca.replace_order_stop("o1", 95.0, cur_stop=98.0)
    assert res["ok"] is False and "refused_stop_loosening" in res["detail"]
    assert patched == [], "aşağı yönlü stop PATCH'i sınırda durmalı"
    assert alpaca.replace_order_stop("o1", 99.0, cur_stop=98.0)["ok"] is True


def test_a4_caller_passes_current_stop():
    assert "cur_stop=cur_stop" in inspect.getsource(loop.reconcile_broker_state)


def _ok():
    class _R:
        status_code = 200

        def json(self): return {"id": "o1"}
    return _R()


# ---------- DETERMİNİZM: aynı plan → aynı gövde (fiyat yuvarlaması dahil) ----------
def test_determinism_same_plan_same_body(monkeypatch):
    bodies = []

    def _post(url, headers=None, json=None, timeout=None):
        bodies.append(json)
        return _ok()

    monkeypatch.setattr(httpx, "post", _post)
    plan = {"id": "P-d", "ticker": "X", "entry_trigger": 100.12345, "stop": 95.6789,
            "profit_target": 110.4321, "size_r": 1.0}
    alpaca.submit_plan(plan, equity=100_000)
    alpaca.submit_plan(dict(plan), equity=100_000)
    assert bodies[0] == bodies[1]


# ---------- Kalıcı: paper kilidi (audit #51) hâlâ hostname tabanlı ----------
def test_paper_lock_still_hostname_based(monkeypatch):
    monkeypatch.setattr(alpaca.secrets, "get",
                        lambda n, *a, **k: "https://paper-api.alpaca.markets.evil.example.com"
                        if n == "ALPACA_PAPER_ENDPOINT" else "k")
    assert alpaca._paper_base() == alpaca.PAPER_BASE
