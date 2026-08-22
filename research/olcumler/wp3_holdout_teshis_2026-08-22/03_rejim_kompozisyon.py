"""H1: holdout penceresi rejim kompozisyonu — eğitim/OOS pencerelerinden farklı mı?
PIT yasası replay ile AYNI: her gün d için idx.loc[:d] dilimi -> regime.classify.
Kaynak: state/bars/spy.csv (SALT OKUMA). Geometri: TESHIS/inc_cache entry-3 anahtarı
IS 2022-01-01 -> OOS 2024-01-01..2026-04-30 (search 2024-01-11..2025-08-18 / confirm ..2026-04-30)
-> holdout 2026-04-30..2026-07-30 (91 gun)."""
import sys, json, collections
sys.path.insert(0, '/Users/erdemozturk/AI-Trading')
import pandas as pd
from meridian import regime as regime_mod

spy = pd.read_csv('/Users/erdemozturk/AI-Trading/state/bars/spy.csv', parse_dates=['date']).set_index('date')
spy = spy.loc['2021-01-01':]  # dataset.FETCH_START — replay'in gördüğü endeks tarihçesiyle AYNI taban

WINDOWS = [
    ("IS 2022-01-01..2024-01-01",       "2022-01-01", "2024-01-01"),
    ("OOS-search 2024-01-11..2025-08-18","2024-01-11", "2025-08-18"),
    ("OOS-confirm 2025-08-18..2026-04-30","2025-08-18", "2026-04-30"),
    ("OOS-tam 2024-01-01..2026-04-30",  "2024-01-01", "2026-04-30"),
    ("HOLDOUT 2026-04-30..2026-07-30",  "2026-04-30", "2026-07-30"),
    ("artik-fold 2025-07-01..2025-08-18","2025-07-01", "2025-08-18"),
]

days = spy.loc["2022-01-01":"2026-07-30"].index
labels = {}
for d in days:
    sl = spy.loc[:d]
    reg, _m = regime_mod.classify(sl.reset_index())
    labels[str(d.date())] = reg

out = {}
print(f"{'pencere':42s} {'n_gun':>5s}  kompozisyon (gun ve %)")
for name, lo, hi in WINDOWS:
    sel = [r for dd, r in labels.items() if lo <= dd < hi]
    c = collections.Counter(sel); n = len(sel)
    comp = {k: {"gun": v, "pct": round(100*v/n, 1)} for k, v in sorted(c.items(), key=lambda kv: -kv[1])}
    # SPY kendi getirisi (pencere ici, kapanis->kapanis)
    w = spy.loc[lo:hi]["close"]
    ret = round(float(w.iloc[-1]/w.iloc[0] - 1)*100, 2) if len(w) > 1 else None
    # pencere ici SPY max drawdown
    mdd = round(float((1 - w/w.cummax()).max())*100, 2) if len(w) > 1 else None
    out[name] = {"n_gun": n, "kompozisyon": comp, "spy_getiri_pct": ret, "spy_mdd_pct": mdd}
    comp_s = " ".join(f"{k}:{v['gun']}g/%{v['pct']}" for k, v in comp.items())
    print(f"{name:42s} {n:5d}  {comp_s}  | SPY getiri %{ret} mdd %{mdd}")

json.dump({"labels_gunluk": labels, "pencereler": out}, open(
    '/Users/erdemozturk/AI-Trading/research/olcumler/wp3_holdout_teshis_2026-08-22/rejim_kompozisyon.json', 'w'), indent=1)
print("\nOK -> rejim_kompozisyon.json")
