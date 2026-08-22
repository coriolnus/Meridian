"""WP3/28d KART-KANITI · CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA; emsal exe007/canli_cek.py).

KOŞUM (yerel oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/wp3_28d_kanit_2026-08-22/canli_cek.py \
        > research/olcumler/wp3_28d_kanit_2026-08-22/canli_ham.json

NE ÇEKER (hepsi salt-okuma; sır yok, emir yok, yazma yok):
  (1) state/bars/spy.csv — 2026-07-01 sonrası satırlar (yerel kuyruk 2026-08-12'de bitiyor;
      claim'i BUGÜNE taşımak için) + 2021-01-01→2026-08-12 pencersinin satır sayısı ve
      kapanış-toplamı (yerel/canlı veri-aynılık kontrolü).
  (2) state/regime.json — canlının BUGÜNKÜ rejim beyanı (premis "chop hiç oluşmadı" ise ve canlı
      bugün chop diyorsa, tek başına belirleyici).
  (3) state/inc_cache.json — girdi başına eval_regime, oos_split, search/confirm dilimlerinin
      rejim sayımları + chop işlemlerin ts_open listesi (kapının FİİLİ dilim büyüklükleri).
  (4) state/heartbeat.json.regime — son atımın rejimi (çapraz kontrol).

UYDURMA YASAĞI: okunamayan kalem null + `_hata` alanıyla döner.
"""
import datetime as dt
import json
from collections import Counter

OUT = {"kart_kaniti": "WP3/28d", "makine": "A1 (canli)",
       "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

# (1) spy.csv kuyruk + aynılık parmak izi
try:
    import pandas as pd
    spy = pd.read_csv("state/bars/spy.csv", parse_dates=["date"])
    kuyruk = spy[spy["date"] >= "2026-07-01"]
    pencere = spy[(spy["date"] >= "2021-01-01") & (spy["date"] <= "2026-08-12")]
    OUT["spy"] = {
        "son_bar": str(spy["date"].max().date()),
        "kuyruk_2026_07_01_sonrasi": kuyruk.assign(date=kuyruk["date"].dt.strftime("%Y-%m-%d"))
                                           .to_dict(orient="records"),
        "aynilik_2021_01_01__2026_08_12": {"satir": int(len(pencere)),
                                           "close_toplam": round(float(pencere["close"].sum()), 4)},
    }
except Exception as e:
    OUT["spy"] = None
    OUT["_spy_hata"] = f"{type(e).__name__}: {e}"

# (2) canlı rejim beyanı
try:
    OUT["regime_json"] = json.load(open("state/regime.json"))
except Exception as e:
    OUT["regime_json"] = None
    OUT["_regime_hata"] = f"{type(e).__name__}: {e}"

# (3) inc_cache dilim sayıları
try:
    inc = json.load(open("state/inc_cache.json"))
    ozet = []
    for v in inc.get("entries", {}).values():
        ts = v.get("_trades_search") or []
        tc = v.get("_trades_confirm") or []
        ozet.append({
            "eval_regime": v.get("eval_regime"), "oos_split": v.get("oos_split"),
            "n_trades_graded": v.get("n_trades_graded"),
            "search_rejim": dict(Counter(str(t.get("regime")) for t in ts)),
            "confirm_rejim": dict(Counter(str(t.get("regime")) for t in tc)),
            "chop_ts_open": sorted(str(t.get("ts_open"))[:10]
                                   for t in ts + tc if t.get("regime") == "chop"),
        })
    OUT["inc_cache"] = {"rev": inc.get("rev"), "girdi": ozet}
except Exception as e:
    OUT["inc_cache"] = None
    OUT["_inc_hata"] = f"{type(e).__name__}: {e}"

# (4) heartbeat rejimi
try:
    hb = json.load(open("state/heartbeat.json"))
    OUT["heartbeat"] = {"ts": hb.get("ts"), "regime": hb.get("regime")}
except Exception as e:
    OUT["heartbeat"] = None
    OUT["_hb_hata"] = f"{type(e).__name__}: {e}"

print(json.dumps(OUT))
