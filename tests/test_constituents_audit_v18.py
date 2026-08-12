"""test_constituents_audit_v18.py — adapters.constituents denetimi (2026-07-21, tur 3).

7. soru ("neyi VARSAYIYOR ama hiçbir yerde İDDİA ETMİYOR?"):
  C1 "bu modül koşuyor"          → HİÇBİR üretim yolu çağırmıyordu; üç denetimlik düzeltme ölü kodda
  C2 "önbellekteki liste gerçek" → diskteki ÜRETİM önbelleği test fixture'ıydı (3 sembol, as_of 2099)
  C3 "boş liste zararsızdır"     → 'bilmiyoruz' ile 'sapma yok' aynı şeye benziyordu
  C4 "kaynak erişilebilir"       → lxml/bs4 yok + Wikipedia 403; ikisi de sessizce yutuluyordu

BEYANLI GÜNCELLEME (v238, 2026-08-13) — C4'ün İKİ YARISI AYRI ÖLÇÜLDÜ, YARISI ÇÜRÜMÜŞTÜ:
  * "lxml/bs4 yok" ARTIK YANLIŞ: lxml 6.1.1 kurulu ve `pyproject.toml`da ana bağımlılık. Aşağıdaki
    `test_c4b_missing_parser_is_visible` HÂLÂ GEÇERLİ ve DEĞİŞMEDİ — ama artık bugünkü canlı
    kurulumu değil, ayrıştırıcının bir gün DÜŞMESİ hâlini ölçer (ImportError'ı `pd.read_html`
    yamasıyla kendisi enjekte ediyor). Yani test bir SENARYO çivisi; kurulum iddiası değil.
  * "Wikipedia 403" HÂLÂ DOĞRU (2026-08-13 ölçümü: HTTP 403, gövde 141 bayt) — `test_c4_...` aynen.
  * BU DENETİMİN GÖRMEDİĞİ ASIL KÖK v238'de bulundu: pandas 3'te `read_html` ham HTML DİZGESİNİ
    dosya-yolu sanıyor (canlı `universe_drift.json` → FileNotFoundError). Kapanışı ve fikstür-HTML
    ile pandas-3 regresyon çivisi `tests/test_ariza_turu_v238.py` [A] bölümündedir.
"""
from __future__ import annotations

import inspect

import pytest

from meridian import store
from meridian.adapters import constituents as con


@pytest.fixture(autouse=True)
def _reset():
    con._HEALTH.update({"ok": None, "source": None, "n": 0, "at": None, "error": ""})
    yield


def _real_list(n=460, prefix="A"):
    return [f"{prefix}{i:03d}" for i in range(n)]


# ---------- C2: makullük kapısı — sahte önbellek servis edilemez ----------
def test_c2_fixture_cache_is_rejected(sandbox_state, monkeypatch):
    """CANLIDA BULUNDU: state/sp500_constituents.json = {"as_of":"2099-01-01",
    "current":["AAPL","MSFT","NVDA"]} — bir test koşusu üretim state'ine sızmıştı. Bir tüketici
    olsaydı S&P 500 diye ÜÇ sembol alırdı."""
    store.write_json(con.CACHE, {"as_of": "2099-01-01", "current": ["AAPL", "MSFT", "NVDA"],
                                 "changes": [{"date": "2026-03-01", "added": "NVDA", "removed": "nan"}]})
    assert con._cached() == {}                                   # kapıdan geçemez
    monkeypatch.setattr(con, "_fetch_tables", lambda: (None, None))
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    assert con.current() == []                                   # sahte liste ASLA servis edilmez
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "constituents_cache_invalid"]
    assert ev and ev[-1]["n"] == 3


def test_c2b_future_stamp_is_rejected(sandbox_state):
    """Gelecek tarihli 'as_of' tazelik kontrolünü anlamsızlaştırır: hiçbir gün 'bugün' olmaz, yani
    önbellek sonsuza kadar bayat ama sonsuza kadar servis edilebilir kalırdı."""
    store.write_json(con.CACHE, {"as_of": "2099-01-01", "current": _real_list()})
    assert con._cached() == {}


def test_c2c_plausible_gate(sandbox_state):
    assert con._plausible(_real_list()) is True
    assert con._plausible(["AAPL", "MSFT", "NVDA"]) is False     # 3 sembol S&P 500 değildir
    assert con._plausible([]) is False
    assert con._plausible(None) is False
    assert con._plausible(["NAN"] * 500) is False                # şekil kontrolü


