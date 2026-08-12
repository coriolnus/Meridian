"""EDG-036 AŞAMA-0 ikinci salt-okuma turu: doc-varlıklar (DB), yasa dosyaları, öğrenme kapıları."""
import json, sqlite3
from collections import Counter
from pathlib import Path

STATE = Path("/opt/meridian/state")
DB = STATE / "meridian.db"
out = {}

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
out["tablolar"] = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
for tbl, ad in (("scoreboard", "scoreboard"), ("portfolio", "portfolio"),
                ("shadow_books", "shadow_books")):
    try:
        r = con.execute(f"SELECT doc_json FROM {tbl} LIMIT 1").fetchone()
        out[ad] = json.loads(r[0]) if r else None
    except Exception as e:
        out[ad] = f"okunamadi: {type(e).__name__}: {e}"

sb = out.get("scoreboard") or {}
if isinstance(sb, dict):
    out["scoreboard_ozet"] = {"current_version": sb.get("current_version"),
                              "versions": {k: {kk: v.get(kk) for kk in
                                               ("live_score", "backtest_oos", "rolled_back",
                                                "parent", "shipped_at", "n_trades")}
                                           for k, v in (sb.get("versions") or {}).items()}}
p = out.get("portfolio") or {}
if isinstance(p, dict):
    out["portfolio_ozet"] = {k: p.get(k) for k in
                             ("realized_pnl", "cash", "equity", "positions", "last_id", "_id")
                             if k in p}
    out["portfolio_anahtarlar"] = sorted(p.keys())

# trade_plans: tohum planları var mı? (llm join tabanı)
out["plans_n"] = con.execute("SELECT COUNT(*) FROM trade_plans").fetchone()[0]
tr = [dict(r) for r in con.execute(
    "SELECT id, plan_id, strategy_version, kaynak, ts_close, setup, regime, score FROM trades")]
out["sv_x_kaynak"] = dict(Counter(f"sv={t['strategy_version']}|{t['kaynak']}" for t in tr))
out["setup_x_kaynak"] = dict(Counter(f"{t['setup']}|{t['kaynak']}" for t in tr))
out["regime_x_kaynak"] = dict(Counter(f"{t['regime']}|{t['kaynak']}" for t in tr))
# plan join oranı
pids = {r[0] for r in con.execute("SELECT id FROM trade_plans")}
out["plan_join"] = {
    "seed_eslesen": sum(1 for t in tr if t["kaynak"] == "replay_seed" and t["plan_id"] in pids),
    "seed_n": sum(1 for t in tr if t["kaynak"] == "replay_seed"),
    "live_eslesen": sum(1 for t in tr if t["kaynak"] == "live_paper" and t["plan_id"] in pids),
    "live_n": sum(1 for t in tr if t["kaynak"] == "live_paper"),
    "ornek_seed_plan_id": [t["plan_id"] for t in tr if t["kaynak"] == "replay_seed"][:3],
    "ornek_live_plan_id": [t["plan_id"] for t in tr if t["kaynak"] == "live_paper"][:3],
}

# llm_opinion taşıyan plan sayısı
opl = 0
for r in con.execute("SELECT extra_json FROM trade_plans"):
    if r[0] and '"llm_opinion"' in r[0]:
        opl += 1
out["plan_llm_opinion_n"] = opl


def jread(name, default=None):
    q = STATE / name
    if not q.exists():
        return default
    try:
        return json.loads(q.read_text())
    except Exception as e:
        return {"_okunamadi": f"{type(e).__name__}: {e}"}


import yaml  # noqa: E402
def yread(name):
    q = STATE / name
    return yaml.safe_load(q.read_text()) if q.exists() else None


st = yread("strategy.yaml") or {}
out["strategy"] = {k: st.get(k) for k in ("version", "parent", "regime")}
g = yread("goal.yaml") or {}
out["goal"] = {k: g.get(k) for k in ("min_sample", "reflection_every", "max_drawdown",
                                     "target_annual_return", "max_open_positions")}

for f in ("hermes_status.json", "axis2_status.json", "learning_loop_open.json",
          "skill_gorus_durum.json", "self_review.json", "shadow_model.json",
          "regime_trigger.json", "mae_profile.json", "validation_report.json",
          "gate_calibration.json", "learning_cadence.json", "sieve.json"):
    d = jread(f)
    out[f] = None if d is None else (sorted(d.keys()) if isinstance(d, dict) else type(d).__name__)

hs = jread("hermes_status.json") or {}
out["hermes_status_ozet"] = {k: hs.get(k) for k in
                             ("last_reflect_at", "reflections", "last_reflection", "last_result",
                              "horizon_ready", "horizon_regime", "closed_trades")}
out["axis2_status"] = jread("axis2_status.json")
out["learning_loop_open"] = jread("learning_loop_open.json")
out["regime_trigger"] = jread("regime_trigger.json")
sm = jread("shadow_model.json") or {}
out["shadow_model_ozet"] = {k: sm.get(k) for k in
                            ("n", "n_real", "n_cf", "trained_at", "auc", "fingerprint", "promoted",
                             "n_live", "durum") if k in sm}
sv = jread("sieve.json") or {}
out["sieve_stages"] = {k: {"in": v.get("in"), "out": v.get("out"),
                           "drops": v.get("drops"), "ts": v.get("ts")}
                       for k, v in (sv.get("stages") or {}).items()} if isinstance(sv, dict) else None
out["skill_gorus_durum"] = jread("skill_gorus_durum.json")
mp = jread("mae_profile.json") or {}
out["mae_profile_ozet"] = {k: mp.get(k) for k in ("n", "n_gercek", "n_cf", "verdict") if k in mp}
vr = jread("validation_report.json") or {}
out["validation_report_ozet"] = {k: vr.get(k) for k in ("real_n", "n", "verdict", "ts") if k in vr}

print(json.dumps(out, ensure_ascii=False, default=str))
