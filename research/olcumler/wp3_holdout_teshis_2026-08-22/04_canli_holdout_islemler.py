"""H2 (orneklem) + H3 (bilesen ayrismasi) — CANLI-KOPYA popülasyon üzerinde.
Kaynak: research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db
(canli A1'in 2026-08-22 kopyasi; exe003 almis, SALT OKUMA).
NOT (baglam tuzagi): bunlar CANLI islemler; -0,5366 REPLAY islemlerinden olculdu.
Ayni pencere, ayni strateji ailesi, FARKLI populasyon — vekil olcum, esdeger degil."""
import sys, json, sqlite3, collections
sys.path.insert(0, '/Users/erdemozturk/AI-Trading')
import yaml
from meridian import score as score_mod

DB = '/Users/erdemozturk/AI-Trading/research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db'
goal = yaml.safe_load(open('/Users/erdemozturk/AI-Trading/state/goal.yaml'))

con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("SELECT * FROM trades")]
con.close()

def in_segment(t, lo, hi):
    """backtest._in_segment ile AYNI yasa: yari-acik acilis + kapanis dilim icinde."""
    op = str(t.get('ts_open') or '')[:10]; cl = str(t.get('ts_close') or '')[:10]
    return bool(lo <= op < hi and (not cl or cl <= hi))

WINDOWS = [
    ("IS 2022-01-01..2024-01-01",        "2022-01-01", "2024-01-01", 731),
    ("OOS-search 2024-01-11..2025-08-18","2024-01-11", "2025-08-18", 585),
    ("OOS-confirm 2025-08-18..2026-04-30","2025-08-18", "2026-04-30", 255),
    ("HOLDOUT 2026-04-30..2026-07-30",   "2026-04-30", "2026-07-30",  91),
]
out = {}
for name, lo, hi, span in WINDOWS:
    seg = [t for t in rows if in_segment(t, lo, hi)]
    n = len(seg)
    reg = collections.Counter(str(t.get('regime')) for t in seg)
    expl = sum(1 for t in seg if t.get('exploration'))
    avg_r = round(sum(float(t.get('r_multiple') or 0) for t in seg)/n, 4) if n else None
    win = round(100*sum(1 for t in seg if float(t.get('r_multiple') or 0) > 0)/n, 1) if n else None
    pnl = round(sum(float(t.get('pnl_dollars') or 0) for t in seg), 2)
    det = score_mod.score_detail(seg, goal, span_days=span)  # mtm yok — kapali-islem egrisi (canli M2M kopyada yok, None degil ama eksik bacak: dd yalniz kapali-islem)
    out[name] = {"n": n, "rejim_dagilimi": dict(reg), "exploration_n": expl,
                 "avg_r": avg_r, "win_pct": win, "pnl_dolar": pnl,
                 "score_detail": {k: v for k, v in det.items() if k != 'targets'}}
    print(f"== {name}: n={n} rejim={dict(reg)} expl={expl} avg_r={avg_r} win%={win} pnl=${pnl}")
    print("   score:", det.get('score'), "| components:", det.get('components'),
          "| reason:", det.get('reason'), "| dd:", det.get('max_drawdown'),
          "| realized_30d:", det.get('realized_30d'), "| sharpe:", det.get('sharpe'))

# aylik islem yogunlugu — kuraklik zaman serisi (son 12 ay)
aylik = collections.Counter(str(t['ts_open'])[:7] for t in rows if str(t['ts_open']) >= '2025-08')
print("\naylik islem sayisi (canli, acilis ayina gore):", dict(sorted(aylik.items())))
out['aylik_2025-08_sonrasi'] = dict(sorted(aylik.items()))
json.dump(out, open('/Users/erdemozturk/AI-Trading/research/olcumler/wp3_holdout_teshis_2026-08-22/canli_holdout_islemler.json', 'w'), indent=1, ensure_ascii=False)
print("\nOK -> canli_holdout_islemler.json")