# ---------- C4: kaynak arızası görünür ----------
def test_c4_source_failure_is_visible(sandbox_state, monkeypatch):
    """Eskiden hem eksik HTML-parser hem 403 `except: return None` ile yutuluyordu; modül 'sessizce
    hep bayat önbellek' moduna düşüyor ve bunu kimse bilmiyordu."""
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    import httpx

    class _R:
        status_code = 403
        text = ""

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R())
    assert con.current() == []
    h = con.health()
    assert h["ok"] is False and "403" in h["error"]


def test_c4b_missing_parser_is_visible(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    import httpx

    class _R:
        status_code = 200
        text = "<html></html>"

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R())
    import pandas as pd
    monkeypatch.setattr(pd, "read_html", lambda *a, **k: (_ for _ in ()).throw(ImportError("lxml")))
    assert con.current() == []
    assert con.health()["ok"] is False and "ImportError" in con.health()["error"]


# ---------- FMP birincil kaynak ----------
def test_fmp_is_primary_source(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "sp500_constituents", lambda: _real_list())
    monkeypatch.setattr(con, "_fetch_tables", lambda: (_ for _ in ()).throw(AssertionError("wiki'ye gitmemeli")))
    out = con.current()
    assert len(out) == 460 and con.health()["source"] == "fmp"
    assert store.read_json(con.CACHE, {})["source"] == "fmp"


def test_quota_blocked_fmp_is_skipped(sandbox_state, monkeypatch):
    """FMP 429 yemişken 500 sembollük bir istek daha atmak kotayı geri getirmez."""
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: True)
    monkeypatch.setattr(fmp, "sp500_constituents", lambda: (_ for _ in ()).throw(AssertionError("çağrılmamalı")))
    monkeypatch.setattr(con, "_fetch_tables", lambda: (None, None))
    assert con.current() == []


# ---------- C1 + C3: gerçek tüketici ve 'bilmiyoruz' dürüstlüğü ----------
def test_c3_drift_unknown_is_not_no_drift(sandbox_state, monkeypatch):
    """'Kaynak yok' ile 'sapma yok' AYNI ŞEY DEĞİL. Boş liste sessizce 'her şey yolunda' diye
    okunursa evren yıllarca ölü isim taşır (bu yıl 7 tanesini elle bulduk)."""
    monkeypatch.setattr(con, "current", lambda *a, **k: [])
    d = con.universe_drift()
    assert d["status"] == "unknown" and d["n_stale"] == 0 and d["reason"]


def test_c1_drift_finds_dead_names(sandbox_state, monkeypatch):
    from meridian.adapters import data
    members = [t for t in data.REPLAY_UNIVERSE if t not in ("NVDA", "AAPL")] + _real_list(460, "B")
    monkeypatch.setattr(con, "current", lambda *a, **k: members)
    d = con.universe_drift()
    assert d["status"] == "ok" and set(d["stale"]) == {"AAPL", "NVDA"}


def test_c1b_drift_has_a_real_consumer():
    """Denetimin ASIL bulgusu: modülün hiç tüketicisi yoktu. Artık P5 döngüsü çağırıyor."""
    from meridian import loop, watchdog
    assert "_universe_drift_check()" in inspect.getsource(loop.daily_cycle)
    assert "universe_drift" in inspect.getsource(loop._universe_drift_check)
    assert "sp500_membership" in inspect.getsource(watchdog.production_report)


def test_c1c_loop_check_writes_state_and_survives_failure(sandbox_state, monkeypatch):
    from meridian import loop
    monkeypatch.setattr(con, "current", lambda *a, **k: [])
    loop._universe_drift_check()
    assert store.read_json("universe_drift.json", {})["status"] == "unknown"
    monkeypatch.setattr(con, "universe_drift", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    loop._universe_drift_check()                                  # döngüyü ASLA bozmaz
    assert any(e.get("event") == "universe_drift_failed" for e in store.read_jsonl("events.jsonl"))


# ---------- kalıcı: #52/#53 düzeltmeleri hâlâ yerinde ----------
def test_pit_changelog_still_walks_backwards(sandbox_state):
    base = _real_list()
    store.write_json(con.CACHE, {"as_of": "2026-07-21", "current": base + ["NEW"],
                                 "changes": [{"date": "October 1, 2026", "added": "NEW", "removed": "OLD"}]})
    members = con.as_of("2025-01-01")
    assert "NEW" not in members and "OLD" in members              # #52: insan-okunur tarih ISO'ya çevrilir


def test_pit_nan_ticker_never_appears(sandbox_state):
    store.write_json(con.CACHE, {"as_of": "2026-07-21", "current": _real_list(),
                                 "changes": [{"date": "2026-10-01", "added": "", "removed": "nan"}]})
    assert "NAN" not in con.as_of("2025-01-01")                   # #49
