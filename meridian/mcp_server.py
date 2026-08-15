"""mcp_server.py — Meridian'ın SALT-OKUNUR durumunu yerel hermes-agent'a MCP aracı olarak açan stdio sunucusu.

NE YAPAR. Kanıt paketini prompt'a tıkıştırmak (ne gerekeceğini önceden bizim tahmin etmemiz)
yerine, ajan bir adayı düşünürken İHTİYACI OLAN veriyi kendisi sorgular. Bağımsız ve bağımlılıksız
bir stdio JSON-RPC (MCP) sunucusudur: satır-ayrımlı JSON-RPC 2.0 konuşur; hermes
`~/.hermes/config.yaml` içindeki mcp_servers kaydıyla başlatır. `serve()` EOF'a kadar döner;
initialize / ping / tools-list / tools-call metotları desteklenir, bozuk satır parse-error alır.

ARAÇLAR (hepsi getter): `meridian_regime` (rejim + maruziyet bütçesi), `meridian_calibrations`
(skor IC, LLM görüş, kapı meta, çıkış verimliliği, cf sadakati), `meridian_near_miss` (eşik-altı
adayların ölüm-nedeni karnesi), `meridian_cf_summary` (karşı-olgusal defter + skill katkısı),
`meridian_selfreview` (haftalık öz-değerlendirme), `meridian_candidate_context` (bir ticker için
karar-anı planı ve kapı gerekçeleri; sonuç/r_multiple DÖNMEZ — öngörü saflığı korunur).

DEĞİŞMEZLER. YETKİ SINIRI MUTLAKTIR: yalnız getter'lar — hiçbir araç state yazmaz, emir vermez,
kapıya dokunmaz; kapı yasası bozulamaz çünkü sunucu yalnızca okur. Her araç savunmacıdır: istisna
metne dönüşür (isError), döngü ölmez. Okur: store/analytics üzerinden state/ (regime.json,
kalibrasyon artefaktları, trade_plans.jsonl, cf_open.json, self_review.json). Hiçbir şey yazmaz."""
from __future__ import annotations
import json
import sys

from . import store, analytics


def _regime(_args: dict) -> dict:
    """Güncel rejim kaydı: tarih, rejim, maruziyet bütçesi/skoru, dağıtım günleri ve genişlik skoru.
    SALT OKUMA."""
    r = store.read_json("regime.json", {})
    return {k: r.get(k) for k in ("date", "regime", "exposure_budget_pct", "exposure_score",
                                  "min_exposure_score", "distribution_days", "breadth_score")}


def _calibrations(_args: dict) -> dict:
    """Kalibrasyon artefaktlarını tek sözlükte toplar (skor IC, LLM görüşü, kapı meta, çıkış verimliliği,
    cf sadakati). Bulunmayan artefakt None kalır — uydurma değer yok. SALT OKUMA."""
    return {
        "score": store.read_json("score_calibration.json", None),
        "llm_opinion": store.read_json("llm_calibration.json", None),
        "gate_meta": store.read_json("gate_calibration.json", None),
        "exit_efficiency": store.read_json("exit_efficiency.json", None),
        "cf_fidelity": store.read_json("cf_fidelity.json", None),
        "note": "cf-beslemeli kalibrasyonları cf_fidelity onaysızsa iskontolu oku",
    }


def _near_miss(_args: dict) -> dict:
    """Hangi giriş eşiği masada para bırakıyor? blocked_by kovası başına adet/giriş/ort.R."""
    return store.read_json("near_miss.json", {"resolved_total": 0, "buckets": {},
                                              "note": "henüz çözülmüş eşik-altı satır yok"})


def _cf_summary(_args: dict) -> dict:
    """Karşı-olgusal defter + skill katkısı — hangi ekran/kurulum gerçekten para kazanıyor."""
    try:
        attr = analytics.skill_attribution()
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        attr = None
    op = store.read_json("cf_open.json", [])
    return {"open_rows": len(op),
            "skill_attribution": attr if isinstance(attr, (list, dict)) else None,
            "note": "cf statik-bracket simülasyonu; canlı yasadan sapma cf_fidelity'de"}


