"""KALEM 1 — BULGU-1 (hayalet-satır hacim-şartı kaçağı) BAĞIMSIZ TEYİDİ.

Ölçüm değil TEYİT: hipotez yok, eşik yok, K'ya sayılmaz. Yapılan iş, halihazırda sevk edilmiş
bir kapının (data._unadjusted_mask / data.sanitize_bars) BULGU-1'de adı geçen satırları
gerçekten yakaladığını, ESKİ kuralı yeniden inşa edip yan yana koyarak kanıtlamak.

SALT-OKUNUR: yerel bar arşivi (state/bars/*.csv) pandas ile OKUNUR; MERIDIAN_ROOT kum havuzuna
alınır, böylece obs.warn/store yazımları üretim state'ine DEĞİL kum havuzuna düşer.
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
from meridian import config  # noqa: E402

LIVE_BARS = Path("/Users/erdemozturk/AI-Trading/state/bars")

# BULGU-1'in adını verdiği vakalar (MERIDIAN_ENGINEERING_LOG.md:527 + data.py:317)
VAKALAR = [("GILD", "2013-12-18"), ("CMCSA", "2013-12-18"),
           ("DLTR", "2012-06-26"), ("UNP", "2014-06-06")]


def esk_kural(df: pd.DataFrame) -> pd.Series:
    """2026-07-30 ÖNCESİ kural — hacim şartı VETO: spike & revert & TERS-ORANLI hacim.
    (data.py:333 "eski (c) hacim TAM TERS oranlı olmalı" — yeniden inşa.)"""
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


def oku(t: str) -> pd.DataFrame:
    p = LIVE_BARS / f"{t.lower()}.csv"
    df = pd.read_csv(p)
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    return df.sort_values("date").reset_index(drop=True)


def satir(df: pd.DataFrame, tarih: str) -> dict | None:
    m = df[df["date"] == tarih]
    return None if m.empty else m.iloc[0].to_dict()


def kanit(df: pd.DataFrame, i: int) -> dict:
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    r = float(c.iloc[i] / c.iloc[i - 1])
    back = float(c.iloc[i + 1] / c.iloc[i]) if i + 1 < len(df) else float("nan")
    drr = abs(r * back - 1.0)
    med = float(v.iloc[max(0, i - data.UNADJ_VOL_WINDOW):i].median())
    return {"r": round(r, 4), "back": round(back, 4), "drr": round(drr, 4),
            "kademe": ("1_strict" if drr < data.UNADJ_STRICT_REVERT_TOL else
                       ("2_revert" if drr < data.UNADJ_REVERT_TOL else "yok")),
            "hacim": float(v.iloc[i]), "onceki_hacim": float(v.iloc[i - 1]),
            "hacim_oran": round(float(v.iloc[i] / v.iloc[i - 1]), 4) if v.iloc[i - 1] else None,
            "recip_|r*vr-1|": round(abs(r * float(v.iloc[i] / v.iloc[i - 1]) - 1.0), 4) if v.iloc[i - 1] else None,
            "medyan_hacim_63": round(med, 1),
            "surge_oran": round(float(v.iloc[i]) / med, 3) if med else None,
            "dolar_hacim": round(float(c.iloc[i] * v.iloc[i]), 1)}


def main() -> None:
    sonuc = {"sandbox_state": str(config.STATE), "vakalar": [],
             "kural_sabitleri": {k: getattr(data, k) for k in
                                 ("SPLIT_SUSPECT_RET", "UNADJ_REVERT_TOL", "UNADJ_STRICT_REVERT_TOL",
                                  "UNADJ_VOLUME_TOL", "UNADJ_VOL_SURGE_MIN", "UNADJ_VOL_WINDOW",
                                  "UNADJ_DOLLAR_VOL_FLOOR")},
             "takvim_yuklendi": None}
    for t, tarih in VAKALAR:
        df = oku(t)
        ham = satir(df, tarih)
        rec: dict = {"ticker": t, "tarih": tarih, "diskte_var": ham is not None,
                     "ham_satir": {k: (round(float(v), 4) if isinstance(v, (int, float)) else v)
                                   for k, v in (ham or {}).items()},
                     "defter_bar": int(len(df))}
        if ham is not None:
            i = int(df.index[df["date"] == tarih][0])
            rec["komsular"] = df.iloc[max(0, i - 2):i + 3].to_dict("records")
            rec["olculen"] = kanit(df, i)
        # YENİ kural (canlı kod)
        yeni = data._unadjusted_mask(df)
        eski = esk_kural(df)
        rec["yeni_kural_yakaladi"] = bool(ham is not None and yeni.iloc[i])
        rec["eski_kural_yakaladi"] = bool(ham is not None and eski.iloc[i])
        rec["yeni_kural_toplam_satir"] = int(yeni.sum())
        rec["eski_kural_toplam_satir"] = int(eski.sum())
        rec["yeni_kural_tarihler"] = sorted(df.loc[yeni.values, "date"].tolist())
        rec["eski_kural_tarihler"] = sorted(df.loc[eski.values, "date"].tolist())
        # TAM KAPI (sanitize_bars) — üretim yolunun kendisi
        temiz, rapor = data.sanitize_bars(df.copy(), t)
        rec["sanitize_rapor"] = {k: int(v) for k, v in rapor.items()}
        rec["kapi_sonrasi_satir_var_mi"] = bool((temiz["date"] == tarih).any())
        rec["kapi_hukmu"] = ("KARANTİNA" if not (temiz["date"] == tarih).any() and ham is not None
                             else ("GEÇTİ" if ham is not None else "SATIR YOK"))
        # defterle karışmasın: bu tarih bars_integrity DÖNEM dışlamasına giriyor mu?
        rec["bars_integrity_safe_start"] = data.safe_start(t)
        sonuc["vakalar"].append(rec)
    sonuc["takvim_yuklendi"] = bool(data._sessions())
    sonuc["ghost_report"] = data.ghost_report()
    print(json.dumps(sonuc, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
