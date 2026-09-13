#!/usr/bin/env python3
"""EDG-2026-089 K1/K2 SAYIMI — retain kadansı (K1) + otomatik zihin-modeli tazelemesi (K2) günlük tablo.

A1'de SALT-OKUR koşar (ssh stdin ile: `ssh a1 python3 - --events /opt/meridian/state/events.jsonl < sayim.py`);
`meridian`ı İTHAL ETMEZ (obs'a ulaşmaz), hiçbir dosya yazmaz, stdout'a JSON basar. Hüküm Rol-1'in (kart
`basari_tanimi`): K1 = pencere günlerinin her birinde `defter_ozeti_retain` olayı sonuc∈{retain, zaten_var} ∧
memory_units artışı; K2 = `refresh_mental_model` async işlemi completed olan gün sayısı ≥5/7. Sayı uydurulmaz:
psql erişilemezse alan None + neden.

Kaynaklar: `state/events.jsonl` (olay `defter_ozeti_retain`, alanlar gun/sonuc/items — ops/defter_ozeti_retain.py),
Postgres `hindsight.async_operations` (operation_type/status/created_at) + `memory_units` (count) — `sudo -u postgres psql`.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, json, subprocess, sys

def olaylar(yol: str, baslangic: str) -> dict:
    gunler: dict[str, list] = collections.defaultdict(list)
    bozuk = 0
    with open(yol, encoding="utf-8") as fh:
        for satir in fh:
            if '"defter_ozeti_retain"' not in satir:
                continue
            try:
                r = json.loads(satir)
            except json.JSONDecodeError:
                bozuk += 1; continue
            if r.get("event") != "defter_ozeti_retain":
                continue
            ts = str(r.get("ts") or "")
            if ts[:10] < baslangic:
                continue
            gunler[ts[:10]].append({"ts": ts[:19], "sonuc": r.get("sonuc"), "items": r.get("items"),
                                    "gun": r.get("gun")})
    return {"gunler": dict(sorted(gunler.items())), "bozuk_satir": bozuk}

def psql(sql: str) -> list[str] | None:
    try:
        p = subprocess.run(["sudo", "-u", "postgres", "psql", "-d", "hindsight", "-At", "-c", sql],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None
    if p.returncode != 0:
        return None
    return [s for s in p.stdout.splitlines() if s.strip()]

def main(argv):
    a = argparse.ArgumentParser()
    a.add_argument("--events", default="/opt/meridian/state/events.jsonl")
    a.add_argument("--baslangic", default="2026-09-13", help="pencere ilk günü (UTC)")
    a.add_argument("--gun-n", type=int, default=7)
    args = a.parse_args(argv)
    ev = olaylar(args.events, args.baslangic)
    tazeleme = psql("select to_char(created_at at time zone 'UTC','YYYY-MM-DD'), status, count(*) "
                    "from async_operations where operation_type='refresh_mental_model' "
                    f"and created_at >= '{args.baslangic}' group by 1,2 order by 1,2")
    mu = psql("select count(*) from memory_units")
    k2: dict[str, dict] = collections.defaultdict(dict)
    if tazeleme is not None:
        for s in tazeleme:
            gun, durum, n = s.split("|")
            k2[gun][durum] = int(n)
    pencere = [(dt.date.fromisoformat(args.baslangic) + dt.timedelta(days=i)).isoformat() for i in range(args.gun_n)]
    bugun = dt.datetime.now(dt.timezone.utc).date().isoformat()
    tablo = []
    for g in pencere:
        e = ev["gunler"].get(g, [])
        sonuclar = [x["sonuc"] for x in e]
        tablo.append({"gun": g, "gecti_mi_takvim": g <= bugun,
                      "k1_retain_olay_n": len(e), "k1_sonuclar": sonuclar,
                      "k1_gun_dolu": any(s in ("retain", "zaten_var") for s in sonuclar) if g <= bugun else None,
                      "k2_tazeleme": (k2.get(g) if tazeleme is not None else None),
                      "k2_gun_dolu": ((k2.get(g, {}).get("completed", 0) >= 1) if (tazeleme is not None and g <= bugun) else None)})
    gecen = [t for t in tablo if t["gecti_mi_takvim"]]
    out = {"kart": "EDG-2026-089", "uretim_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "pencere": pencere, "tablo": tablo,
           "k1_dolu_gun": sum(1 for t in gecen if t["k1_gun_dolu"]), "k1_gecen_gun": len(gecen),
           "k2_dolu_gun": (sum(1 for t in gecen if t["k2_gun_dolu"]) if tazeleme is not None else None),
           "k2_neden": (None if tazeleme is not None else "psql erişilemedi (sudo/postgres) — K2 ölçülemedi"),
           "memory_units": (int(mu[0]) if mu else None),
           "memory_units_neden": (None if mu else "psql erişilemedi"),
           "events_bozuk_satir": ev["bozuk_satir"],
           "hukum": None, "hukum_notu": "hüküm Rol-1'in — 2026-09-20'de kart basari_tanimi ile; bu tablo sayımdır"}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1); print()

if __name__ == "__main__":
    main(sys.argv[1:])
