import importlib, json, os, sys
from pathlib import Path
REPO=Path("/Users/erdemozturk/AI-Trading"); sys.path.insert(0,str(REPO))
os.environ["MERIDIAN_DB"]="off"
w=Path(sys.argv[1])
from meridian import config
config.STATE=w; config.BARS=w/"bars"; config.HISTORY=w/"history"; config.reload_config()
import meridian.store as store, meridian.storage as storage
for m in (store,storage): importlib.reload(m)
from meridian import shadowlaw, score as score_mod
importlib.reload(shadowlaw)
tr=store.read_jsonl("trades.jsonl"); goal=config.goal()
d=shadowlaw.variance_drift(tr,goal)          # İLK çağrı — sıra kirlenmesi yok
print(json.dumps({"dunya":w.name,"n":len(tr),"kayma_n":len(d["kayma"]),
                  "margin_scale":(d.get("olcum") or {}).get("margin_scale"),
                  "kayitli":shadowlaw.MEASURED_V3["margin_scale"],
                  "MONEY_GATE_MARGIN":shadowlaw.MONEY_GATE_MARGIN,
                  "score_tum":score_mod.score(tr,goal),
                  "min_sample":goal.get("min_sample"),
                  "rollback_if_worse_by":goal.get("rollback_if_worse_by")},ensure_ascii=False))
