"""EDG-2026-052 · E2 dakika-dogrulama — CIKIS BACAGI HAM KANIT CEKIMI (SALT-OKUMA).

ssh-stdin deseni (exe007 emsali): A1'de yalniz store.read_jsonl kosar; DOSYA YAZILMAZ,
POST/emir yok. trades.jsonl'dan yalniz alpaca_fill_price TASIYAN satirlar (cikis bacagi
gercek Alpaca dolumu) + olcumun kullandigi alanlar tasinir. UYDURMA YASAGI: okunamayan null+_hata.
"""
import datetime as dt
import json

OUT = {"kart": "EDG-2026-052",
       "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
       "makine": "A1 (canli)"}
try:
    from meridian import store
    trades = store.read_jsonl("trades.jsonl")
    ALAN = ("id", "plan_id", "ticker", "ts_open", "ts_close", "exit", "exit_reason",
            "alpaca_fill_price", "mirror_divergence", "kaynak", "regime")
    sec = [{k: t.get(k) for k in ALAN} for t in trades if t.get("alpaca_fill_price") is not None]
    OUT["trades_toplam_n"] = len(trades)
    OUT["alpaca_fill_price_satir_n"] = len(sec)
    OUT["satirlar"] = sec
except Exception as e:
    OUT["_hata"] = f"{type(e).__name__}: {e}"
print(json.dumps(OUT))
