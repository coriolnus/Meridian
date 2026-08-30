"""EXE-2026-009 P-1 DÜZELTMESİ (operatör hükmü 2026-08-29): `pencere` damgası GÖNDERİM anındaki
yürürlük rejimini söyler — DEFTERE YAZIM anındakini değil.

ÖLÇÜLEN ARIZA (research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/TESPIT.md):
damga `_patch_entry_slippage` içinde, yani dolum defterе yazılırken basılıyordu. Gönderim ile
yazım arasına bir DAĞITIM girerse ikisi ayrışır: DE/PANW satırları `ts=2026-08-21T20:32:22Z` ile
ESKİ (13:30) rejimde gönderildi, canlı `barclock` 1345'e 2026-08-23T14:53:43Z'de döndü, satırlar
2026-08-24'te yazılıp damgayı ORADA aldı → yanlış banda düştüler (hakemin 1345 bandı %50 kontamine).

ÇİVİLENEN YENİ SÖZLEŞME:
  (1) Damga GÖNDERİM satırı yazılırken basılır (`mirror_submit_armed`), barclock TEK kaynağından.
  (2) Dolum yaması damgaya DOKUNMAZ — ne yeniden yazar ne de eksik damgayı tamamlar.
  (3) Damgasız (bu düzeltmeden önce gönderilmiş) satıra yazım-anı rejimi UYDURULMAZ: damgasız
      kalır. Rejimi bilmeden banda atamak, kontaminasyonun ta kendisiydi (UYDURMA YASAĞI).
"""
import datetime as dt

import pytest

from meridian import barclock as bc, intraday_cycle as ic, loop, store

UTC = dt.timezone.utc


@pytest.fixture(autouse=True)
def _saat_sifirla():
    ic._CONSUMER = None
    yield
    bc.reset_clock()
    ic._CONSUMER = None


def _ayna_satir(**ek):
    return {"date": "2026-07-22", "plan_id": "P1", "ticker": "AAPL", "motor": "ayna",
            "karar": "submitted", "entry_trigger": 100.0, "limit": 101.0,
            "fill": None, "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None, **ek}


# ── (1) DAMGA GÖNDERİMDE BASILIR ──────────────────────────────────────────────────────────────
def test_gonderim_satiri_pencere_damgasini_GONDERIM_aninda_tasir(sandbox_state, monkeypatch):
    """RED sebebi: bugün `mirror_submit_armed` E2 satırına `pencere` YAZMIYOR — damga ancak
    dolum yamasında, yani günler sonra basılıyor."""
    from meridian import config
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")           # ayna kapısı açık
    monkeypatch.setattr(bc, "ENTRY_WINDOW_ET_MIN", 9 * 60 + 30)     # gönderim anı: ESKİ rejim
    bc.set_clock(lambda: dt.datetime(2026, 7, 23, 13, 35, tzinfo=UTC))
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000", "cash": "100000"})
    monkeypatch.setattr(alpaca, "positions", lambda: [])
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda pl, eq, **kw: {"ok": True, "qty": 10,
                                              "law": {"limit": 101.0, "mode": "limit",
                                                      "tif": "day", "atr": 1.0}})
    meta = {"armed": [{"id": "P1", "ticker": "AAPL", "entry_trigger": 100.0,
                       "stop": 95.0, "target": 110.0}]}
    loop.mirror_submit_armed(meta, "2026-07-23", eq_now=100_000.0, halted=False)

    rows = [r for r in store.read_jsonl(loop.ENTRY_LEDGER) if r.get("karar") == "submitted"]
    assert rows, "gönderim satırı yazılmadı — test kurulumu bozuk"
    assert rows[0]["pencere"] == "1330", "damga GÖNDERİM anındaki rejimi taşımıyor"


# ── (2) DOLUM YAMASI DAMGAYA DOKUNMAZ ─────────────────────────────────────────────────────────
def test_gonderimde_damgalanan_satir_dolum_yaziminda_DEGISMEZ(sandbox_state):
    """Regresyon kilidi: gönderimde 1330 damgalanmış satır, yürürlük 1345'ken dolsa bile
    1330 kalır (DE/PANW vakasının tam karşılığı)."""
    store.write_jsonl(loop.ENTRY_LEDGER, [_ayna_satir(pencere="1330")])
    assert bc.pencere_rejimi() == "1345"                            # yazım anı: YENİ rejim
    loop._patch_entry_slippage({"P1": {"status": "filled", "filled_avg_price": "101.5",
                                       "filled_qty": "10"}}, {"AAPL": 100.0}, "2026-07-23")
    r = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert r["fill"] == 101.5                                       # yama işini yaptı
    assert r["pencere"] == "1330"                                   # ama damgaya dokunmadı


def test_damgasiz_satira_yazim_ani_rejimi_UYDURULMAZ(sandbox_state):
    """RED sebebi: bugün yama `if "pencere" not in r` dalıyla damgasız satıra O ANKİ rejimi
    basıyor — DE/PANW'yi yanlış banda düşüren satır tam olarak budur."""
    store.write_jsonl(loop.ENTRY_LEDGER, [_ayna_satir()])            # damgasız (bayat) satır
    assert bc.pencere_rejimi() == "1345"
    loop._patch_entry_slippage({"P1": {"status": "filled", "filled_avg_price": "101.5",
                                       "filled_qty": "10"}}, {"AAPL": 100.0}, "2026-07-23")
    r = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert r["fill"] == 101.5                                       # yama işini yaptı
    assert r.get("pencere") is None, \
        "damgasız satıra yazım-anı rejimi basıldı — gönderim rejimi bilinmeden banda atama UYDURMADIR"
