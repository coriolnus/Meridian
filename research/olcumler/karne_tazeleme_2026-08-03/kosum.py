"""BASE-2026-001 SİSTEM KARNESİ — tek KOL koşar, sonucu JSON'a yazar. Kol adı argv[1].

KOLLAR (kart BASE-2026-001, parameter_grid.kollar):
  tam_guncel            : bugünkü motor (HEAD kopyası) + bugünkü canlı parametreler + CANLI backtest
                          yolunun kullandığı veri kapıları. state'te bars_integrity.json VAR.
  tam_guncel_pk         : tam_guncel'in BİREBİR ikizi — determinizm pozitif kontrolü (kart guards).
  butunluk_dislamasiz   : TEK FARK — state'te bars_integrity.json YOK (dışlama defteri kapalı).
  e1_oncesi_icra        : TEK FARK — goal.yaml `execution_v2.limit_pct_cap` 0.01 → 0.10, yani E1
                          limit tavanı ETKİSİZ (limit = tetik×1.10 > max_chase tavanı tetik×1.04;
                          replay `fill_entry`e atr GEÇİRMEZ, bkz. backtest.py:200). Kalan E1 maddeleri
                          replay'de zaten atıl: gap vetosu `gap_at_submit=None` ile ateşlemez, TIF
                          yalnız aynanın alanıdır. Yani bu kol E1 ÖNCESİ İÇ MOTOR DAVRANIŞIDIR ve
                          iddia ÖLÇÜLÜR: kolun `entry_missed_limit` sayısı SIFIR olmalı.

MOTOR KOPYALANDI, YAMALANMADI — kod_damgasi.json HEAD ile bayt eşitliğini gösterir. Defterler
kancalarla toplanır (kosum_kanca.py).

SALT-ÖLÇÜM: her kol kendi state_<kol>/ dizinine yazar; barlar canlı önbellekten SEMBOLİK BAĞ ile
SALT-OKUNUR okunur (load_cached ağa çıkmaz, CSV yeniden yazmaz — canlı worker aynı dosyaları okuyor).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
KOL = sys.argv[1]
STATE_DIR = SANDBOX / f"state_{KOL}"
assert STATE_DIR.is_dir(), f"state dizini yok: {STATE_DIR}"

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ["MERIDIAN_ROOT"] = str(SANDBOX)
sys.path.insert(0, str(SANDBOX))

import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402
import yaml                               # noqa: E402

from meridian import config               # noqa: E402

config.STATE = STATE_DIR
config.HISTORY = config.STATE / "history"
config.BARS = config.STATE / "bars"
config.HISTORY.mkdir(parents=True, exist_ok=True)

import kosum_kanca as kk                  # noqa: E402

backtest, dataset, shadowlaw = kk.backtest, kk.dataset, kk.shadowlaw
sc, data_adapter = kk.sc, kk.data_adapter

assert str(kk.MOTOR).startswith(str(SANDBOX / "meridian")), f"YANLIŞ MOTOR: {kk.MOTOR}"

# --- R1 GEOMETRİSİ: r1_baseline.py ve wpg_olcum/kosum.py ile BİREBİR AYNI ----------------------
GEOM = dict(is_start="2022-01-01", oos_start="2024-01-01", oos_end="2026-04-30",
            holdout_end="2026-07-30",
            folds=["2024-01-01", "2024-10-01", "2025-07-01", "2026-04-30"])
EMBARGO = 10

# İşlem satırının alan kümesi — `pnl_dollars` İÇERİDE (wpg tani_kosum'un (1) numaralı dersi).
ISLEM_ALAN = ("ticker", "ts_open", "ts_close", "entry", "exit", "r_multiple", "size_r",
              "exit_reason", "setup", "regime_at_plan", "pnl_dollars", "pnl_pct", "costs",
              "bars_held", "qty", "plan_id", "id", "score", "regime", "mfe_r", "mae_r",
              "scaled_out", "strategy_version")

PLAN_ALAN = ("id", "date", "ticker", "score", "setup", "sector", "gate_verdict", "gate_reasons",
             "entry_trigger", "stop", "size_r", "regime_at_plan", "r_multiple_expected",
             "strategy_version")


def trade_digest(trades: list) -> str:
    """wpg_olcum/kosum.py ve tani_kosum.py ile BİREBİR AYNI TANIM — kıyas ancak böyle meşrudur."""
    rows = []
    for t in sorted(trades, key=lambda x: (str(x.get("ts_open")), str(x.get("ticker")))):
        rows.append("|".join(str(t.get(k)) for k in
                             ("ticker", "ts_open", "ts_close", "entry", "exit", "r_multiple",
                              "size_r", "exit_reason", "setup")))
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def equity_stats(equity: list, lo: str, hi: str) -> dict:
    if not equity:
        return {"olculdu": False, "neden": "equity eğrisi boş"}
    df = pd.DataFrame(equity, columns=["date", "eq"])
    df = df[(df["date"] >= lo) & (df["date"] < hi)]
    if len(df) < 5:
        return {"olculdu": False, "neden": f"pencerede {len(df)} gün (<5)"}
    eq = df["eq"].astype(float).to_numpy()
    r = np.diff(eq) / eq[:-1]
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq) / peak
    return {"olculdu": True, "n_gun": int(len(df)),
            "eq_ilk": round(float(eq[0]), 2), "eq_son": round(float(eq[-1]), 2),
            "gunluk_vol": round(float(np.std(r, ddof=1)), 6),
            "yillik_vol": round(float(np.std(r, ddof=1) * np.sqrt(252)), 6),
            "gunluk_ort_getiri": round(float(np.mean(r)), 8),
            "mtm_max_dd": round(float(dd.max()), 6),
            "toplam_getiri": round(float(eq[-1] / eq[0] - 1.0), 6)}


def main() -> None:
    st = yaml.safe_load((STATE_DIR / "strategy.yaml").read_text())
    params = dict(st["params"])
    by_regime = st.get("params_by_regime") or None
    # STRATEJİ SÜRÜMÜ CANLI STATE'TEN OKUNUR (kart: "state'ten oku, beyan et") — sabit YAZILMAZ.
    sv = st.get("version")
    assert isinstance(sv, int), f"strategy.yaml version okunamadı: {sv!r}"
    goal = config.goal()

    kk.kur()
    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    print(f"[{KOL}] barlar: {len(bars)} sembol, endeks {len(index)} satır, sv={sv}", flush=True)

    res = backtest.walk_forward(params, bars, index, goal, GEOM["is_start"], GEOM["oos_start"],
                                GEOM["oos_end"], GEOM["holdout_end"], strategy_version=sv,
                                oos_folds=GEOM["folds"], embargo_days=EMBARGO,
                                params_by_regime=by_regime)
    kk.bitir()

    br = kk._replay_res[0]
    assert br is not None, "replay sonucu yakalanamadı — kanca kurulmamış"

    sp = res.get("oos_split") or {}
    s_start, s_end = str(sp.get("search_start"))[:10], str(sp.get("search_end"))[:10]
    span = max(1, (dt.date.fromisoformat(s_end) - dt.date.fromisoformat(s_start)).days)
    its = res.get("_trades_search") or []
    itc = res.get("_trades_confirm") or []
    od = res.get("oos_detail") or {}
    tum = br.trades or []
    eqs = br.equity or []
    plan_log = br.plan_log or []

    def _slim(ts):
        return [{k: t.get(k) for k in ISLEM_ALAN} for t in ts]

    out = {
        "kol": KOL,
        "motor": str(kk.MOTOR),
        "motor_tipi": "HEAD_kopyasi_yamasiz",
        "state_dizini": str(STATE_DIR),
        "strategy_version_kaynagi": "state/strategy.yaml:version",
        "strategy_version": sv,
        "params": params, "params_by_regime": by_regime,
        "entry_law": backtest.brk.entry_law(),
        "goal_execution_v2": (goal or {}).get("execution_v2"),
        "goal_limits": (goal or {}).get("limits"),
        "geometri": GEOM, "embargo": EMBARGO,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": round((dt.datetime.now() - t0).total_seconds(), 1),
        "n_sembol": len(bars), "n_endeks_satir": int(len(index)),
        "calendar_ilk": (str(eqs[0][0]) if eqs else None),
        "calendar_son": (str(eqs[-1][0]) if eqs else None),

        # ---- VERİ KAPISI BEYANI: iddia değil ÖLÇÜM ----
        "veri_kapilari": {
            "yukleyici": "dataset.load_cached (ağa çıkmaz, CSV yeniden yazmaz)",
            "yukleyici_uyguladigi_kapilar": "data.sanitize_bars + data._window (load_cached gövdesi)",
            "bars_integrity_defteri_state_te_var": (STATE_DIR / "bars_integrity.json").exists(),
            "bars_integrity_defter_ozeti": {
                k: (data_adapter.bars_integrity() or {}).get(k)
                for k in ("rev", "sembol_sayisi", "kirilma_sayisi", "dislanan_bar_toplam",
                          "uretildi")},
            # ÖLÇÜM: dışlama bu koşumda gerçekten uygulandı mı? rows_excluded=0 ⇒ backtest yolu
            # `measurement_bars`ı HİÇ çağırmadı (tüketiciler yalnız component_ic + cf_backfill).
            "integrity_report": data_adapter.integrity_report(),
            "ghost_report": (data_adapter.ghost_report()
                             if hasattr(data_adapter, "ghost_report") else
                             {"olculdu": False, "neden": "ghost_report yok"}),
        },

        # ---- İMZA ----
        "imza": {
            "oos_score": res.get("oos_score"),
            "para_search": shadowlaw.money_score(its, goal, span_days=span),
            "n_trades_total": res.get("n_trades_total"),
            "oos_n": od.get("n"), "search_n": len(its), "confirm_n": len(itc),
            "avg_r": od.get("avg_r"), "win_rate": od.get("win_rate"),
            "sharpe": od.get("sharpe"), "max_drawdown": od.get("max_drawdown"),
            "total_return": od.get("total_return"),
            "is_score": res.get("is_score"), "holdout_score": res.get("holdout_score"),
            "trade_digest_search": trade_digest(its),
            "trade_digest_confirm": trade_digest(itc),
            "trade_digest_tum": trade_digest(tum),
            "plan_digest": hashlib.sha256("\n".join(
                f"{p.get('id')}|{p.get('score')}|{p.get('gate_verdict')}"
                for p in plan_log).encode()).hexdigest(),
            "equity_digest": hashlib.sha256("\n".join(
                f"{d}|{v}" for d, v in eqs).encode()).hexdigest(),
        },

        # ---- KARNE ALANLARI (kart success_metric listesi) ----
        "is_detail": res.get("is_detail"),
        "oos_detail": od,
        "holdout_detail": res.get("holdout_detail"),
        "full_detail": res.get("full_detail"),
        "oos_split": {"search_start": s_start, "search_end": s_end, "span_days": span,
                      "confirm_end": GEOM["oos_end"]},
        "para": {
            "search": shadowlaw.money_score(its, goal, span_days=span),
            "search_detail": shadowlaw.money_score_detail(its, goal, span_days=span),
            "confirm_detail": (shadowlaw.money_score_detail(itc, goal, span_days=span)
                               if itc else {"olculdu": False, "neden": "confirm dilimi boş"}),
            "tum_oos_detail": shadowlaw.money_score_detail(its + itc, goal, span_days=span),
        },
        "mtm_dd_veto": res.get("mtm_dd_veto"),
        "search_dd_islem": (round(float(sc.max_drawdown(sc.equity_curve(its))), 6) if its else None),
        "folds": res.get("oos_folds"), "folds_full": res.get("oos_folds_full"),
        "fold_avg_r_mean": res.get("oos_fold_avg_r_mean"),
        "tail_risk": res.get("oos_tail_risk"), "tail_risk_full": res.get("oos_tail_risk_full"),

        "equity_is": equity_stats(eqs, GEOM["is_start"], GEOM["oos_start"]),
        "equity_search": equity_stats(eqs, s_start, s_end),
        "equity_oos": equity_stats(eqs, s_start, GEOM["oos_end"]),
        "equity_holdout": equity_stats(eqs, GEOM["oos_end"], GEOM["holdout_end"]),
        "equity_tam": equity_stats(eqs, GEOM["is_start"], GEOM["holdout_end"]),

        # ---- HAM DEFTERLER (analiz aşaması bunlardan yürür) ----
        "_equity": [[str(d), float(v)] for d, v in eqs],
        "_trades_tum": _slim(tum),
        "_trades_search": _slim(its),
        "_trades_confirm": _slim(itc),
        "_plan_log": [{k: p.get(k) for k in PLAN_ALAN} for p in plan_log],
        "_candidate_log_n": len(br.candidate_log or []),
        "_seanslar": kk.seanslar,
        "_fill_cagrilari": kk.fill_cagrilari,
        "_kapanislar": kk.kapanislar,
        "_acik_kalan_ayna": sorted(kk.acik),
    }

    (SANDBOX / f"kol_{KOL}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                        default=str))
    print(f"[{KOL}] BİTTİ {out['sure_sn']}sn · oos={out['imza']['oos_score']} "
          f"para={out['imza']['para_search']} n_oos={out['imza']['oos_n']} "
          f"n_tum={out['imza']['n_trades_total']} plan={len(plan_log)} "
          f"fill_cagri={len(kk.fill_cagrilari)} digest={out['imza']['trade_digest_tum'][:12]}",
          flush=True)


if __name__ == "__main__":
    main()
