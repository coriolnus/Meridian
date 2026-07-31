"""test_mirror_stream_audit_v33.py — mirror_stream denetimi (2026-07-21, tur 18).

7. soru:
  MS1 "bekleyen kayıt eninde sonunda kapanır" → HAYIR: tek bir terminal olay (filled/canceled)
     kaçarsa kayıt SONSUZA KADAR 'pending' kalır ve o sembol kalıcı olarak karar dışı olur.
     Sessiz, alarmsız açlık — hem de tam olarak "31 sessiz kayıp" sınıfından.
  MS2 "kopuş koruma bacaklarını iptal etmez" → BULUNDU: kopuş yolunda iptal mantığının İKİNCİ bir
     kopyası vardı; (a) operatörün ELLE girdiği emirleri de iptal ediyordu (sahiplik yok) ve
     (b) `partially_filled` de PENDING kümesinde olduğu için KISMEN DOLMUŞ bir parent'ı iptal edip
     canlı pozisyonu ÇIPLAK bırakabiliyordu — modülün "asla yapmam" dediği şeyin ta kendisi
  MS3 "akış PAPER'a kilitli"                 → wss://paper-api... dışına çıkış olmamalı
"""
from __future__ import annotations

import datetime as dt
import inspect

from meridian import mirror_stream as ms, store


def _sm(sandbox):
    ms.MACHINE = None
    return ms.MirrorOrderStateMachine()


def _order(coid="P-1", sym="AAA", status="new"):
    return {"client_order_id": coid, "symbol": sym, "status": status, "qty": "10",
            "filled_qty": "0", "id": "o1"}


# ---------- MS1: bekleyen kayıt sonsuza kadar bloklayamaz ----------
def test_ms1_fresh_pending_blocks_new_decisions(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("new", _order())
    assert sm.pending_symbols() == {"AAA"}
    assert ms.pending_symbols_snapshot() == {"AAA"}


def test_ms1b_stale_pending_stops_blocking_and_is_reported(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("new", _order())
    old = (dt.datetime.now(dt.timezone.utc)
           - dt.timedelta(hours=ms.PENDING_MAX_AGE_H + 1)).isoformat(timespec="seconds")
    sm.orders["P-1"]["updated"] = old
    sm._persist()
    assert sm.pending_symbols() == set(), "kaçan terminal olay sembolü sonsuza dek kilitliyor"
    assert ms.pending_symbols_snapshot() == set()
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "mirror_pending_stale"]
    assert ev and ev[-1]["ticker"] == "AAA", "sessizce yok saymak da yasak — kayda geçmeli"


def test_ms1c_terminal_events_clear_the_block(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("new", _order())
    sm.apply("fill", _order(status="filled"))
    assert sm.pending_symbols() == set()


def test_ms1d_rejection_alarms(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("rejected", _order(status="rejected"))
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "BROKER_REJECT" in blob or "RET" in blob


def test_ms1e_event_without_coid_is_ignored(sandbox_state):
    sm = _sm(sandbox_state)
    sm.apply("fill", {"symbol": "AAA", "status": "filled"})
    assert sm.orders == {}                      # birleştirme anahtarı yoksa kayıt tutulamaz


# ---------- MS2: koruma bacakları dokunulmaz ----------
def test_ms2_disconnect_never_cancels_protective_legs():
    src = inspect.getsource(ms)
    assert "close_all" not in src, "kopuşta düzleştirme yolu OLMAMALI"
    assert "httpx.delete" not in src, "ham iptal çağrısı = denetlenmemiş ikinci kopya"
    assert "cancel_open_entries" in src, "iptal YALNIZ adaptörün denetlenmiş yolundan geçmeli"


def test_ms2b_disconnect_delegates_to_the_audited_path(sandbox_state, monkeypatch):
    """Davranışsal kilit: kopuş devre-kesicisi açıkken bile YALNIZ motorun dolmamış girişleri gider;
    operatörün emri ve kısmen dolmuş parent'lar korunur (adaptörün süzgeci)."""
    from meridian.adapters import alpaca
    monkeypatch.setenv("MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES", "1")
    rows = [{"id": "1", "symbol": "AAA", "status": "new", "filled_qty": "0",
             "client_order_id": "P-2026-07-21-AAA", "side": "buy", "type": "stop"},
            {"id": "2", "symbol": "NVDA", "status": "new", "filled_qty": "0",
             "client_order_id": "operator-manual", "side": "buy", "type": "limit"},
            {"id": "3", "symbol": "BBB", "status": "partially_filled", "filled_qty": "4",
             "client_order_id": "P-2026-07-21-BBB", "side": "buy", "type": "stop"}]
    killed = []
    monkeypatch.setattr(alpaca, "orders", lambda **k: rows)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: killed.append(oid) or {"ok": True})
    ms.MACHINE = None
    ms.MirrorStreamListener()._maybe_cancel_entries()
    assert killed == ["1"], f"yalnız motorun DOLMAMIŞ girişi iptal edilmeli, iptal edilen: {killed}"


# ---------- MS3: paper kilidi ----------
def test_ms3_stream_url_is_paper_locked(monkeypatch):
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "get",
                        lambda n, *a, **k: "https://api.alpaca.markets" if n == "ALPACA_PAPER_ENDPOINT" else "k")
    url = ms.MirrorStreamListener._url()
    assert url.startswith("wss://paper-api.alpaca.markets"), f"gerçek-para akışına çıkış: {url}"


# ---------- dosya sonsuz büyümez ----------
def test_terminal_records_are_pruned(sandbox_state):
    sm = _sm(sandbox_state)
    for i in range(130):
        sm.apply("fill", _order(coid=f"P-{i}", sym=f"S{i}", status="filled"))
    assert len([v for v in sm.orders.values() if v["status"] == "filled"]) <= 100


def test_stream_flag_transitions_are_logged(sandbox_state):
    sm = _sm(sandbox_state)
    sm.set_stream(True)
    sm.set_stream(True)                          # aynı durum → tekrar log YOK
    sm.set_stream(False)
    evs = [e["event"] for e in store.read_jsonl("events.jsonl")
           if str(e.get("event", "")).startswith("mirror_stream_")]
    assert evs == ["mirror_stream_up", "mirror_stream_down"]
