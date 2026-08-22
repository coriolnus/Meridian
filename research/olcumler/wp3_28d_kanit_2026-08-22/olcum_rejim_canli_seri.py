"""WP3/28d KART-KANITI · CANLI barlarla rejim serisi SAYIMI (analiz; kartı Rol-1 yazacak).

Neden ayrı koşum: yerel spy.csv ile canlı spy.csv 2026-07-29'dan itibaren revizyon farklı
(43 alan; hacim dahil) ve canlıda 2026-08-13→2026-08-21 kuyruğu var. Canlı-dünya etiketleri
canlı barlardan hesaplanmalı — üretim fonksiyonunun kendisiyle (regime.classify /
build_regime_json), FETCH_START=2021-01-01 genişleyen dilim.

Çıktı: sonuc_canli_seri.json + gunluk_rejim_canli.csv. UYDURMA YASAĞI: ölçülemeyen null+neden.
"""
from __future__ import annotations
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from meridian import regime as regime_mod          # noqa: E402

COUNT_START = "2022-01-01"
CLAIM_DATE = "2025-07-01"
OUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    ham = json.load(open(OUT_DIR / "canli_spy_2021p.json"))["satirlar"]
    df = pd.DataFrame(ham)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    import yaml
    params = (yaml.safe_load((REPO / "state/strategy.yaml").read_text()).get("params") or {})

    rows = []
    for i in range(len(df)):
        d = df["date"].iloc[i]
        ds = str(d.date())
        if ds < COUNT_START:
            continue
        sl = df.iloc[: i + 1]
        rj = regime_mod.build_regime_json(sl, params, ds)
        rows.append({"date": ds, "regime": rj["regime"], "budget": rj["exposure_budget_pct"],
                     "dd": rj["distribution_days"], "score": rj["exposure_score"]})
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "gunluk_rejim_canli.csv", index=False)

    since = out[out["date"] >= CLAIM_DATE]
    chop = out[out["regime"] == "chop"]
    chop_since = since[since["regime"] == "chop"]
    conf_win = out[(out["date"] >= "2025-08-18") & (out["date"] < "2026-04-30")]  # R1 confirm dilimi

    sonuc = {
        "kart_kaniti": "WP3/28d — CANLI barlarla rejim serisi (hüküm yok)",
        "olcum_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "veri": {"kaynak": "canli_spy_2021p.json (A1 state/bars/spy.csv, ssh salt-okuma)",
                 "son_bar": str(df["date"].max().date()), "gun_sayisi": int(len(out)),
                 "yerel_fark_beyani": "yerel spy.csv ile fark yalnız 2026-07-29 sonrası revizyonlar"},
        "dagilim_toplam": dict(Counter(out["regime"])),
        "dagilim_yil": {y: dict(Counter(g["regime"])) for y, g in out.groupby(out["date"].str[:4])},
        "iddia_penceresi": {
            "pencere": [CLAIM_DATE, str(df["date"].max().date())],
            "gun": int(len(since)), "dagilim": dict(Counter(since["regime"])),
            "chop_gunu": int(len(chop_since)),
            "chop_gunleri": sorted(chop_since["date"].tolist()),
            "girise_acik_chop(budget>0)": int((chop_since["budget"] > 0).sum()),
            "girise_kapali_chop(budget=0)": int((chop_since["budget"] == 0).sum()),
        },
        "son_chop_gunu": (chop["date"].iloc[-1] if len(chop) else None),
        "agustos_2026_etiketleri": out[out["date"] >= "2026-08-01"][
            ["date", "regime", "budget", "dd"]].to_dict(orient="records"),
        "r1_confirm_diliminde": {
            "pencere": ["2025-08-18", "2026-04-30"],
            "gun": int(len(conf_win)), "dagilim": dict(Counter(conf_win["regime"])),
            "chop_gunu": int((conf_win["regime"] == "chop").sum()),
            "girise_acik_chop": int(((conf_win["regime"] == "chop") & (conf_win["budget"] > 0)).sum()),
        },
    }
    (OUT_DIR / "sonuc_canli_seri.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False))
    print(json.dumps({k: sonuc[k] for k in ("iddia_penceresi", "son_chop_gunu",
                                            "agustos_2026_etiketleri", "r1_confirm_diliminde")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
