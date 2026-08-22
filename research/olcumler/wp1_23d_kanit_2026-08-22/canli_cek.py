"""WP1-23d KART-KANITI · CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA; emsal: exe007/canli_cek.py,
edg042_kosum_2026-08-22/canli_cek.py — aynı ssh-stdin deseni).

KOŞUM (yerelden, canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/wp1_23d_kanit_2026-08-22/canli_cek.py \
        > research/olcumler/wp1_23d_kanit_2026-08-22/canli_ham.json

NE ÇEKER: trades.jsonl TÜM satırlar (23d örneklem sayımı için gereken alanlar) +
goal.slippage_bps künyesi. YAZMA YOK. UYDURMA YASAĞI: okunamayan kalem null + _hata.
"""
import datetime as dt
import json

OUT: dict = {"kalem": "WP1-23d kart-kaniti",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "makine": "A1 (canli)"}

try:
    from meridian import store
except Exception as e:
    OUT["_hata"] = f"meridian.store import: {type(e).__name__}: {e}"
    print(json.dumps(OUT))
    raise SystemExit(0)

try:
    trades = store.read_jsonl("trades.jsonl")
    TR_ALAN = ("id", "plan_id", "ticker", "ts_close", "side", "exit", "exit_reason",
               "kaynak", "broker_teyit", "broker_teyit_neden",
               "alpaca_fill_price", "alpaca_fill_beyan", "qty")
    OUT["trades"] = {"n": len(trades),
                     "satirlar": [{k: t.get(k) for k in TR_ALAN} for t in trades]}
except Exception as e:
    OUT["trades"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

try:
    from meridian import config
    OUT["goal_slippage_bps"] = config.goal().get("slippage_bps")
except Exception as e:
    OUT["goal_slippage_bps"] = None
    OUT["goal_slippage_bps_hata"] = f"{type(e).__name__}: {e}"

print(json.dumps(OUT))
