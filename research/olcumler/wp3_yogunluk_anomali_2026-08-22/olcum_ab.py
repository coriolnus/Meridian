"""WP3 yoğunluk anomalisi — KONTROLLÜ A/B TEŞHİS KOŞUMU (yerel, dar pencere; TARAMA DEĞİL).

Soru: aynı pencere + aynı barlar + aynı kodda, 2026-08-03..08-12 operatör paketi
(E1 limit serbest · derisk rampası 3/8→15/36 · slot 5→20 + boyut 1,0→0,5R) replay işlem
yoğunluğunu tek başına açıklıyor mu — ve eski dünyada hangi kapı kesiyor?

Yöntem: state/bars CSV'leri DOĞRUDAN okunur (adapters.load_many ÇAĞRILMAZ — bayat önbellek
yeniden-fetch + CSV yazımı tetiklerdi; state'e yazmak YASAK). Seriler FETCH_START=2021-01-01'e
kırpılır (inc_cache koşumlarıyla aynı taban — rejim q0.80 bağlamı; bkz. wp3_28d bağlam tuzağı).
`config.goal` ve `obs.warn/event` SÜREÇ-İÇİ yamanır (entry_law + derisk_ramp global config okur;
obs state'e yazmasın). replay SAF hesaptır — state'e yazmaz.

SINIR (beyanlı): koşum SOĞUK BAŞLAR (pencere başında boş portföy + START_EQUITY).
inc_cache'in walk'ı 2022'den gelir ve pencereye MİRAS özkaynak/dd ile girer — rampanın
dd-bacağı soğuk başlangıçta eksik ölçülür; sonuçlar bu şerhle okunur.
"""
import copy, json, sys, time
import pandas as pd

sys.path.insert(0, "/Users/erdemozturk/AI-Trading")
import yaml

from meridian import backtest, config as mconfig, obs as mobs
from meridian.adapters import data as mdata

FETCH_START = "2021-01-01"
BARS_DIR = "/Users/erdemozturk/AI-Trading/state/bars"
OUTP = "/Users/erdemozturk/AI-Trading/research/olcumler/wp3_yogunluk_anomali_2026-08-22/sonuc_ab.json"

