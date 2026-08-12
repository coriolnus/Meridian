"""EDG-2026-036 AŞAMA-0 — CANLI SALT-OKUMA KANITI (hiçbir bayt yazılmaz).

DB read-only URI ile açılır (mode=ro). state/*.json düz `open()` ile okunur.
meridian.store KULLANILMAZ: `store.read_*` → `db_backed()` → bayat-defter süzgeci (rename = YAZIM).
"""
import json, os, sqlite3, sys
from collections import Counter
from pathlib import Path

STATE = Path("/opt/meridian/state")
DB = STATE / "meridian.db"
out = {"state": str(STATE), "db_var": DB.exists()}


def jread(name, default=None):
    p = STATE / name
    if not p.exists():
        return default
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        return {"_okunamadi": f"{type(e).__name__}: {e}"}


def jlread(name, limit=None):
    p = STATE / name
    if not p.exists():
        return []
    rows = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows[-limit:] if limit else rows


# ---- 1) TRADES (DB, salt-okuma) ---------------------------------------------------------------
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cols = [r[1] for r in con.execute("PRAGMA table_info(trades)")]
out["trades_kolonlari"] = cols
rows = []
for r in con.execute("SELECT * FROM trades ORDER BY rowid"):
    d = dict(r)
    ex = d.pop("extra_json", None)
    if ex:
        try:
            d.update(json.loads(ex))
        except Exception:
            pass
    rows.append(d)
out["trades_n"] = len(rows)
out["kaynak_dagilimi"] = dict(Counter(str(t.get("kaynak")) for t in rows))
out["sv_dagilimi"] = dict(Counter(f"{t.get('kaynak')}|sv={t.get('strategy_version')}" for t in rows))

# ALAN SAYIMI (kaynak kırılımlı): hangi alan hangi dilimde DOLU?
alanlar = {}
for t in rows:
    k = str(t.get("kaynak"))
    for a, v in t.items():
        d = alanlar.setdefault(a, {})
        c = d.setdefault(k, {"var": 0, "dolu": 0})
        c["var"] += 1
        if v is not None:
            c["dolu"] += 1
out["alan_sayimi"] = alanlar

out["pnl"] = {}
for k in set(str(t.get("kaynak")) for t in rows):
    dil = [t for t in rows if str(t.get("kaynak")) == k]
    pn = [float(t["pnl_dollars"]) for t in dil if t.get("pnl_dollars") is not None]
    rm = [float(t["r_multiple"]) for t in dil if t.get("r_multiple") is not None]
    out["pnl"][k] = {"n": len(dil), "n_pnl": len(pn), "toplam_pnl": round(sum(pn), 2),
                     "ort_pnl": round(sum(pn) / len(pn), 2) if pn else None,
                     "n_r": len(rm), "ort_r": round(sum(rm) / len(rm), 4) if rm else None,
                     "ts_min": min((str(t.get("ts_close") or "") for t in dil), default=None),
                     "ts_max": max((str(t.get("ts_close") or "") for t in dil), default=None)}

# ---- 2) DSR: aynı formül, ÜÇ payda ------------------------------------------------------------
sys.path.insert(0, "/opt/meridian")
from meridian import validation as _val          # saf matematik (yazmaz)
from meridian import score as _score             # START_EQUITY
from meridian import dataset as _ds

SE = float(_score.START_EQUITY)


def _dsr(dilim, n_trials):
    ret = [float(t["pnl_dollars"]) / SE for t in dilim if t.get("pnl_dollars") is not None]
    return {"n_ret": len(ret), "dsr": _val.deflated_sharpe(ret, max(1, n_trials))}


# n_trials: validation_trio ile AYNI kanal (oos_erosion dosyası + hypotheses k_probes)
ero = jread("oos_erosion.json", {}) or {}
ws = (ero.get("windows") or {})
guncel = {k: v for k, v in ws.items() if v.get("pencere_id") == _ds.ROTATION_ID}
sorgu = sum(int(v.get("queries") or 0) for v in guncel.values())
hyp = jlread("hypotheses.jsonl")
kp = sum(int(((h.get("backtest") or {}).get("k_probes")) or 0) for h in hyp)
n_trials = sorgu + kp
out["n_trials"] = {"toplam": n_trials, "erosion_sorgu_guncel_pencere": sorgu, "k_probes": kp,
                   "pencere_id": _ds.ROTATION_ID, "erosion_n_pencere_guncel": len(guncel),
                   "erosion_n_pencere_hepsi": len(ws)}
out["dsr"] = {
    "TUM_DEFTER (validation_trio'nun fiilen kullandığı)": _dsr(rows, n_trials),
    "yalniz_live_paper": _dsr([t for t in rows if t.get("kaynak") == "live_paper"], n_trials),
    "yalniz_replay_seed": _dsr([t for t in rows if t.get("kaynak") == "replay_seed"], n_trials),
    "DSR_MIN_N": _val.DSR_MIN_N, "DSR_HARD_MIN": _val.DSR_HARD_MIN,
}

