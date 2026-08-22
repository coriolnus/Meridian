import json
d = json.load(open('/Users/erdemozturk/AI-Trading/state/inc_cache.json'))
for k, v in d['entries'].items():
    if v.get('eval_regime') is not None:
        continue
    print('='*80)
    # anahtar tuple'ından pencereler
    print('KEY windows:', k[:250])
    print('oos_split:', v['oos_split'])
    print('oos_score:', v['oos_score'], '| holdout_score:', v['holdout_score'])
    hd = v.get('holdout_detail') or {}
    print('holdout_detail:', json.dumps(hd, ensure_ascii=False)[:800])
    od = v.get('oos_detail') or {}
    print('oos_detail keys:', sorted(od.keys()) if isinstance(od, dict) else type(od))
    if isinstance(od, dict):
        print('oos components:', od.get('components'), '| n:', od.get('n_trades'), od.get('n'))
    print('oos_folds:', v.get('oos_folds'))
    print('oos_folds_full:', v.get('oos_folds_full'))
