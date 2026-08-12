"""EDG-036 AŞAMA-1 EK ÖLÇÜM: shadowlaw kayma bekçisi + sieve ihlal dedektörü + rollback girdileri.
Yerel sandbox; hiçbir canlı yola dokunulmaz. `check_and_rollback` ÇAĞRILMAZ (yazar) — girdileri
AYNI kod yollarından yeniden okunur ve `_would_have`ten ÖNCEKİ karar noktası raporlanır."""
import importlib
import json
import sys
import traceback
from pathlib import Path

REPO = Path("/Users/erdemozturk/AI-Trading")
SB = Path(sys.argv[1])
OUT = Path(sys.argv[2])
sys.path.insert(0, str(REPO))
import os
os.environ["MERIDIAN_DB"] = "off"

res = {}
for w in ("a", "b"):
    d = SB / w
    from meridian import config
    config.STATE = d
    config.BARS = d / "bars"
    config.HISTORY = d / "history"
    import meridian.store as store
    import meridian.storage as storage
    for m in (store, storage):
        importlib.reload(m)
    from meridian import shadowlaw, sieve, versioning, rollback, score as score_mod
    for m in (shadowlaw, sieve, versioning, rollback):
        importlib.reload(m)
    o = {}
    tr = store.read_jsonl("trades.jsonl")
    goal = config.goal()

    # (1) SHADOWLAW KAYMA BEKÇİSİ — kanonik n_boot/seed (2000/42)
    try:
        dr = shadowlaw.variance_drift(tr, goal)
        o["shadowlaw_variance_drift"] = {
            "olculdu": dr["olculdu"], "kayma": dr["kayma"],
            "kayitli_n_trades": dr.get("kayitli_n_trades"),
            "yururlukteki_MONEY_GATE_MARGIN": shadowlaw.MONEY_GATE_MARGIN,
            "yururlukteki_DD_VETO_MARGIN": shadowlaw.DD_VETO_MARGIN,
            "olcum_ozet": {k: (dr.get("olcum") or {}).get(k)
                           for k in ("margin_scale", "sd_dusus", "ort_dusus",
                                     "dd_veto_gurultunun_disinda", "para_payi_tek_terim",
                                     "n_trades", "n_blocks", "block_days")}}
    except Exception as e:
        o["shadowlaw_variance_drift"] = {"_olculemedi": f"{type(e).__name__}: {e}",
                                         "_iz": traceback.format_exc().splitlines()[-3:]}

    # (2) SIEVE İHLAL DEDEKTÖRÜ — şema elemesi eşiği aşıyor mu?
    try:
        rp = sieve.report()
        o["sieve_report"] = {"ok": sieve.ok(), "violations": rp.get("violations"),
                             "stages": {k: {"in": v.get("in"), "out": v.get("out"),
                                            "drops": v.get("drops")}
                                        for k, v in (rp.get("stages") or {}).items()},
                             "esik": {"SEMA_ESCALATE_FRAC": sieve.SEMA_ESCALATE_FRAC,
                                      "SEMA_ESCALATE_MIN_N": sieve.SEMA_ESCALATE_MIN_N}}
    except Exception as e:
        o["sieve_report"] = {"_olculemedi": f"{type(e).__name__}: {e}"}

    # (3) ROLLBACK GİRDİLERİ (karar noktasına KADAR — _would_have ÇAĞRILMAZ)
    try:
        st = config.load_strategy()
        v, par = int(st.get("version", 1)), st.get("parent")
        ereg = rollback._ship_eval_regime(v)
        trs = [t for t in tr if str(t.get("regime")) == ereg] if ereg else tr
        cur = [t for t in trs if t.get("strategy_version") == v]
        pr = [t for t in trs if t.get("strategy_version") == par]
        ms = int(goal["min_sample"])
        sbv = versioning.scoreboard().get("versions", {}).get(str(par), {})
        cur_score = score_mod.score(cur, goal) if len(cur) >= ms else None
        par_score = score_mod.score(pr, goal) if len(pr) >= ms else None
        yol = "islemlerden"
        if par_score is None and not ereg:
            par_score = sbv.get("live_score", sbv.get("backtest_oos"))
            yol = "scoreboard.live_score|backtest_oos"
        par_score2 = rollback._parent_score_fallback(v, par_score)
        if par_score2 != par_score:
            yol = "shipping_gate_incumbent_oos (_parent_score_fallback)"
        o["rollback_girdileri"] = {
            "version": v, "parent": par, "ship_eval_regime": ereg, "min_sample": ms,
            "n_cur": len(cur), "n_parent": len(pr),
            "erken_return_None": len(cur) < ms,
            "cur_score": cur_score, "par_score_ham": par_score, "par_score": par_score2,
            "par_score_yolu": yol,
            "scoreboard_parent_kaydi": sbv,
            "scoreboard_parent_anahtarlari": sorted(sbv.keys()),
            "rollback_if_worse_by": goal.get("rollback_if_worse_by"),
            "ham_delta": (None if (cur_score is None or par_score2 is None)
                          else round(cur_score - par_score2, 4)),
            "ham_delta_esigi_asiyor": (None if (cur_score is None or par_score2 is None) else
                                       bool((cur_score - par_score2)
                                            < -float(goal["rollback_if_worse_by"]))),
            "not": ("nihai karar `_karar_girdisi` (would_have replay'i) ile verilir — o replay "
                    "bar tabanı ister ve BURADA KOŞULMADI; rapor karar noktasına KADARki girdilerdir")}
    except Exception as e:
        o["rollback_girdileri"] = {"_olculemedi": f"{type(e).__name__}: {e}",
                                   "_iz": traceback.format_exc().splitlines()[-3:]}
    res[f"dunya_{w.upper()}"] = o

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
print("[edg036b] yazıldı", OUT)
