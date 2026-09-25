"""EDG-2026-102 PK-2 — Rol-1 elle doğrulama: 5 örnek satır ham parquet'ten BAĞIMSIZ yeniden türetilir.

A1'de: ssh ... '/opt/veri/pilot-venv/bin/python -' < pk2_elle.py
Yalnız okur; hiçbir yere yazmaz.
"""
import datetime as dt
import json
from zoneinfo import ZoneInfo

import pyarrow.compute as pc
import pyarrow.parquet as pq

KOK = "/opt/veri/olcum/edg102/olcum-2026-09-25"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc

d = json.load(open(f"{KOK}/sonuc.json"))
ornek = d["pk"]["pk2"]["ornekler"]


def et(ns):
    return dt.datetime.fromtimestamp(ns / 1e9, UTC).astimezone(NY)


tamam = 0
for o in ornek:
    tk, gun, eff = o["ticker"], o["seans"], o["eff_stop"]
    t = pq.read_table(f"/opt/veri/tick/islem/{gun}.parquet", columns=["ts", "sembol", "fiyat"])
    t = t.filter(pc.equal(t["sembol"], tk))
    kay = sorted(zip(t.column("ts").to_pylist(), [f / 1e4 for f in t.column("fiyat").to_pylist()]))
    seans = [(a, b) for a, b in kay if dt.time(9, 30) <= et(a).time() < dt.time(16, 0)]
    i = next((k for k, r in enumerate(seans) if r[1] <= eff), None)
    fill = seans[i + 1][1] if i is not None and i + 1 < len(seans) else None
    ek = (eff - fill) / eff * 1e4 if fill is not None else None
    ok = fill is not None and abs(fill - o["tick_fill"]) < 1e-9 and abs(ek - o["kayma_bps"]) < 1e-6
    tamam += ok
    saat = et(seans[i][0]).strftime("%H:%M:%S") if i is not None else None
    print(f"{tk} {gun} eff={eff:.4f} dokunus={seans[i][1] if i is not None else None} @{saat} ET"
          f" dolum={fill} kayma={None if ek is None else round(ek, 3)}"
          f" | betik dolum={o['tick_fill']} kayma={round(o['kayma_bps'], 3)}"
          f" -> {'UYUSUYOR' if ok else 'AYRISIYOR'}")
print(f"PK-2: {tamam}/{len(ornek)} uyusuyor")
