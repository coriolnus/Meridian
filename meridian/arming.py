"""arming.py — Silahlanma Değerlendiricisi (#3): uyuyan→ölç→silahla döngüsünün eksik son halkası.

Uyuyan kurulumlar (momentum_burst, episodic_pivot) karşı-olgusal defterde ileriye dönük ölçülür; bu
modül o kanıt YAZILI eşiği geçtiğinde KAPI ölçÜMÜNÜ otomatik koşar: incumbent (mevcut silahlı set)
vs aday (aynı parametreler + kurulum silahlı) üretim pencerelerinde walk edilir ve karar TAMAMEN
mevcut yasaya bırakılır (_gate_eval: blok-bootstrap + K-ceza + fold çoğunluğu + kuyruk vetosu).

SİLAHLANMA OTOMATİK DEĞİLDİR: kapı GEÇSE bile ARMED_SETUPS değişmez — sonuç panele/deftere
"silahlanmaya hazır (P=…)" olarak düşer ve operatör onayı beklenir (canlı davranış değişikliği
bilinçli bir insan kararıdır; momentum_burst emsali). Kapı kalırsa ölçülen sayılar dürüstçe kalır.

Ölçüm kanalı: params["entry.armed_extra"] — scan_entry bu listedeki kurulumları da silahlı sayar;
paramlar üzerinden aktığı için canlı döngüyle YARIŞMAZ (global ARMED_SETUPS'a dokunulmaz)."""
from __future__ import annotations

from . import config, store, obs

REPORT_FILE = "arming_report.json"
MIN_CF_ENTERED = 30        # kapı ölçümünü tetiklemek için kurulum başına en az girilmiş cf kaydı
MIN_CF_AVG_R = 0.0         # ve cf ortalama R'si pozitif olmalı (negatif kanıtla walk yakmayız)


def setup_report() -> dict:
    """Karşı-olgusal defterin kurulum kırılımı: n (girilmiş), kazanma, ort. R, rejim dağılımı.
    Panel + eşik kararı buradan okur; hiçbir karar yetkisi yok."""
    from . import counterfactual as cf
    by: dict[str, dict] = {}
    for r in cf.resolved_rows(entered_only=True):
        s = str(r.get("setup") or "?")
        b = by.setdefault(s, {"n": 0, "wins": 0, "sum_r": 0.0, "regimes": {}})
        b["n"] += 1
        rm = float(r.get("r_multiple") or 0.0)
        b["wins"] += 1 if rm > 0 else 0
        b["sum_r"] += rm
        reg = str(r.get("regime") or "?")
        b["regimes"][reg] = b["regimes"].get(reg, 0) + 1
    return {s: {"n": b["n"], "win_rate": round(b["wins"] / b["n"], 3),
                "avg_r": round(b["sum_r"] / b["n"], 3), "regimes": b["regimes"]}
            for s, b in by.items() if b["n"]}


def _dormant_setups() -> list[str]:
    from . import strategy as strat
    engine = ("breakout_vcp", "momentum_burst", "pullback", "episodic_pivot")
    return [s for s in engine if s not in strat.ARMED_SETUPS]


def evaluate(bars=None, index=None) -> dict:
    """Haftalık değerlendirme: eşiği geçen her uyuyan kurulum için kapı ölçümü. Dönen rapor
    arming_report.json'a yazılır; loop/scheduler dönüşü görmezden gelir (yalnız sinyal)."""
    rep = setup_report()
    out = {"checked_at": store.read_json("heartbeat.json", {}).get("ts"),
           "cf_report": rep, "measurements": {},
           "rule": f"cf n>={MIN_CF_ENTERED} ve ort.R>{MIN_CF_AVG_R} → kapı ölçümü; silahlanma operatör onayı"}
    eligible = [s for s in _dormant_setups()
                if rep.get(s, {}).get("n", 0) >= MIN_CF_ENTERED
                and rep.get(s, {}).get("avg_r", -1) > MIN_CF_AVG_R]
    prev = store.read_json(REPORT_FILE, {})
    for setup in eligible:
        try:
            out["measurements"][setup] = _measure(setup, bars, index)
        except Exception as e:
            out["measurements"][setup] = {"error": f"{type(e).__name__}: {e}"}
    # eşiği geçemeyenlerin durumu da dürüstçe raporda (neden ölçülmedi görünür olsun)
    for setup in _dormant_setups():
        if setup not in out["measurements"]:
            r = rep.get(setup, {})
            out["measurements"][setup] = {"status": "insufficient_cf",
                                          "n": r.get("n", 0), "avg_r": r.get("avg_r")}
    store.write_json(REPORT_FILE, out)
    for setup, m in out["measurements"].items():
        if m.get("status") == "gate_passed" and (prev.get("measurements", {}).get(setup) or {}).get("status") != "gate_passed":
            obs.alarm("ARMING_READY", f"uyuyan kurulum kapıyı GEÇTİ: {setup} — silahlanma operatör onayı bekliyor",
                      setup=setup, p=m.get("search_p"))
    return out


def _measure(setup: str, bars=None, index=None) -> dict:
    """Kapı ölçümü: incumbent vs (+setup silahlı) — üretim pencereleri, mevcut yasa, K=1.
    entry.armed_extra param kanalıyla; global duruma dokunulmaz."""
    from . import reflect, dataset
    from .oos_pipeline import OutOfSamplePipeline
    if bars is None or index is None:
        bars, index = dataset.load(use_cache=True)
    goal = config.goal()
    cur = config.load_strategy()
    params = dict(cur["params"])
    w = reflect._default_windows()
    inc = reflect._wf_cached(params, int(cur.get("version", 1)), bars, index, goal,
                             cur.get("params_by_regime"), windows=w)
    cand_params = {**params, "entry.armed_extra": [setup]}
    cand = reflect.backtest.walk_forward(cand_params, bars, index, goal, w[0], w[1], w[2], w[3],
                                         strategy_version=int(cur.get("version", 1)),
                                         oos_folds=list(w[4]), embargo_days=w[5],
                                         params_by_regime=cur.get("params_by_regime"))
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)
    # ÖLÇÜLEMEDİ ≠ REDDEDİLDİ (denetim turu 7, 2026-07-21 — canlıda yakalandı):
    # momentum_burst raporda "gate_rejected" görünüyordu ama gerekçe "candidate OOS score undefined
    # (below min_sample)" idi; yani kapı ölçüm YAPAMAMIŞTI. Bu, "denedik ve kaybetti" diye okunuyor,
    # kurulumu haksızca gömüyor ve "neden hâlâ uyuyor" sorusunu yanlış cevaplıyordu.
    undefined = (gate.get("incumbent_oos") is None or gate.get("candidate_oos") is None
                 or gate.get("search_p") is None)
    status = "gate_passed" if passes else ("gate_undefined" if undefined else "gate_rejected")
    result = {"status": status,
              "search_p": gate.get("search_p"), "p_required": gate.get("search_p_required"),
              "incumbent_oos": gate.get("incumbent_oos"), "candidate_oos": gate.get("candidate_oos"),
              "fold_wins": gate.get("fold_wins"), "why": why or None}
    if passes:                                              # onay yürüyüşü de aynen (arama iyimserliği kırpılır)
        pipe = OutOfSamplePipeline(goal)
        conf = pipe.confirm(inc, cand)
        result["confirm_p"] = conf.p
        if not conf.passes:
            result["status"] = "gate_rejected_confirmation"
            result["why"] = conf.why
    obs.log("arming_measured", setup=setup, **{k: v for k, v in result.items() if k != "why"})
    return result
