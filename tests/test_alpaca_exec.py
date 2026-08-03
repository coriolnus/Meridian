"""Alpaca PAPER execution — the paper-endpoint HARD LOCK and correct bracket-order sizing. httpx mocked;
no real order is placed. The real-money live path is NOT exercised here (it stays flag-gated elsewhere)."""
import pytest

from meridian.adapters import alpaca
from meridian import secrets


def test_paper_base_is_hard_locked_even_if_configured_live(sandbox_state, monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_ENDPOINT", "https://api.alpaca.markets/v2")   # a LIVE URL
    secrets.clear_cache()
    assert "paper-api.alpaca.markets" in alpaca._paper_base()     # forced to paper — can't hit real money
    assert "api.alpaca.markets/v2" not in alpaca._paper_base().replace("paper-api", "")


class _R:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p


def test_submit_plan_sizes_bracket_and_posts_paper(sandbox_state, monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_KEY", "k")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "s")
    secrets.clear_cache()
    cap = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        cap["url"], cap["body"] = url, json
        return _R({"id": "o1", "status": "new", "symbol": "F"})
    monkeypatch.setattr(alpaca.httpx, "post", fake_post)

    plan = {"ticker": "F", "entry_trigger": 20.0, "profit_target": 26.0, "stop": 18.0, "size_r": 1.0}
    res = alpaca.submit_plan(plan, equity=100_000)
    assert res["ok"]
    assert "paper-api.alpaca.markets" in cap["url"] and cap["url"].endswith("/v2/orders")
    b = cap["body"]
    # risk = 1.0*1%*100k = $1000; per-share = 20-18 = $2 → qty 500; notional cap 0.25*100k/20=1250 → 500 kept
    assert b["symbol"] == "F" and int(b["qty"]) == 500 and b["order_class"] == "bracket"
    # E1 (WP-E, 2026-07-31) — BU İDDİA DEĞİŞTİ: eski hâli `type == "stop"` + `time_in_force == "gtc"`
    # idi ve CANLIDA 95/95 satırda reddedildi ("stop price must be greater than current price"),
    # çünkü `entry_trigger` sinyal barının KAPANIŞIDIR. Referans fiyat verilmediğinde (bu test)
    # yasa gap dalına düşer → limit fiyatlı emir, tavan = tetik + yüzde tavanı (ATR yok).
    # YÜRÜRLÜK: tavan %1 değil %4 — OPERATÖR KARARI 2026-08-03 (goal.yaml `execution_v2`; kart
    # EXE-2026-001 hükmü + ölçüm research/olcumler/e1_grid_2026-08-03). Bu test GERÇEK yapılandırmayı
    # okur, o yüzden beklenti yeni yasadan türetildi: 20 · 1,04 = 20,8 (= MAX_ENTRY_GAP_PCT zarfı).
    assert b["side"] == "buy" and b["type"] == "limit" and b["limit_price"] == 20.8
    assert b["time_in_force"] == "day"           # GTC bayat tetik taşıyordu (kart EXE-2026-001)
    assert b["take_profit"]["limit_price"] == 26.0 and b["stop_loss"]["stop_price"] == 18.0
    assert res["law"]["mode"] == "marketable_limit" and res["law"]["law"] == "E1-v1"


def test_submit_plan_uses_stop_limit_when_price_is_still_below_the_trigger(sandbox_state, monkeypatch):
    """Referans fiyat tetiğin ALTINDAYSA kırılım teyidi korunur: stop-limit (stop=tetik, limit=tavan)."""
    monkeypatch.setenv("ALPACA_PAPER_KEY", "k")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "s")
    secrets.clear_cache()
    cap = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        cap["body"] = json
        return _R({"id": "o2", "status": "new", "symbol": "F"})
    monkeypatch.setattr(alpaca.httpx, "post", fake_post)

    plan = {"ticker": "F", "entry_trigger": 20.0, "profit_target": 26.0, "stop": 18.0, "size_r": 1.0}
    res = alpaca.submit_plan(plan, equity=100_000, ref_price=19.5, atr=0.2)
    assert res["ok"] and res["law"]["mode"] == "stop_limit"
    b = cap["body"]
    # YÜRÜRLÜK (OPERATÖR KARARI 2026-08-03, goal.yaml `execution_v2` / kart EXE-2026-001 hükmü):
    # limit = 20 + min(100·0,2, %4·20) = 20 + min(20,00, 0,80) = 20,80 → ATR bacağı ARTIK BAĞLAMIYOR.
    # Testin amacı DAL SEÇİMİDİR (ref < tetik → kırılım teyidi = stop-limit) ve o korundu; ATR
    # ölçülü verilmesine rağmen bağlayan taraf yüzde tavanıdır ve satır bunu BEYAN eder.
    assert b["type"] == "stop_limit" and b["stop_price"] == 20.0 and b["limit_price"] == 20.8
    assert res["law"]["offset_kaynak"] == "pct_cap", \
        "ATR ölçülüyken bile bağlayan taraf yüzde tavanı olmalı (E1 bacağı BAĞLAMAZ — 2026-08-03)"


def test_submit_plan_rejects_bad_stop(sandbox_state, monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER_KEY", "k")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "s")
    secrets.clear_cache()
    bad = {"ticker": "X", "entry_trigger": 10.0, "profit_target": 12.0, "stop": 10.0, "size_r": 1.0}  # per-share 0
    assert alpaca.submit_plan(bad, equity=100_000)["ok"] is False
