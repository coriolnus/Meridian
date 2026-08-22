import json
d = json.load(open('/Users/erdemozturk/AI-Trading/state/inc_cache.json'))
for k, v in d['entries'].items():
    hs = v.get('holdout_score'); os_ = v.get('oos_score')
    print('---')
    print('eval_regime:', v.get('eval_regime'), '| oos_score:', os_, '| holdout_score:', hs)
    print('oos_split:', v.get('oos_split'))
    print('n_trades_total:', v.get('n_trades_total'), '| graded:', v.get('n_trades_graded'))
    ts = v.get('_trades_search') or []; tc = v.get('_trades_confirm') or []
    print('n _trades_search:', len(ts), '| n _trades_confirm:', len(tc))
    if tc:
        print('confirm trade keys:', sorted(tc[0].keys()))
