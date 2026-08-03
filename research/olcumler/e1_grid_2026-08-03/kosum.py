"""EXE-2026-001 E1 İCRA GRID'İ — tek KOL koşar, sonucu JSON'a yazar. Kol adı argv[1].

KAYNAK HARNESS: research/olcumler/karne_tazeleme_2026-08-03/kosum.py (o da karne_olcum'un
betiğidir) — R1 geometrisi, imza/digest tanımları, defter alanları AYNEN. EKLENENLER (yalnız
ÖLÇÜM yüzeyi, motor davranışına dokunmaz):
  * `entry_law` + `entry_rejects` (motorun KENDİ sayacı) + dolum/dolmama oranı (plan-bazlı)
  * `gap_gozlemi`: `fill_entry`e geçen `gap_at_submit` argümanının dağılımı — `cancel` grid
    noktasının replay yolunda BAĞLAYIP BAĞLAMADIĞI iddia değil ÖLÇÜM olsun diye
  * `kotumser`: E3 bandının ikiz sütunu — üretim fonksiyonlarıyla (`analytics.pessimistic_band`,
    `analytics._kotumser_ek_dolar`) aynı defter üzerinde
  * `kacan_dolum`: dolmayan planların hipotetik KOŞULSUZ-AÇILIŞ getirisi (betimleyici; ham
    barlardan ileri-getiri, ikinci bir icra/çıkış modeli KURULMADI)

MOTOR KOPYALANDI, YAMALANMADI (kod_damgasi.json). KOLLAR ARASI TEK FARK `state_<kol>/goal.yaml`
`execution_v2` bloğudur.

SALT-ÖLÇÜM: her kol kendi state_<kol>/ dizinine yazar; barlar canlı önbellekten SEMBOLİK BAĞ ile
SALT-OKUNUR okunur (load_cached ağa çıkmaz, CSV yeniden yazmaz).
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
sc, data_adapter, an = kk.sc, kk.data_adapter, kk.an

assert str(kk.MOTOR).startswith(str(SANDBOX / "meridian")), f"YANLIŞ MOTOR: {kk.MOTOR}"

# --- R1 GEOMETRİSİ: karne_tazeleme / karne_olcum / r1_baseline ile BİREBİR AYNI ----------------
GEOM = dict(is_start="2022-01-01", oos_start="2024-01-01", oos_end="2026-04-30",
            holdout_end="2026-07-30",
            folds=["2024-01-01", "2024-10-01", "2025-07-01", "2026-04-30"])
EMBARGO = 10
UFUKLAR = (5, 10, 20)          # kaçan-dolum ileri-getiri ufukları (seans)

ISLEM_ALAN = ("ticker", "ts_open", "ts_close", "entry", "exit", "r_multiple", "size_r",
              "exit_reason", "setup", "regime_at_plan", "pnl_dollars", "pnl_pct", "costs",
              "bars_held", "qty", "plan_id", "id", "score", "regime", "mfe_r", "mae_r",
              "scaled_out", "strategy_version")

PLAN_ALAN = ("id", "date", "ticker", "score", "setup", "sector", "gate_verdict", "gate_reasons",
             "entry_trigger", "stop", "size_r", "regime_at_plan", "r_multiple_expected",
             "strategy_version")


def trade_digest(trades: list) -> str:
    """karne_olcum / karne_tazeleme ile BİREBİR AYNI TANIM — kıyas ancak böyle meşrudur."""
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


def _ozet(xs: list) -> dict:
    if not xs:
        return {"olculdu": False, "neden": "örneklem yok", "n": 0}
    s = sorted(xs)
    return {"olculdu": True, "n": len(s), "ort": round(sum(s) / len(s), 4),
            "medyan": round(s[len(s) // 2], 4), "toplam": round(sum(s), 4),
            "min": round(s[0], 4), "maks": round(s[-1], 4),
            "poz_oran": round(sum(1 for x in s if x > 0) / len(s), 4)}


def kacan_dolum_getirisi(bars: dict, cagrilar: list) -> dict:
    """DOLMAYAN planların hipotetik KOŞULSUZ-AÇILIŞ getirisi — BETİMLEYİCİ.

    Ne YAPILIR: dolum çağrısının o günkü AÇILIŞINDAN (motorun `next_open`u, yani limitsiz motorun
    ödeyeceği fiyat) h seans sonraki KAPANIŞA ham getiri; ve planın kendi stop mesafesiyle
    R-benzeri = (kapanış_h − açılış) / (açılış − stop).
    Ne YAPILMAZ: çıkış mantığı simüle EDİLMEZ (trail/breakeven/chandelier/giveback/regime_flip/
    scale_out yok), friksiyon düşülmez, portföy slotu/ısı/eş-anlı pozisyon kısıtı UYGULANMAZ.
    Yani bu bir "kaçan kâr" defteri DEĞİL, kaçan planların sonradan ne yaptığının betimidir.
    Veri sonu ufka yetmiyorsa satır `olculemedi` sayılır (uydurma yok)."""
    idx = {t: df.set_index("date") for t, df in bars.items()}
    satirlar, olculemedi = [], 0
    for c in cagrilar:
        if c["sonuc"] == "dolu":
            continue
        t = c["ticker"]
        df = idx.get(t)
        if df is None:
            olculemedi += 1
            continue
        d = pd.Timestamp(c["date"])
        if d not in df.index:
            olculemedi += 1
            continue
        i = int(df.index.get_loc(d))
        o = float(df["open"].iloc[i])
        stop = c.get("stop")
        risk = (o - float(stop)) if (stop is not None and o > float(stop)) else None
        row = {"date": c["date"], "ticker": t, "sonuc": c["sonuc"], "acilis": round(o, 4),
               "stop": stop, "risk_hisse": (round(risk, 4) if risk else None)}
        eksik = False
        for h in UFUKLAR:
            j = i + h
            if j >= len(df):
                row[f"ret_{h}"] = None
                row[f"r_{h}"] = None
                eksik = True
                continue
            cl = float(df["close"].iloc[j])
            row[f"ret_{h}"] = round(cl / o - 1.0, 6)
            row[f"r_{h}"] = (round((cl - o) / risk, 4) if risk else None)
        if eksik:
            olculemedi += 1
        satirlar.append(row)

    def coll(anahtar, sadece=None):
        return [s[anahtar] for s in satirlar if s.get(anahtar) is not None
                and (sadece is None or s["sonuc"] == sadece)]

    out = {"n_dolmayan": len(satirlar), "n_ufuk_eksik": olculemedi,
           "ufuklar": list(UFUKLAR),
           "yontem": ("hipotetik koşulsuz-açılış girişi = o günün AÇILIŞI; h seans sonra KAPANIŞ; "
                      "R-benzeri planın kendi stop mesafesiyle. Çıkış mantığı/friksiyon/portföy "
                      "kısıtı YOK — betimleyici."),
           "tum_dolmayan": {}, "yalniz_entry_missed_limit": {}, "satirlar": satirlar}
    for h in UFUKLAR:
        out["tum_dolmayan"][f"ret_{h}"] = _ozet(coll(f"ret_{h}"))
        out["tum_dolmayan"][f"r_{h}"] = _ozet(coll(f"r_{h}"))
        out["yalniz_entry_missed_limit"][f"ret_{h}"] = _ozet(coll(f"ret_{h}", "entry_missed_limit"))
        out["yalniz_entry_missed_limit"][f"r_{h}"] = _ozet(coll(f"r_{h}", "entry_missed_limit"))
    return out


def main() -> None:
    st = yaml.safe_load((STATE_DIR / "strategy.yaml").read_text())
    params = dict(st["params"])
    by_regime = st.get("params_by_regime") or None
    sv = st.get("version")
    assert isinstance(sv, int), f"strategy.yaml version okunamadı: {sv!r}"
    goal = config.goal()

    kk.kur()
    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    law = backtest.brk.entry_law()
    print(f"[{KOL}] barlar: {len(bars)} sembol, endeks {len(index)} satır, sv={sv}, yasa={law}",
          flush=True)

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

    # --- DOLUM / DOLMAMA (plan-bazlı: fill_entry çağrısına ULAŞAN her plan bir gözlemdir) ---
    cg = kk.fill_cagrilari
    dolan = sum(1 for c in cg if c["sonuc"] == "dolu")
    nedenler: dict[str, int] = {}
    for c in cg:
        if c["sonuc"] != "dolu":
            nedenler[c["sonuc"]] = nedenler.get(c["sonuc"], 0) + 1
    dolum = {
        "cagri_n": len(cg), "dolan_n": dolan, "dolmayan_n": len(cg) - dolan,
        "dolum_orani": (round(dolan / len(cg), 4) if cg else None),
        "dolmama_orani": (round((len(cg) - dolan) / len(cg), 4) if cg else None),
        "dolmama_orani_yalniz_limit": (round(nedenler.get("entry_missed_limit", 0) / len(cg), 4)
                                       if cg else None),
        "ret_nedenleri": nedenler,
        "motorun_kendi_sayaci_entry_rejects": dict(getattr(br, "entry_rejects", {}) or {}),
        "taban_beyani": ("payda = `fill_entry` çağrısına ulaşan plan sayısı (silahlanmış, barı "
                         "olan, slot/kesici/size_mult kapılarını geçmiş plan). Kartın kill#1 "
                         "eşiği (%40) bu paydayla okunur."),
    }

    # --- E3 KÖTÜMSER BAND İKİZ SÜTUNU (üretim fonksiyonları; hükme girmez) ---
    band = an.pessimistic_band(goal)
    ek_tum, n_olc_tum, n_atl_tum = an._kotumser_ek_dolar(tum, band)
    ek_s, n_olc_s, n_atl_s = an._kotumser_ek_dolar(its, band)
    net_tum = round(sum(float(t["pnl_dollars"]) for t in tum
                        if t.get("pnl_dollars") is not None), 2) if tum else None
    net_s = round(sum(float(t["pnl_dollars"]) for t in its
                      if t.get("pnl_dollars") is not None), 2) if its else None
    kotumser = {
        "band": band,
        "tum_replay": {"net": net_tum, "ek_maliyet": ek_tum,
                       "net_kotumser": (None if (net_tum is None or ek_tum is None)
                                        else round(net_tum - ek_tum, 2)),
                       "n_olculen": n_olc_tum, "n_notional_yok": n_atl_tum},
        "search": {"net": net_s, "ek_maliyet": ek_s,
                   "net_kotumser": (None if (net_s is None or ek_s is None)
                                    else round(net_s - ek_s, 2)),
                   "n_olculen": n_olc_s, "n_notional_yok": n_atl_s},
        "hukme_girmez": True,
        "kapsam": "ek maliyet YALNIZ giriş bacağına; rapor yüzeyi, karar değil (goal.yaml E3 notu)",
    }

    out = {
        "kol": KOL,
        "motor": str(kk.MOTOR),
        "motor_tipi": "HEAD_kopyasi_yamasiz",
        "state_dizini": str(STATE_DIR),
        "strategy_version_kaynagi": "state/strategy.yaml:version",
        "strategy_version": sv,
        "params": params, "params_by_regime": by_regime,
        "entry_law": law,
        "goal_execution_v2": (goal or {}).get("execution_v2"),
        "goal_limits": (goal or {}).get("limits"),
        "geometri": GEOM, "embargo": EMBARGO,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": round((dt.datetime.now() - t0).total_seconds(), 1),
        "n_sembol": len(bars), "n_endeks_satir": int(len(index)),
        "calendar_ilk": (str(eqs[0][0]) if eqs else None),
        "calendar_son": (str(eqs[-1][0]) if eqs else None),

        "veri_kapilari": {
            "yukleyici": "dataset.load_cached (ağa çıkmaz, CSV yeniden yazmaz)",
            "bars_integrity_defteri_state_te_var": (STATE_DIR / "bars_integrity.json").exists(),
            "bars_integrity_defter_ozeti": {
                k: (data_adapter.bars_integrity() or {}).get(k)
                for k in ("rev", "sembol_sayisi", "kirilma_sayisi", "dislanan_bar_toplam",
                          "uretildi")},
            "integrity_report": data_adapter.integrity_report(),
        },

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

        "dolum": dolum,
        "gap_gozlemi": dict(kk.gap_gozlemi),
        "kotumser": kotumser,
        "kacan_dolum": kacan_dolum_getirisi(bars, cg),

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

        "_equity": [[str(d), float(v)] for d, v in eqs],
        "_trades_tum": _slim(tum),
        "_trades_search": _slim(its),
        "_trades_confirm": _slim(itc),
        "_plan_log": [{k: p.get(k) for k in PLAN_ALAN} for p in plan_log],
        "_fill_cagrilari": cg,
        "_candidate_log_n": len(br.candidate_log or []),
    }

    (SANDBOX / f"kol_{KOL}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                        default=str))
    print(f"[{KOL}] BİTTİ {out['sure_sn']}sn · oos={out['imza']['oos_score']} "
          f"para={out['imza']['para_search']} n_tum={out['imza']['n_trades_total']} "
          f"dolum={dolan}/{len(cg)} dolmama={dolum['dolmama_orani']} "
          f"net={net_tum} digest={out['imza']['trade_digest_tum'][:12]}", flush=True)


if __name__ == "__main__":
    main()