# --- girdi: barlar (salt-okuma, dogrudan CSV) -------------------------------------------------
def load_csv(sym):
    df = pd.read_csv(f"{BARS_DIR}/{sym.lower()}.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df[df["date"] >= pd.Timestamp(FETCH_START)].reset_index(drop=True)

t0 = time.time()
index_bars = load_csv("SPY")
bars = {}
for s in mdata.REPLAY_UNIVERSE:
    try:
        bars[s] = load_csv(s)
    except FileNotFoundError:
        pass
YUKLEME = {"n_sembol": len(bars), "spy_ilk": str(index_bars["date"].iloc[0].date()),
           "spy_son": str(index_bars["date"].iloc[-1].date()), "sn": round(time.time() - t0, 1)}

goal_disk = yaml.safe_load(open("/Users/erdemozturk/AI-Trading/state/goal.yaml"))
strat = yaml.safe_load(open("/Users/erdemozturk/AI-Trading/state/strategy.yaml"))
P_V5 = dict(strat["params"])                       # position_size_r 0.5
P_V3 = {**P_V5, "position_size_r": 1.0}            # inc_cache yerel girdisiyle birebir (ölçüldü)

def eski_goal(g):
    g = copy.deepcopy(g)
    g["limits"]["max_open_positions"] = 5
    g["limits"]["derisk_full_dd"] = 0.03           # 08-12 öncesi kod-gömülü rampa
    g["limits"]["derisk_floor_dd"] = 0.08
    g["execution_v2"]["limit_atr_mult"] = 0.5      # 08-03 öncesi E1 kart-varsayılanı (bağlar)
    g["execution_v2"]["limit_pct_cap"] = 0.01
    g["execution_v2"]["gap_behavior"] = "cancel"   # marketable_limit öncesi davranış
    return g

# --- süreç-içi yamalar (state'e yazım sıfır) --------------------------------------------------
_AKTIF_GOAL = {"g": goal_disk}
mconfig.goal = lambda *a, **k: _AKTIF_GOAL["g"]
_UYARILAR = []
mobs.warn = lambda *a, **k: _UYARILAR.append((a, k))
if hasattr(mobs, "event"):
    mobs.event = lambda *a, **k: _UYARILAR.append((a, k))

def kos(ad, params, goal, sv, start, end):
    _AKTIF_GOAL["g"] = goal
    t = time.time()
    res = backtest.replay(params, bars, index_bars, goal, start, end,
                          strategy_version=sv, params_by_regime=None, with_gate_detail=False)
    sure = round(time.time() - t, 1)
    from collections import Counter
    verd = Counter(); nogo_neden = Counter()
    for p in (res.plan_log or []):
        v = p.get("gate_verdict")
        verd[v] += 1
        if v == "NO_GO":
            for r in (p.get("gate_reasons") or []):
                nogo_neden[str(r)[:60]] += 1
    kapali = [t_ for t_ in res.trades if t_.get("ts_close")]
    eq = [e[1] for e in (res.equity or [])]
    return {
        "arm": ad, "pencere": [start, end], "sure_sn": sure,
        "n_islem_kapali": len(kapali), "n_islem_defter": len(res.trades),
        "n_plan": len(res.plan_log or []),
        "verdicts": dict(verd), "nogo_nedenleri_top12": nogo_neden.most_common(12),
        "entry_rejects": res.entry_rejects, "earnings_gate": res.earnings_gate,
        "eq_son": round(eq[-1], 0) if eq else None,
        "eq_min": round(min(eq), 0) if eq else None,
    }

HOLD = ("2026-04-30", "2026-07-30")
F3 = ("2025-07-01", "2026-04-30")
ARMS = [
    ("H_A_yeni_dunya_v5", P_V5, goal_disk, 5, *HOLD),
    ("H_B_eski_dunya_v3", P_V3, eski_goal(goal_disk), 3, *HOLD),
]
# izolasyon kolları (tek düğme değişir, taban ESKİ dünya)
g = eski_goal(goal_disk); g["execution_v2"]["limit_atr_mult"] = 100.0
g["execution_v2"]["limit_pct_cap"] = 0.04; g["execution_v2"]["gap_behavior"] = "marketable_limit"
ARMS.append(("H_C_eski+E1serbest", P_V3, g, 3, *HOLD))
g = eski_goal(goal_disk); g["limits"]["derisk_full_dd"] = 0.15; g["limits"]["derisk_floor_dd"] = 0.36
ARMS.append(("H_D_eski+rampa1536", P_V3, g, 3, *HOLD))
g = eski_goal(goal_disk); g["limits"]["max_open_positions"] = 20
ARMS.append(("H_E_eski+slot20boyut05", P_V5, g, 5, *HOLD))
# 21-vs-249'un asıl penceresi (fold3-full) — iki uç dünya
ARMS.append(("F3_A_yeni_dunya_v5", P_V5, goal_disk, 5, *F3))
ARMS.append(("F3_B_eski_dunya_v3", P_V3, eski_goal(goal_disk), 3, *F3))

OUT = {"gorev": "wp3_yogunluk_anomali A/B", "yukleme": YUKLEME, "kollar": []}
for ad, p, gl, sv, s, e in ARMS:
    try:
        OUT["kollar"].append(kos(ad, p, gl, sv, s, e))
    except Exception as ex:
        OUT["kollar"].append({"arm": ad, "_hata": f"{type(ex).__name__}: {ex}"})
    json.dump(OUT, open(OUTP, "w"), ensure_ascii=False, indent=1)  # her kol sonrası diske
    print("BITTI:", ad, flush=True)
print("TAMAM", round(time.time() - t0, 1), "sn")
