"""test_intraday_cycle_v88.py — Faz 4 gözlem-modu tüketicisi. Look-ahead kilidi + gözlem-silahlamıyor kanıtı.

`_hotstate_off_by_default` (conftest) Redis'i kapatır → read_bars MONKEYPATCH ile enjekte edilir.
`set_clock` module-global → autouse _reset_clock ZORUNLU (donuk saat sonraki testlere sızmasın).
"""
import datetime as dt

import pytest

from meridian import intraday_cycle as ic, barclock as bc, store

UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)   # 10:46:30 ET (yaz, RTH açık)


@pytest.fixture(autouse=True)
def _reset():
    ic._CONSUMER = None
    yield
    bc.reset_clock()
    ic._CONSUMER = None


def _bar(t, h, c):
    return {"t": t, "o": c, "h": h, "l": c, "c": c, "v": 100}


def _inject(monkeypatch, bars):
    monkeypatch.setattr(ic.hotstate, "read_bars", lambda tk, n: bars)


def test_only_admissible_closed_bars_enter_the_decision(sandbox_state, monkeypatch):
    """LOOK-AHEAD KİLİDİ: 14:46 forming bar (kapanış 14:47 > as_of 14:46:30) karara GİRMEZ."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [{"ticker": "AAPL", "entry_trigger": 100.0}]})
    _inject(monkeypatch, [_bar("2026-07-23T14:44:00Z", 99, 98),
                          _bar("2026-07-23T14:45:00Z", 101, 100.5),
                          _bar("2026-07-23T14:46:00Z", 999, 500)])   # FORMING — dışlanmalı
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    rows = store.read_jsonl("intraday_decisions.jsonl")
    assert len(rows) == 1
    r = rows[0]
    assert r["bar_t"] == "2026-07-23T14:45:00Z"      # forming 14:46 DEĞİL
    assert r["admissible_bars"] == 2                 # 14:44 + 14:45
    assert r["fired"] is True                        # 14:45 high 101 >= trigger 100
    assert r["decision_as_of"] >= r["close_ts"]      # 3 damga audit: kapanmış tarafta


def test_observation_writes_ledger_but_never_arms(sandbox_state, monkeypatch):
    """GÖZLEM SİLAHLAMIYOR KANITI: karar satırı yazılır ama portfolio/armed DEĞİŞMEZ (sıfır yetki)."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [{"ticker": "AAPL", "entry_trigger": 100.0}]})
    _inject(monkeypatch, [_bar("2026-07-23T14:45:00Z", 101, 100.5)])
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert len(store.read_jsonl("intraday_decisions.jsonl")) == 1
    pf = store.read_json("portfolio.json", {})
    assert pf.get("positions") == {} and len(pf.get("armed", [])) == 1   # pozisyon açılmadı, armed büyümedi


def test_stale_closed_bar_is_skipped(sandbox_state, monkeypatch):
    bc.set_clock(lambda: dt.datetime(2026, 7, 23, 14, 50, 0, tzinfo=UTC))   # 14:45 barından 4 dk sonra
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    _inject(monkeypatch, [_bar("2026-07-23T14:45:00Z", 101, 100)])          # kapanış 14:46, age 240s > 120
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert store.read_jsonl("intraday_decisions.jsonl") == []               # bayat → karar yok
    assert ic.consumer().skipped["stale"] == 1


def test_only_watched_symbols_are_processed(sandbox_state, monkeypatch):
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    seen = []

    def fake_read(tk, n):
        seen.append(tk)
        return [_bar("2026-07-23T14:45:00Z", 1, 1)]

    monkeypatch.setattr(ic.hotstate, "read_bars", fake_read)
    ic.consumer().on_barfeed_event({"syms": "AAPL,MSFT,NVDA,GOOG"})         # yalnız AAPL izleniyor
    assert seen == ["AAPL"]


def test_session_closed_no_work(sandbox_state, monkeypatch):
    bc.set_clock(lambda: dt.datetime(2026, 7, 23, 2, 0, 0, tzinfo=UTC))     # 22:00 ET (önceki gün) — kapalı
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: (_ for _ in ()).throw(AssertionError("RTH dışı işlenmemeli")))
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert ic.consumer().skipped["session"] == 1


def test_halt_stops_the_cycle(sandbox_state, monkeypatch):
    from meridian import health
    bc.set_clock(lambda: RTH)
    health.set_halt(True)
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: (_ for _ in ()).throw(AssertionError("halt'ta işlenmemeli")))
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert ic.consumer().skipped["halt"] == 1


def test_redis_down_symbol_skipped_not_crash(sandbox_state, monkeypatch):
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    monkeypatch.setattr(ic.hotstate, "read_bars", lambda tk, n: None)       # Redis down
    ic.consumer().on_barfeed_event({"syms": "AAPL"})                        # istisna ATMAMALI
    assert ic.consumer().skipped["no_bars"] == 1


def test_event_error_is_swallowed_not_fatal(sandbox_state, monkeypatch):
    """Callback barfeed daemon thread'inde koşar — bir hata thread'i düşürmemeli, kaydedilmeli."""
    bc.set_clock(lambda: RTH)
    monkeypatch.setattr(ic, "store", None)      # _handle içinde patlat (store.read_json → AttributeError)
    ic.consumer().on_barfeed_event({"syms": "AAPL"})   # yükseltmemeli
    assert ic.consumer().last_error                     # hata görünür
