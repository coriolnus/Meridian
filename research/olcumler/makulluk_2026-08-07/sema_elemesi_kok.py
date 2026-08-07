"""sema:bar_yok:tarih KÖK ÖLÇÜMÜ — hangi 7 satır, neden düşüyor? (MAKULLÜK bulgusu 2, 2026-08-07)

SALT OKUMA. Bu betik state'e HİÇBİR ŞEY yazmaz:
  * `sieve.Sieve` KULLANILMAZ (yazan taraf o) — eşleştirme döngüsü burada yeniden kurulur;
  * `obs.warn` no-op'a bağlanır (yoksa `measurement_bars` sembol başına events.jsonl'a yazardı);
  * `component_ic()`/`threshold_curve.build()` ÇAĞRILMAZ (ikisi de artefakt yazar).
Amaç ölçmek, üretmek değil: düşen satırların (katman, ticker, tarih) kimliğini ve her birinin
DÜŞME SEBEBİNİ ayrı ayrı adlandırmak.

Çıktı: bulgu.json (yanına RAPOR.md elle yazılır).
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

import pandas as pd  # noqa: E402

from meridian import config, obs, store  # noqa: E402
from meridian import strategy as strat  # noqa: E402
from meridian import component_ic as cic  # noqa: E402
from meridian.adapters import data as data_adapter  # noqa: E402

# --- YAZMA KAPISI: uyarı kanalı diske düşmesin (bu betik ölçer, iz bırakmaz) -------------------
obs.warn = lambda *a, **k: None          # type: ignore[assignment]


def satirlar() -> list[tuple[str, str, str]]:
    """`component_ic._rows()` ile AYNI çıkarım, ama Sieve'siz (o yazıyor)."""
    from meridian import counterfactual as cf
    rows: list[tuple[str, str, str]] = []
    for t in store.read_jsonl("trades.jsonl"):
        pid = str(t.get("plan_id") or "")
        parts = pid.split("-")
        if not pid.startswith("P-") or len(parts) < 5:
            continue
        rows.append(("gercek", parts[4], "-".join(parts[1:4])))
    for r in cf.resolved_rows(entered_only=True):
        if not r.get("ticker") or not r.get("date"):
            continue
        rows.append(("cf", str(r["ticker"]), str(r["date"])[:10]))
    return rows


def evren(measurement: bool) -> dict:
    """`component_ic._load_universe()` ile aynı yol; `measurement=False` bütünlük kırpması OLMADAN
    (iki çerçeveyi kıyaslamak, 'defter mi düşürdü yoksa bar gerçekten yok mu' sorusunu ayırır)."""
    per = {}
    for t in data_adapter.REPLAY_UNIVERSE:
        cp = data_adapter._cache_path(t)
        if not cp.exists():
            continue
        try:
            df, _ = data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
            if measurement:
                df = data_adapter.measurement_bars(df, t)
            if df is not None and len(df) > strat.PIVOT_LOOKBACK + 3:
                per[t] = df.set_index("date").sort_index()
        except Exception as e:                                  # noqa: BLE001
            print(f"  !! {t}: {type(e).__name__}: {e}")
    return per


def main() -> None:
    rows = satirlar()
    per_m = evren(measurement=True)
    per_ham = evren(measurement=False)
    ham_takvim = sorted({d for df in per_ham.values() for d in df.index})
    ham_takvim_set = set(ham_takvim)

    dusen: list[dict] = []
    n_in = 0
    for katman, ticker, dstr in sorted(rows, key=lambda r: (r[0] != "gercek", r[1], r[2])):
        n_in += 1
        frame = per_m.get(ticker)
        if frame is None:
            dusen.append({"katman": katman, "ticker": ticker, "tarih": dstr,
                          "eleme": "sema:bar_yok:sembol"})
            continue
        d = pd.Timestamp(dstr)
        if d in frame.index:
            continue
        # --- DÜŞTÜ: sebebini AYRI AYRI adlandır -------------------------------------------
        ham = per_ham.get(ticker)
        ss = data_adapter.safe_start(ticker)
        kayit = {
            "katman": katman, "ticker": ticker, "tarih": dstr,
            "eleme": "sema:bar_yok:tarih",
            "haftanin_gunu": d.day_name(),
            "ham_barda_var": bool(ham is not None and d in ham.index),
            "guvenli_baslangic": ss,
            "butunluk_kirpmasi_dusurdu": bool(ss and dstr < ss),
            "sembolun_ilk_bari": (str(frame.index.min().date()) if len(frame.index) else None),
            "sembolun_son_bari": (str(frame.index.max().date()) if len(frame.index) else None),
            "tarih_evrenin_takviminde": d in ham_takvim_set,
            "kac_sembolde_bu_tarih_var": sum(1 for df in per_ham.values() if d in df.index),
            "onceki_bar": None, "sonraki_bar": None,
        }
        if len(frame.index):
            onc = frame.index[frame.index < d]
            son = frame.index[frame.index > d]
            kayit["onceki_bar"] = str(onc.max().date()) if len(onc) else None
            kayit["sonraki_bar"] = str(son.min().date()) if len(son) else None
        dusen.append(kayit)

    tarih_dusen = [x for x in dusen if x["eleme"] == "sema:bar_yok:tarih"]
    out = {
        "olculen": "component_ic.eslesme eşleştirme döngüsü (threshold_curve.eslesme AYNI çerçeve: "
                   "cic._load_universe + aynı (ticker,tarih) satırları → aynı düşme kümesi)",
        "n_in": n_in,
        "n_dusen_toplam": len(dusen),
        "n_bar_yok_tarih": len(tarih_dusen),
        "n_bar_yok_sembol": len(dusen) - len(tarih_dusen),
        "evren_sembol_sayisi": {"olcum": len(per_m), "ham": len(per_ham)},
        "evren_takvimi": {"ilk": str(ham_takvim[0].date()) if ham_takvim else None,
                          "son": str(ham_takvim[-1].date()) if ham_takvim else None,
                          "seans": len(ham_takvim)},
        "dusenler": dusen,
    }
    p = pathlib.Path(__file__).with_name("bulgu.json")
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != "dusenler"}, indent=2, ensure_ascii=False))
    for x in dusen:
        print(json.dumps(x, ensure_ascii=False))
    print(f"\n→ {p}")
    print(f"state yazımı: YOK (obs.warn no-op, Sieve kullanılmadı) · config.STATE={config.STATE}")


if __name__ == "__main__":
    main()
