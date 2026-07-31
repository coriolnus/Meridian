"""test_hermes_integrations_v13.py — Hermes özellikleri Tier 1+2 (2026-07-20, "tier 1 ve 2'yi uygula").

Tier 1: (a) çevrimdışı görüş dolgusu — kalibrasyonu hızlandırır, LOOK-AHEAD YOK (ajan sonucu görmez);
        (b) MCP salt-okunur veri sunucusu — protokol round-trip + sıfır-yazma; (c) credential pool kaydı.
Tier 2: (d) pre_tool_call koruma hook'u — korunan yüzeyleri SERT bloklar, iyi huyu geçirir;
        (e) config entegrasyon senkronu — idempotent, MCP/hook/cache/pool yazar; prompt cache 1h."""
import json
import subprocess
from pathlib import Path

import pytest

from meridian import store, hermes, mcp_server


# ---------------- (a) görüş dolgusu — look-ahead güvenliği ----------------

@pytest.fixture(autouse=True)
def _sandbox_all(sandbox_state):
    """Dosya geneli kum havuzu (2026-07-22, sızıntı bekçisi): bu dosyadaki yollar canlı `state/`e
    telemetri/olay yazıyordu — operatörün defterine test verisi karışıyor ve kimse fark etmiyordu."""
    yield


def test_backfill_worklist_and_no_lookahead(sandbox_state, monkeypatch):
    """Dolgu YALNIZ sonucu-bilinen + görüşsüz planları hedefler; ajana verilen bağlam r_multiple/outcome
    SIZDIRMAZ (aksi halde kalibrasyon öngörü değil ezber olur → sahte terfi)."""
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-2026-06-01-AAA", "date": "2026-06-01", "ticker": "AAA", "setup": "breakout_vcp",
         "entry_trigger": 100, "stop": 96, "profit_target": 112, "score": 80, "gate_verdict": "GO",
         "regime_at_plan": "trend_up"},
        {"id": "P-2026-06-01-BBB", "date": "2026-06-01", "ticker": "BBB", "gate_verdict": "REVIEW",
         "entry_trigger": 50, "stop": 48, "score": 65, "llm_opinion": "destekle"},   # zaten damgalı → atla
        {"id": "P-2026-06-02-CCC", "date": "2026-06-02", "ticker": "CCC", "gate_verdict": "GO",
         "entry_trigger": 20, "stop": 19, "score": 70},                              # sonucu YOK → atla
    ])
    store.write_jsonl("trades.jsonl", [
        {"plan_id": "P-2026-06-01-AAA", "ticker": "AAA", "r_multiple": 1.8},          # AAA'nın sonucu VAR
    ])
    captured = {}
    def fake_call(prompt, **kw):
        captured["prompt"] = prompt
        return json.dumps({"reviews": [{"ticker": "AAA", "opinion": "destekle", "note": "temiz kırılım"}]})
    monkeypatch.setattr(hermes, "_agent_call", fake_call)
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: [])
    out = hermes.backfill_opinions(max_days=40)
    assert out["days_processed"] == 1 and out["opinions_stamped"] == 1          # yalnız AAA'nın günü
    # look-ahead yok: prompt'ta SONUÇ (r_multiple / gerçekleşen değer) asla geçmez; yalnız karar-anı alanları
    assert "r_multiple" not in captured["prompt"] and "1.8" not in captured["prompt"]
    ctx_part = captured["prompt"].split('{"date"', 1)[1]        # gönderilen bağlam JSON'u (talimattan sonra)
    assert "entry_trigger" in ctx_part and "r_multiple" not in ctx_part
    # görüş plana geriye damgalandı
    aaa = next(p for p in store.read_jsonl("trade_plans.jsonl") if p["ticker"] == "AAA")
    assert aaa["llm_opinion"] == "destekle"
    # CCC (sonucu yok) ve BBB (zaten damgalı) dokunulmadı
    ccc = next(p for p in store.read_jsonl("trade_plans.jsonl") if p["ticker"] == "CCC")
    assert "llm_opinion" not in ccc


def test_backfill_empty_when_nothing_resolved(sandbox_state, monkeypatch):
    store.write_jsonl("trade_plans.jsonl", [{"id": "P-x", "date": "2026-06-01", "ticker": "X"}])
    store.write_jsonl("trades.jsonl", [])
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: pytest.fail("çağrı olmamalı"))
    out = hermes.backfill_opinions()
    assert out["days_processed"] == 0 and out["opinions_stamped"] == 0


