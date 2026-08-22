"""Holdout ici kirilim: ay, cikis nedeni, en kotu isimler — negatifin yapisi."""
import sqlite3, collections, json
DB = '/Users/erdemozturk/AI-Trading/research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db'
con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("SELECT * FROM trades")]; con.close()

def seg(lo, hi):
    return [t for t in rows if lo <= str(t['ts_open'])[:10] < hi and (not t['ts_close'] or str(t['ts_close'])[:10] <= hi)]

H = seg("2026-04-30", "2026-07-30"); C = seg("2025-08-18", "2026-04-30")
out = {}
def brk(ts, key):
    g = collections.defaultdict(list)
    for t in ts: g[key(t)].append(float(t['r_multiple'] or 0))
    return {k: {"n": len(v), "avg_r": round(sum(v)/len(v), 3), "sum_r": round(sum(v), 2)}
            for k, v in sorted(g.items())}
out['holdout_ay'] = brk(H, lambda t: str(t['ts_open'])[:7])
out['holdout_cikis'] = brk(H, lambda t: t['exit_reason'])
out['confirm_cikis'] = brk(C, lambda t: t['exit_reason'])
losers = sorted(H, key=lambda t: float(t['r_multiple'] or 0))[:8]
out['holdout_en_kotu8'] = [{"t": t['ticker'], "open": str(t['ts_open'])[:10], "r": t['r_multiple'],
                            "exit": t['exit_reason'], "setup": t['setup']} for t in losers]
out['holdout_setup'] = brk(H, lambda t: t['setup'])
out['confirm_setup'] = brk(C, lambda t: t['setup'])
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open('/Users/erdemozturk/AI-Trading/research/olcumler/wp3_holdout_teshis_2026-08-22/holdout_kirilim.json', 'w'), indent=1, ensure_ascii=False)
