"""cur_score değişimi ARTEFAKTTAN mı GOAL değişiminden mi? İki eksen ayrı ayrı çevrilir."""
import copy, json, os, sys
from pathlib import Path
REPO=Path("/Users/erdemozturk/AI-Trading"); sys.path.insert(0,str(REPO))
os.environ["MERIDIAN_DB"]="off"
from meridian import config
config.STATE=Path(sys.argv[1])/"base"; config.BARS=config.STATE/"bars"; config.HISTORY=config.STATE/"history"
config.reload_config()
from meridian import score as score_mod
D=REPO/"research/olcumler/edg036b_yenileme_kuru_2026-08-13"
tam=json.loads((D/"islemler_tam_kontrolgd.json").read_text())
slim=json.loads((D/"islemler_kontrol.json").read_text())          # 032'nin SLIM projeksiyonu
goal_yeni=config.goal()
goal_eski=copy.deepcopy(goal_yeni); goal_eski["max_drawdown"]=0.08   # 036 ilk kuru koşumundaki hâl
out={}
for gad,g in (("goal_max_dd_0.16_BUGUN",goal_yeni),("goal_max_dd_0.08_036_ilk_kosum",goal_eski)):
    for dad,rows in (("TAM_SATIR_885",tam),("SLIM_12_ALAN_885",slim)):
        out[f"{gad} | {dad}"]=score_mod.score(rows,g)
print(json.dumps(out,ensure_ascii=False,indent=1))