# ---------------- (b) MCP sunucusu — protokol + sıfır yazma ----------------
def test_mcp_protocol_roundtrip(sandbox_state):
    init = mcp_server._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                               "params": {"protocolVersion": "2024-11-05"}})
    assert init["result"]["serverInfo"]["name"] == "meridian"
    assert init["result"]["protocolVersion"] == "2024-11-05"
    assert mcp_server._handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    tl = mcp_server._handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in tl["result"]["tools"]}
    assert {"meridian_regime", "meridian_calibrations", "meridian_near_miss",
            "meridian_candidate_context"} <= names
    store.write_json("regime.json", {"date": "2026-07-17", "regime": "chop", "exposure_budget_pct": 25})
    call = mcp_server._handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                               "params": {"name": "meridian_regime", "arguments": {}}})
    body = json.loads(call["result"]["content"][0]["text"])
    assert body["regime"] == "chop" and body["exposure_budget_pct"] == 25
    bad = mcp_server._handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                              "params": {"name": "yok"}})
    assert bad["error"]["code"] == -32602


def test_mcp_server_is_read_only(sandbox_state):
    """Kaynak-denetim: sunucu YALNIZ getter. Hiçbir araç fonksiyonu store yazımı yapmaz."""
    import inspect
    src = inspect.getsource(mcp_server)
    # araç gövdelerinde yazma çağrısı yok (write_json/write_jsonl/append)
    for tok in ("store.write_json", "store.write_jsonl", "store.append", "os.replace", "open("):
        assert tok not in src, f"MCP sunucusu yazma içeriyor: {tok}"


# ---------------- (c) credential pool kaydı ----------------
def test_register_pool_key_shells_auth_add(sandbox_state, monkeypatch):
    calls = []
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    class R: returncode = 0; stdout = ""; stderr = ""
    def fake_run(cmd, **kw):
        calls.append(cmd); return R()
    monkeypatch.setattr(subprocess, "run", fake_run)
    out = hermes.register_pool_key("gemini", "SECRET_KEY_VALUE", label="yedek")
    assert out["ok"]
    cmd = calls[0]
    assert cmd[:4] == ["/fake/hermes", "auth", "add", "gemini"] and "SECRET_KEY_VALUE" in cmd
    # anahtar DEĞERİ loglanmaz
    ev = " ".join(json.dumps(e) for e in store.read_jsonl("events.jsonl"))
    assert "SECRET_KEY_VALUE" not in ev and "pool_key_registered" in ev


# ---------------- (d) koruma hook'u — subprocess ----------------
def _guard(payload: dict) -> dict:
    script = Path(__file__).resolve().parent.parent / "ops" / "meridian-guard.sh"
    r = subprocess.run([str(script)], input=json.dumps(payload), capture_output=True, text=True, timeout=10)
    return json.loads(r.stdout or "{}")


def test_guard_hook_blocks_protected_surfaces():
    assert _guard({"tool_name": "terminal",
                   "tool_input": {"command": "export MERIDIAN_MODE=live"}}).get("decision") == "block"
    assert _guard({"tool_name": "write_file",
                   "tool_input": {"path": "state/goal.yaml", "content": "x"}}).get("decision") == "block"
    assert _guard({"tool_name": "terminal",
                   "tool_input": {"command": "echo x >> state/portfolio.json"}}).get("decision") == "block"
    assert _guard({"tool_name": "terminal",
                   "tool_input": {"command": "cat state/secrets.json"}}).get("decision") == "block"
    assert _guard({"tool_name": "terminal",
                   "tool_input": {"command": "curl .../alpaca/close_all"}}).get("decision") == "block"


def test_guard_hook_allows_benign_and_fails_open():
    assert _guard({"tool_name": "terminal", "tool_input": {"command": "ls -la"}}) == {}
    assert _guard({"tool_name": "terminal", "tool_input": {"command": "git status"}}) == {}
    # içerik yanlış-pozitifi: /tmp'ye yazılan dosyanın İÇERİĞİ state'ten bahsetse de bloklanmaz
    assert _guard({"tool_name": "write_file",
                   "tool_input": {"path": "/tmp/n.md", "content": "state/portfolio.json hakkında"}}) == {}