def _selfreview(_args: dict) -> dict:
    """Haftalık öz-değerlendirmenin özeti: üretim damgası, dikkat maddeleri, çelişkiler ve ilerleme.
    SALT OKUMA."""
    r = store.read_json("self_review.json", {})
    return {"generated": r.get("generated"), "attention": r.get("attention", []),
            "contradictions": r.get("contradictions", []),
            "progress": r.get("progress", {})}


def _candidate_context(args: dict) -> dict:
    """Belirli bir ticker için BUGÜNÜN karar-anı planı (varsa) + son görüşü — ajan kendi kararını
    Meridian'ın kapı gerekçeleriyle çapraz okuyabilsin. Sonuç (r_multiple) DÖNMEZ (öngörü saflığı)."""
    tk = str(args.get("ticker", "")).upper()
    if not tk:
        return {"error": "ticker gerekli"}
    plans = store.read_jsonl("trade_plans.jsonl")
    mine = [p for p in plans if str(p.get("ticker", "")).upper() == tk]
    if not mine:
        return {"ticker": tk, "found": False}
    p = mine[-1]
    return {"ticker": tk, "found": True,
            "plan": {k: p.get(k) for k in ("date", "setup", "entry_trigger", "stop", "profit_target",
                                           "size_r", "score", "gate_verdict", "gate_reasons",
                                           "skill_chain", "llm_opinion", "p_win_shadow")}}


TOOLS = [
    {"name": "meridian_regime", "fn": _regime,
     "description": "Güncel piyasa rejimi ve maruziyet bütçesi (chop/trend_up, bütçe %, eşik).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_calibrations", "fn": _calibrations,
     "description": "Tüm kalibrasyon özetleri: skor IC, LLM görüş, kapı meta, çıkış verimliliği, cf sadakati.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_near_miss", "fn": _near_miss,
     "description": "Hangi giriş eşiği masada para bırakıyor — eşik-altı adayların ölüm-nedeni karnesi.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_cf_summary", "fn": _cf_summary,
     "description": "Karşı-olgusal defter özeti + skill/ekran katkısı (hangi kurulum para kazanıyor).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_selfreview", "fn": _selfreview,
     "description": "En son haftalık öz-değerlendirme: DİKKAT satırları, katmanlar-arası çelişkiler, ilerleme.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "meridian_candidate_context", "fn": _candidate_context,
     "description": "Bir ticker için karar-anı planı ve kapı gerekçeleri (sonuç dönmez).",
     "inputSchema": {"type": "object",
                     "properties": {"ticker": {"type": "string", "description": "Sembol, ör. NVDA"}},
                     "required": ["ticker"]}},
]
_BY_NAME = {t["name"]: t for t in TOOLS}
PROTOCOL_VERSION = "2024-11-05"


def _handle(msg: dict) -> dict | None:
    """Bir JSON-RPC isteğini işle. Bildirim (id yok) → None (yanıt yazılmaz)."""
    mid = msg.get("id")
    method = msg.get("method")
    if method == "initialize":
        client_pv = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": client_pv,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "meridian", "version": "1.0.0"}}}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "tools": [{"name": t["name"], "description": t["description"],
                       "inputSchema": t["inputSchema"]} for t in TOOLS]}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        tool = _BY_NAME.get(name)
        if not tool:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"bilinmeyen araç: {name}"}}
        try:
            payload = tool["fn"](params.get("arguments") or {})
            text = json.dumps(payload, ensure_ascii=False, default=str)
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": text}], "isError": False}}
        except Exception as e:                       # araç asla döngüyü düşürmez — hata metne döner
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": f"hata: {type(e).__name__}: {e}"}],
                "isError": True}}
    if mid is not None:                              # bilinmeyen METOT (bildirim değil) → standart hata
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"bilinmeyen metot: {method}"}}
    return None


def serve(stdin=None, stdout=None) -> None:
    """Satır-ayrımlı JSON-RPC döngüsü. EOF'ta çıkar. Bozuk satır → parse error (id yoksa sessiz geç)."""
    inp = stdin or sys.stdin
    outp = stdout or sys.stdout
    for line in inp:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            outp.write(json.dumps({"jsonrpc": "2.0", "id": None,
                                   "error": {"code": -32700, "message": "parse error"}}) + "\n")
            outp.flush()
            continue
        resp = _handle(msg)
        if resp is not None:
            outp.write(json.dumps(resp, ensure_ascii=False) + "\n")
            outp.flush()


if __name__ == "__main__":
    serve()