# ---- 3) PBO tabanı ----------------------------------------------------------------------------
vled = jlread("validation_ledger.jsonl")
out["pbo_tabani"] = {
    "validation_ledger_n": len(vled),
    "guncel_pencere_n": sum(1 for r in vled if r.get("pencere_id") == _ds.ROTATION_ID),
    "PBO_MIN_ADAY": _val.PBO_MIN_ADAY,
    "seri_tasiyan_n": sum(1 for r in vled if r.get("seri")),
    "not": "PBO trades defterini HİÇ okumaz — adayların kendi getiri serilerinden hesaplanır",
}

# ---- 4) TÜKETİCİ ARTEFAKTLARI (yazılmış hâlleri — üretici çağrılmaz) --------------------------
def kisalt(d, alanlar):
    if not isinstance(d, dict):
        return d
    return {a: d.get(a) for a in alanlar if a in d}


sc = jread("score_calibration.json")
out["score_calibration.json"] = None if sc is None else {
    "n": sc.get("n"), "n_real": sc.get("n_real"), "n_cf": sc.get("n_cf"),
    "rank_ic_havuz": sc.get("rank_ic"),
    "katmanlar": sc.get("katmanlar"),
    "gercek_kaynak": sc.get("gercek_kaynak"),
    "verdict": sc.get("verdict"),
}
llm = jread("llm_calibration.json")
out["llm_calibration.json"] = None if llm is None else kisalt(
    llm, ["n", "n_gercek", "n_cf", "pairs", "n_pairs", "kovalar", "buckets", "verdict", "hukum",
          "promoted", "terfi", "brier", "hit_rate", "eleme", "prov"])
out["llm_calibration.json_anahtarlar"] = None if llm is None else sorted(llm.keys())

nm = jread("near_miss.json")
out["near_miss.json_anahtarlar"] = None if nm is None else sorted(nm.keys())
out["near_miss.json"] = None if nm is None else kisalt(
    nm, ["n", "n_gercek", "n_cf", "esik", "satirlar_n", "verdict", "hukum", "kapsam", "prov"])

cff = jread("cf_fidelity.json")
out["cf_fidelity.json"] = None if cff is None else kisalt(
    cff, ["n_gercek", "n_cf", "n_kesisim", "kapsam", "verdict", "hukum", "sadakat", "prov"])
out["cf_fidelity.json_anahtarlar"] = None if cff is None else sorted(cff.keys())

ee = jread("exit_efficiency.json")
out["exit_efficiency.json"] = None if ee is None else kisalt(
    ee, ["n", "n_gercek", "n_cf", "verdict", "prov"])

cic = jread("component_ic.json")
out["component_ic.json_anahtarlar"] = None if cic is None else sorted(cic.keys())
out["component_ic.json"] = None if cic is None else kisalt(
    cic, ["n", "n_gercek", "n_cf", "katmanlar", "verdict", "prov"])

tc = jread("threshold_curve.json")
out["threshold_curve.json"] = None if tc is None else kisalt(
    tc, ["n", "n_gercek", "n_cf", "verdict", "prov"])

sv = jread("sieve.json")
out["sieve.json_asamalar"] = None if not isinstance(sv, dict) else {
    k: {"in": v.get("in"), "out": v.get("out"), "drops": v.get("drops")}
    for k, v in (sv.get("stages") or {}).items()}

ax2 = jread("skills_axis2.json") or jread("axis2.json")
out["axis2_dosyasi"] = None if ax2 is None else kisalt(ax2, ["sayim", "aktif_payda", "esik", "ts"])

sb = jread("scoreboard.json")
out["scoreboard"] = None if not isinstance(sb, dict) else {
    "current_version": sb.get("current_version"),
    "versions": sorted((sb.get("versions") or {}).keys())}

port = jread("portfolio.json")
out["portfolio_realized_pnl"] = None if not isinstance(port, dict) else port.get("realized_pnl")

sm = jread("shadow_model.json")
out["shadow_model_anahtarlar"] = None if sm is None else sorted(sm.keys()) if isinstance(sm, dict) else type(sm).__name__

out["hypotheses_n"] = len(hyp)
out["hypotheses_status"] = dict(Counter(h.get("status") for h in hyp))
gorus = jlread("skill_gorusleri.jsonl") or jlread("skill_gorus.jsonl")
out["skill_gorus_defteri_n"] = len(gorus)
cfled = jlread("counterfactuals.jsonl")
out["counterfactuals_n"] = len(cfled)

# state dizin listesi (hangi tüketici artefaktı VAR?)
out["state_dosyalari"] = sorted(p.name for p in STATE.iterdir() if p.is_file())

print(json.dumps(out, ensure_ascii=False, default=str))