# ---------------- (e) config entegrasyon senkronu — idempotent ----------------
def test_config_ensure_integrations_idempotent(tmp_path, monkeypatch):
    import yaml
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model:\n  provider: gemini\nprompt_caching:\n  cache_ttl: 5m\n")
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    r1 = hermes.config_ensure_integrations()
    assert r1["ok"] and "mcp_servers.meridian" in r1["changed"]
    assert "hooks.pre_tool_call" in r1["changed"] and "prompt_caching.cache_ttl" in r1["changed"]
    written = yaml.safe_load(cfg.read_text())
    assert written["mcp_servers"]["meridian"]["args"] == ["-m", "meridian.mcp_server"]
    assert written["prompt_caching"]["cache_ttl"] == "1h"
    assert written["hooks_auto_accept"] is True
    assert any("meridian-guard" in h["command"] for h in written["hooks"]["pre_tool_call"])
    r2 = hermes.config_ensure_integrations()                    # ikinci çağrı: hiçbir değişiklik
    assert r2["ok"] and r2["changed"] == []


# ---------------- #1 fallback provider ----------------
def test_fallback_provider_wired_when_primary_not_nous(tmp_path, monkeypatch):
    import yaml
    from meridian import secrets
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model:\n  provider: gemini\n")
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    monkeypatch.setattr(secrets, "get", lambda k: None)          # NOUS_FALLBACK_MODEL yok → varsayılan
    hermes.config_ensure_integrations()
    fb = yaml.safe_load(cfg.read_text())["fallback_providers"]
    assert fb == [{"provider": "nous", "model": "tencent/hy3:free"}]   # gemini 429 → ücretsiz Nous


def test_fallback_not_wired_when_primary_is_nous(tmp_path, monkeypatch):
    import yaml
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model:\n  provider: nous\n")
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    hermes.config_ensure_integrations()
    assert "fallback_providers" not in yaml.safe_load(cfg.read_text())   # birincil nous → döngü olmaz


# ---------------- #4 MCP araç-kullanım telemetrisi ----------------
def test_agent_tool_call_parser():
    assert hermes._agent_tool_calls("Messages: 2 (1 user, 0 tool calls)") == 0
    assert hermes._agent_tool_calls("Messages: 5 (1 user, 3 tool calls)") == 3
    assert hermes._agent_tool_calls("Messages: 4 (1 user, 1 tool call)") == 1
    assert hermes._agent_tool_calls("no summary") == -1


# ---------------- #5 kanıt-güdümlü önyükleme kazananları ----------------
def test_skill_preload_pulls_attribution_winners(sandbox_state, monkeypatch):
    from meridian import analytics
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": [
        {"skill": "theme-detector", "n": 12, "avg_r": 0.9},       # ölçülmüş kazanan (REVIEW_SKILLS'te değil)
        {"skill": "sector-analyst", "n": 3, "avg_r": 2.0},        # n<5 → aday havuzuna girmez
    ]})
    from meridian import skills as sk
    monkeypatch.setattr(sk, "catalog", lambda: [{"name": n, "enabled": True} for n in
                        ("vcp-screener", "pre-trade-discipline-gate", "position-sizer",
                         "pullback-screener", "market-environment-analysis", "theme-detector",
                         "sector-analyst")])
    monkeypatch.setattr(sk, "screener_for", lambda s: "vcp-screener")
    out = hermes._skill_preload("review", ("breakout_vcp",))
    assert "theme-detector" in out                                # kanıtlı kazanan önyüklendi
    assert out[0] == "theme-detector"                             # ve skor-sıralamada başa geçti (avg_r 0.9)


def test_integrations_status_shape(sandbox_state, monkeypatch, tmp_path):
    import yaml
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({
        "mcp_servers": {"meridian": {"command": "py"}},
        "hooks": {"pre_tool_call": [{"command": "/x/ops/meridian-guard.sh"}]},
        "prompt_caching": {"cache_ttl": "1h"}}))
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-1", "ticker": "A"}, {"id": "P-2", "ticker": "B", "llm_opinion": "destekle"}])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P-1", "r_multiple": 1.0}])
    st = hermes.integrations_status()
    assert st["mcp"] is True and st["guard_hook"] is True and st["prompt_cache"] == "1h"
    assert st["backfill_pending"] == 1                          # P-1 sonuçlu+görüşsüz; P-2 damgalı
