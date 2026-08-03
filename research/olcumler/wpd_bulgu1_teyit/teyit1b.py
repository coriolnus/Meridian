"""KALEM 1 ek — SINIF GENİŞLİĞİ: BULGU-1'in %29/%77 sayısını yerel arşivde bağımsız yeniden üret.

Tüm state/bars/*.csv üzerinde, TAKVİM KAPISI UYGULANDIKTAN SONRA (hayalet-seans satırları
düştükten sonra — BULGU-1 ölçümü "geçerli-seans satırı" üzerindeydi):
  (a)      |r−1| > SPLIT_SUSPECT_RET            → aday havuzu
  (a&b)    + geri-dönüş (drr < UNADJ_REVERT_TOL) → gerçek tek-satır hayalet sınıfı
  (a&b&c_ESKİ) hacim TERS-ORANLI (ya da 0)      → ESKİ kuralın karantinaya aldığı
  YENİ     data._unadjusted_mask                → bugünkü kuralın karantinaya aldığı
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SB = Path(__file__).resolve().parent
os.environ["MERIDIAN_ROOT"] = str(SB)
os.environ.setdefault("MERIDIAN_MODE", "paper")
sys.path.insert(0, "/Users/erdemozturk/AI-Trading")

import pandas as pd  # noqa: E402

from meridian.adapters import data  # noqa: E402

LIVE_BARS = Path("/Users/erdemozturk/AI-Trading/state/bars")


def esk_kural(df: pd.DataFrame) -> pd.Series:
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    prev_c, next_c, prev_v = c.shift(1), c.shift(-1), v.shift(1)
    r = c / prev_c.where(prev_c > 0)
    back = next_c / c.where(c > 0)
    spike = (r - 1.0).abs() > data.SPLIT_SUSPECT_RET
    revert = (r * back - 1.0).abs() < data.UNADJ_REVERT_TOL
    zero_vol = v.fillna(-1) == 0
    recip = ((r * (v / prev_v.where(prev_v > 0))) - 1.0).abs() < data.UNADJ_VOLUME_TOL
    return (spike & revert & (zero_vol | recip)).fillna(False)


def parcala(df: pd.DataFrame) -> dict:
    c = pd.to_numeric(df["close"], errors="coerce")
    prev_c, next_c = c.shift(1), c.shift(-1)
    r = c / prev_c.where(prev_c > 0)
    back = next_c / c.where(c > 0)
    spike = ((r - 1.0).abs() > data.SPLIT_SUSPECT_RET).fillna(False)
    revert = ((r * back - 1.0).abs() < data.UNADJ_REVERT_TOL).fillna(False)
    return {"a": spike, "ab": spike & revert, "drr": (r * back - 1.0).abs(), "r": r}


def main() -> None:
    files = sorted(LIVE_BARS.glob("*.csv"))
    tot = {"defter": 0, "satir_ham": 0, "satir_gecerli_seans": 0,
           "a": 0, "ab": 0, "eski": 0, "yeni": 0}
    ab_satirlar, yeni_ekstra, eski_ozel = [], [], []
    for p in files:
        t = p.stem.upper()
        df = pd.read_csv(p)
        if df.empty or "close" not in df:
            continue
        df["date"] = df["date"].astype(str).str.slice(0, 10)
        df = df.sort_values("date").reset_index(drop=True)
        tot["defter"] += 1
        tot["satir_ham"] += len(df)
        gh = data._ghost_mask(df)
        df = df.loc[~gh].reset_index(drop=True) if gh.any() else df
        tot["satir_gecerli_seans"] += len(df)
        pz = parcala(df)
        eski, yeni = esk_kural(df), data._unadjusted_mask(df)
        tot["a"] += int(pz["a"].sum()); tot["ab"] += int(pz["ab"].sum())
        tot["eski"] += int(eski.sum()); tot["yeni"] += int(yeni.sum())
        for i in df.index[pz["ab"].values]:
            ab_satirlar.append({"t": t, "tarih": df.at[i, "date"], "r": round(float(pz["r"].iloc[i]), 4),
                                "drr": round(float(pz["drr"].iloc[i]), 4),
                                "eski": bool(eski.iloc[i]), "yeni": bool(yeni.iloc[i])})
        for i in df.index[(yeni & ~eski).values]:
            yeni_ekstra.append({"t": t, "tarih": df.at[i, "date"], "r": round(float(pz["r"].iloc[i]), 4),
                                "drr": round(float(pz["drr"].iloc[i]), 4)})
        for i in df.index[(eski & ~yeni).values]:
            eski_ozel.append({"t": t, "tarih": df.at[i, "date"], "r": round(float(pz["r"].iloc[i]), 4)})
    kacan_eski = [x for x in ab_satirlar if not x["eski"]]
    kacan_yeni = [x for x in ab_satirlar if not x["yeni"]]
    out = {"toplam": tot,
           "eski_kuralin_kacirdigi_ab": len(kacan_eski),
           "eski_kacak_pay_pct": round(100 * len(kacan_eski) / max(len(ab_satirlar), 1), 1),
           "yeni_kuralin_kacirdigi_ab": len(kacan_yeni),
           "yeni_kacak_pay_pct": round(100 * len(kacan_yeni) / max(len(ab_satirlar), 1), 1),
           "ab_satirlar": sorted(ab_satirlar, key=lambda x: (x["t"], x["tarih"])),
           "yeni_yakalayip_eski_kaciran": sorted(yeni_ekstra, key=lambda x: (x["t"], x["tarih"])),
           "eski_yakalayip_yeni_kaciran": eski_ozel}
    print("###JSON###")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
