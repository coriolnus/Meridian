"""EDG-2026-106 PK-2 — Rol-1 BAĞIMSIZ yeniden türetme (betiğin kodunu KULLANMAZ).

A1'de: ssh … '/opt/veri/pilot-venv/bin/python -' < edg106_pk2_elle.py
Girdi olarak yalnız örneklerin KİMLİĞİ + plan girdileri (ticker, seans, tetik, entry, ref_kapanis) alınır;
f, L, t0, dal, dolum ve fark ham parquet + bar CSV'den burada ayrıca hesaplanır. Hiçbir yere yazmaz.
"""
import csv
import datetime as dt
import json
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from zoneinfo import ZoneInfo

import pyarrow.compute as pc
import pyarrow.parquet as pq

NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
d = json.load(open("/opt/veri/olcum/edg106/elle-2026-09-25/sonuc.json"))
ornek = d["pk"]["pk2"]["ornekler"]
F = [Fraction(1)] + [Fraction(1, k) for k in range(2, 31)] + [Fraction(k) for k in range(2, 11)] + \
    [Fraction(2, 3), Fraction(3, 4), Fraction(4, 5), Fraction(3, 2), Fraction(4, 3), Fraction(5, 4)]


def ns_et(ns):
    return dt.datetime.fromtimestamp(ns / 1e9, UTC).astimezone(NY)


def py_round(x, n):
    # canlı zincir Python round() kullanır (float) — aynısı
    return round(x, n)


tamam = 0
for o in ornek:
    tk, gun = o["ticker"], o["seans"]
    tetik, entry, ref = Decimal(str(o["tetik"])), Decimal(str(o["entry"])), Decimal(str(o["ref_kapanis"]))
    bar = next(r for r in csv.DictReader(open(f"/opt/meridian/state/bars/{tk.lower().replace('.', '-')}.csv")) if r["date"][:10] == gun)
    bar_acilis = Decimal(bar["open"])
    t = pq.read_table(f"/opt/veri/tick/islem/{gun}.parquet", columns=["ts", "sembol", "fiyat"])
    t = t.filter(pc.equal(t["sembol"], tk))
    kay = sorted(zip(t.column("ts").to_pylist(), t.column("fiyat").to_pylist()), key=lambda x: x[0])
    seans = [(ts, Decimal(f) / Decimal(10000)) for ts, f in kay if dt.time(9, 30) <= ns_et(ts).time() < dt.time(16, 0)]
    r = Fraction(bar_acilis) / Fraction(seans[0][1])
    f = min(F, key=lambda c: abs(r / c - 1))
    f = f if abs(r / f - 1) <= Fraction(2, 100) else None
    fD = Decimal(f.numerator) / Decimal(f.denominator)
    tetik_h, entry_h, ref_h = tetik / fD, entry / fD, ref / fD
    L = Decimal(str(py_round(py_round(float(tetik_h) * 1.04, 4), 2)))
    dal = "GAP" if ref_h >= tetik_h else "STOP_LIMIT"
    i0 = next(i for i, (ts, _) in enumerate(seans) if ns_et(ts).time() >= dt.time(9, 45))
    dolum = None
    if dal == "GAP":
        dolum = next((p for ts, p in seans[i0 + 1:] if p <= L), None)
    else:
        ia = next((i for i in range(i0, len(seans)) if seans[i][1] >= tetik_h), None)
        if ia is not None:
            dolum = next((p for ts, p in seans[ia + 1:] if p <= L), None)
    fark = None if dolum is None else float((dolum - entry_h) / entry_h * 10000)
    ok = (str(f) == str(o["olcek_f"]) and dal == o["dal"] and
          ((dolum is None and o["canli_dolum"] is None) or
           (dolum is not None and o["canli_dolum"] is not None and abs(float(dolum) - float(o["canli_dolum"])) < 1e-9
            and abs(fark - o["fark_bps"]) < 1e-6)))
    tamam += ok
    print(f"{tk} {gun} f={f} dal={dal} L={L} t0={ns_et(seans[i0][0]).strftime('%H:%M:%S')} p0={seans[i0][1]} dolum={dolum} "
          f"fark={None if fark is None else round(fark, 3)} | betik f={o['olcek_f']} dal={o['dal']} dolum={o['canli_dolum']} "
          f"fark={None if o['fark_bps'] is None else round(o['fark_bps'], 3)} sinif={o['sinif']} -> {'UYUSUYOR' if ok else 'AYRISIYOR'}")
print(f"PK-2: {tamam}/{len(ornek)} uyuşuyor")
