"""ÖNCE sütunu — canlı state SNAPSHOT'ının KOPYASI üzerinde salt-okuma. Gerçek state'e yazmaz."""
import json, os, pathlib, sys
SB = pathlib.Path(__file__).resolve().parent
os.environ["MERIDIAN_ROOT"] = str(SB); sys.path.insert(0, str(SB))
from meridian import config
config.STATE = SB / "state_once"; config.HISTORY = config.STATE / "history"; config.BARS = config.STATE / "bars"
from meridian import analytics, store
out = {}
for ad, fn in (("result_verdict", analytics.result_verdict),
               ("profit_waterfall", analytics.profit_waterfall),
               ("cf_fidelity", analytics.cf_fidelity)):
    try:
        out[ad] = fn()
    except Exception as e:
        out[ad] = {"olculdu": False, "neden": f"{type(e).__name__}: {e}"}
try:
    out["live_expectancy_ceiling"] = analytics.live_expectancy_ceiling()
except Exception as e:
    out["live_expectancy_ceiling"] = {"olculdu": False, "neden": f"{type(e).__name__}: {e}"}
out["scoreboard"] = store.read_json("scoreboard.json", None)
out["motor"] = str(pathlib.Path(analytics.__file__).resolve())
(SB / "once.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
print("YAZILDI once.json")
