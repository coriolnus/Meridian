"""KALEM 2 — bars_integrity güvensiz-dönem dışlamasının BAĞIMSIZ TEYİDİ (salt-okunur).

Kanonik tüketici yolunu (`sanitize_bars` → `measurement_bars`, component_ic._load_universe ile
BİREBİR aynı çağrı sırası) tüm evren üzerinde koşturur ve `integrity_report()` sayacını okur.
Ayrıca üç davranış iddiasını gerçek defterle sınar:
  (1) dikiş-dönemi DIŞLANIR   (2) temiz dönem GEÇER   (3) defterde-kayıt-yok sembol TAM geçer
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

SB = Path(__file__).resolve().parent
os.environ["MERIDIAN_ROOT"] = str(SB)
os.environ.setdefault("MERIDIAN_MODE", "paper")
sys.path.insert(0, "/Users/erdemozturk/AI-Trading")

LIVE = Path("/Users/erdemozturk/AI-Trading/state")
(SB / "state").mkdir(parents=True, exist_ok=True)
shutil.copy2(LIVE / "bars_integrity.json", SB / "state" / "bars_integrity.json")

import pandas as pd  # noqa: E402

from meridian.adapters import data  # noqa: E402

BARS = LIVE / "bars"


def main() -> None:
    led = data.bars_integrity()
    sem = led.get("semboller") or {}
    uni = sorted(set(str(t).upper() for t in data.REPLAY_UNIVERSE))
    say = {"istenen": 0, "dosya_yok": 0, "yuklendi": 0,
           "hayalet_dusen": 0, "karantina_dusen": 0,
           "defter_dislanan_satir": 0, "defter_etkilenen_sembol": 0,
           "defterde_kayit_yok_tam_gecen": 0}
    ayrisan = []
    for t in uni:
        say["istenen"] += 1
        cp = BARS / f"{t.lower()}.csv"
        if not cp.exists():
            say["dosya_yok"] += 1
            continue
        df, rep = data.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
        say["yuklendi"] += 1
        say["hayalet_dusen"] += int(rep.get("ghost_session_dropped") or 0)
        say["karantina_dusen"] += int(rep.get("unadjusted_quarantined") or 0)
        n0 = len(df)
        out = data.measurement_bars(df, t)
        d = n0 - len(out)
        say["defter_dislanan_satir"] += d
        say["defter_etkilenen_sembol"] += int(d > 0)
        if t not in sem:
            say["defterde_kayit_yok_tam_gecen"] += int(d == 0)
            if d:
                ayrisan.append({"t": t, "dusen": d, "not": "defterde KAYIT YOK ama satır düştü (İHLAL)"})
        else:
            beklenen = int(sem[t].get("dislanan_bar") or 0)
            # defterdeki sayı HAM defter üzerinden üretildi; sanitize sonrası küçük fark olabilir
            if abs(beklenen - d) > 3:
                ayrisan.append({"t": t, "defterdeki": beklenen, "olculen": d,
                                "not": "defter ile ölçüm AYRIŞTI (>3 satır)"})
            # (2) temiz dönem GEÇER: güvenli başlangıçtan ÖNCE satır kalmamalı, SONRAsı tam kalmalı
            ss = sem[t].get("guvenli_baslangic")
            if ss is not None and len(out):
                if str(out["date"].astype(str).str.slice(0, 10).min()) < ss:
                    ayrisan.append({"t": t, "not": f"güvenli başlangıç {ss} ÖNCESİ satır kaldı (İHLAL)"})

    rapor = data.integrity_report()
    out = {"defter": {"rev": led.get("rev"), "uretildi": led.get("uretildi"),
                      "sembol_sayisi": led.get("sembol_sayisi"),
                      "kirilma_sayisi": led.get("kirilma_sayisi"),
                      "dislanan_bar_toplam": led.get("dislanan_bar_toplam"),
                      "kural": led.get("kural")},
           "evren": len(uni), "sayaclar": say,
           "integrity_report": {k: v for k, v in rapor.items() if k != "applied"},
           "integrity_report_applied_ilk10": dict(list(sorted(rapor["applied"].items(),
                                                              key=lambda kv: -kv[1]))[:10]),
           "ayrisan": ayrisan}
    print("###JSON###")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
