"""WP3 yogunluk anomalisi — CANLI GIRDI KANITI (SALT-OKUMA, stdin deseni; emsal exe007).
Ceker: inc_cache ozeti (anahtar/param/fold/holdout) + bars kapsami + evren + goal/strategy parmak izi.
YAZMA YOK."""
import datetime as dt, glob, hashlib, json, os

OUT = {"gorev": "wp3_yogunluk_anomali", "makine": "A1",
       "cekim": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

def _sha(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except Exception as e:
        return f"HATA:{type(e).__name__}"

BASE = "/opt/meridian"
# 1) inc_cache.json ozeti
try:
    d = json.load(open(os.path.join(BASE, "state/inc_cache.json")))
    ents = []
    for k, v in d.get("entries", {}).items():
        ents.append({
            "key": k[:400],
            "params_pos_size": (v.get("params") or {}).get("position_size_r"),
            "params": v.get("params"),
            "eval_regime": v.get("eval_regime"),
            "n_trades_total": v.get("n_trades_total"),
            "n_trades_graded": v.get("n_trades_graded"),
            "oos_split": v.get("oos_split"),
            "is_score": v.get("is_score"), "oos_score": v.get("oos_score"),
            "holdout_score": v.get("holdout_score"),
            "holdout_detail": v.get("holdout_detail"),
            "oos_folds": v.get("oos_folds"),
            "oos_folds_full": v.get("oos_folds_full"),
            "n_trades_search": len(v.get("_trades_search") or []),
            "n_trades_confirm": len(v.get("_trades_confirm") or []),
        })
    OUT["inc_cache"] = {"rev": d.get("rev"),
                        "rev_utc": dt.datetime.fromtimestamp(d["rev"], dt.timezone.utc).isoformat() if isinstance(d.get("rev"), (int, float)) else None,
                        "n_entries": len(d.get("entries", {})), "entries": ents,
                        "mtime": dt.datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, "state/inc_cache.json")), dt.timezone.utc).isoformat()}
except Exception as e:
    OUT["inc_cache"] = {"_hata": f"{type(e).__name__}: {e}"}

# 2) bars kapsami (sembol sayisi, son-bar dagilimi)
try:
    import csv as _csv
    import collections
    last = collections.Counter(); n = 0
    for p in sorted(glob.glob(os.path.join(BASE, "state/bars/*.csv"))):
        n += 1
        try:
            with open(p) as f:
                rows = f.read().strip().splitlines()
            last[rows[-1].split(",")[0]] += 1
        except Exception:
            last["_okunamadi"] += 1
    OUT["bars"] = {"n_files": n, "son_bar_dagilimi": dict(last.most_common(8))}
except Exception as e:
    OUT["bars"] = {"_hata": f"{type(e).__name__}: {e}"}

# 3) evren + strategy + goal
try:
    import sys
    sys.path.insert(0, BASE)
    from meridian.adapters import data as _d
    OUT["evren"] = {"replay_universe_n": len(_d.REPLAY_UNIVERSE),
                    "retired_n": len(getattr(_d, "RETIRED_SYMBOLS", []))}
except Exception as e:
    OUT["evren"] = {"_hata": f"{type(e).__name__}: {e}"}
for f, key in (("state/goal.yaml", "goal_sha"), ("state/bounds.yaml", "bounds_sha"),
               ("state/strategy.yaml", "strategy_sha")):
    OUT[key] = _sha(os.path.join(BASE, f))
try:
    OUT["strategy_head"] = open(os.path.join(BASE, "state/strategy.yaml")).read()[:900]
except Exception as e:
    OUT["strategy_head"] = f"HATA:{type(e).__name__}"

print(json.dumps(OUT, ensure_ascii=False))
