"""test_mcp_audit_v31.py — mcp_server denetimi (2026-07-21, tur 16).

Bu sunucu, LLM'in Meridian'ın iç durumuna açılan tek penceresi. 7. soru:
  MC1 "MUTLAK yetki sınırı: yalnız getter" → docstring'de BÜYÜK harfle yazılı; kanıtı yoktu.
     Burada iki katmanlı kanıt: (a) AST — hiçbir araç yazma çağrısına ulaşmıyor, (b) DAVRANIŞ —
     bütün araçlar koştuktan sonra state klasörünün BYTE'ı değişmemeli.
  MC2 "sonuç sızdırmaz" → candidate_context ÖNGÖRÜ SAFLIĞI için r_multiple döndürmemeli; ajan
     geçmiş bir kararın sonucunu görürse "tahminleri" geriye dönük olarak kusursuz olur
  MC3 "bozuk girdi döngüyü öldürmez" → JSON-RPC protokol dayanıklılığı
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import io
import json
from pathlib import Path

import pytest

from meridian import mcp_server as mcp, store


SRC = inspect.getsource(mcp)


def _snapshot(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _call(name, args=None, mid=1):
    return mcp._handle({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                        "params": {"name": name, "arguments": args or {}}})


# ---------- MC1: sıfır yazma ----------
def test_mc1_no_write_calls_anywhere_in_the_module():
    bad = {"write_json", "write_jsonl", "append_jsonl", "merge_dated_jsonl", "unlink", "mkdir",
           "write_text", "write_bytes", "replace", "remove"}
    called = set()
    for n in ast.walk(ast.parse(SRC)):
        if isinstance(n, ast.Call):
            f = n.func
            called.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    hits = called & bad
    assert not hits, f"MCP sunucusunda YAZMA çağrısı: {hits}"
    assert "open" not in called, "dosya açma yok (yalnız store okuyucuları)"


def test_mc1b_running_every_tool_changes_nothing_on_disk(sandbox_state):
    store.write_json("regime.json", {"date": "2026-07-20", "regime": "chop", "exposure_budget_pct": 40})
    store.write_jsonl("trade_plans.jsonl", [{"ticker": "NVDA", "date": "2026-07-20", "setup": "vcp",
                                             "gate_verdict": "GO", "r_multiple": 2.2}])
    before = _snapshot(sandbox_state)
    for t in mcp.TOOLS:
        args = {"ticker": "NVDA"} if "ticker" in (t["inputSchema"].get("properties") or {}) else {}
        res = _call(t["name"], args)
        assert res["result"]["content"][0]["type"] == "text"
    assert _snapshot(sandbox_state) == before, "araçlardan biri diske yazdı — yetki sınırı ihlali"


# ---------- MC2: öngörü saflığı ----------
def test_mc2_candidate_context_never_returns_the_outcome(sandbox_state):
    store.write_jsonl("trade_plans.jsonl", [{"ticker": "NVDA", "date": "2026-07-20", "setup": "vcp",
                                             "gate_verdict": "GO", "score": 71,
                                             "r_multiple": 2.2, "pnl_dollars": 1234.5,
                                             "exit_reason": "target"}])
    res = _call("meridian_candidate_context", {"ticker": "NVDA"})
    text = res["result"]["content"][0]["text"]
    for leak in ("r_multiple", "pnl_dollars", "exit_reason"):
        assert leak not in text, f"sonuç sızdı: {leak} — ajanın 'tahmini' geriye dönük kusursuz olur"
    assert "gate_verdict" in text and "score" in text


def test_mc2b_unknown_ticker_is_honest(sandbox_state):
    store.write_jsonl("trade_plans.jsonl", [])
    res = _call("meridian_candidate_context", {"ticker": "ZZZZ"})
    assert '"found": false' in res["result"]["content"][0]["text"].lower()


# ---------- MC3: protokol dayanıklılığı ----------
def test_mc3_unknown_tool_is_an_error_not_a_crash():
    res = _call("meridian_send_order", {})
    assert res["error"]["code"] == -32602


def test_mc3b_unknown_method_and_notifications():
    assert mcp._handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    r = mcp._handle({"jsonrpc": "2.0", "id": 9, "method": "tools/uydurma"})
    assert r["error"]["code"] == -32601


def test_mc3c_tool_exception_becomes_text_not_a_dead_loop(monkeypatch):
    monkeypatch.setitem(mcp._BY_NAME["meridian_regime"], "fn",
                        lambda a: (_ for _ in ()).throw(RuntimeError("patla")))
    res = _call("meridian_regime")
    assert res["result"]["isError"] is True and "patla" in res["result"]["content"][0]["text"]


def test_mc3d_malformed_line_does_not_stop_the_server():
    out = io.StringIO()
    mcp.serve(stdin=io.StringIO('bozuk json\n{"jsonrpc":"2.0","id":2,"method":"ping"}\n'), stdout=out)
    lines = [json.loads(l) for l in out.getvalue().strip().splitlines()]
    assert lines[0]["error"]["code"] == -32700          # bozuk satır bildirildi
    assert lines[1]["id"] == 2 and lines[1]["result"] == {}   # ama döngü DEVAM etti


def test_tools_list_matches_the_registry():
    r = mcp._handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    names = {t["name"] for t in r["result"]["tools"]}
    assert names == {t["name"] for t in mcp.TOOLS}
    assert all(n.startswith("meridian_") for n in names)
