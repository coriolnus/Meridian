"""EDG-2026-036 AŞAMA-1 — KURU KOŞUM (yerel izole sandbox; canlıya HİÇBİR ŞEY yazılmaz).

DÜNYA A = canlı defterin BUGÜNKÜ hâli (95 replay_seed sv=4 + 2 live_paper sv=3)
DÜNYA B = EDG-032 C+mb defteri (885 satır, sha d4033de6…) + AYNI 2 live_paper satırı

DİSİPLİN: UYDURMA YASAĞI. 032 artefaktında OLMAYAN alan None kalır; yalnız kartın aşama-2'de
ADIYLA yazdığı İKİ prosedürel damga basılır (kaynak=replay_seed, strategy_version=5) + `id`
(defter yazarının sayaç ürünü). Bunlar VERİDEN gelmez ve raporda ayrıca beyan edilir.
"""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import traceback
from collections import Counter
from pathlib import Path

REPO = Path("/Users/erdemozturk/AI-Trading")
SB = Path(sys.argv[1])            # sandbox kökü (base/ + a/ + b/ burada)
BASE = SB / "base"
OUT = Path(sys.argv[2])
CMB = REPO / "research/olcumler/edg032_final_paket_2026-08-12/islemler_cmb.json"

LIVE_COLS = ["id", "plan_id", "ticker", "side", "ts_open", "ts_close", "entry", "exit", "qty",
             "r_multiple", "r_multiple_expected", "pnl_pct", "pnl_dollars", "costs", "exit_reason",
             "strategy_version", "regime", "setup", "score", "exploration", "scaled_out",
             "bars_held", "mfe_r", "mae_r", "kaynak", "skill_chain"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---- 1) DB kopyasından dosya-çağı defterleri çıkar ---------------------------------------------
def db_dump(dbp: Path) -> dict:
    con = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    o = {}
    for tbl, ad in (("trades", "trades"), ("trade_plans", "plans")):
        rows = []
        for r in con.execute(f"SELECT * FROM {tbl} ORDER BY rowid"):
            d = dict(r)
            d.pop("seq", None)
            ex = d.pop("extra_json", None)
            if ex:
                try:
                    d.update(json.loads(ex))
                except Exception:
                    pass
            rows.append({k: v for k, v in d.items() if v is not None})
        o[ad] = rows
    for tbl, ad in (("scoreboard", "scoreboard"), ("portfolio", "portfolio"),
                    ("shadow_books", "shadow_books")):
        r = con.execute(f"SELECT doc_json FROM {tbl} LIMIT 1").fetchone()
        o[ad] = json.loads(r[0]) if r else None
    pts = [[r[0], r[1]] for r in con.execute("SELECT ts, equity FROM equity_curve ORDER BY rowid")]
    o["equity"] = {"points": pts}
    con.close()
    return o


dump = db_dump(BASE / "meridian.db")
canli_trades = dump["trades"]

# ---- 2) ŞEMA UYUM RAPORU -----------------------------------------------------------------------
cmb = json.loads(CMB.read_text())
cmb_alanlar = sorted({k for r in cmb for k in r})
cmb_dolu = {k: sum(1 for r in cmb if r.get(k) is not None) for k in cmb_alanlar}
canli_alanlar = sorted({k for r in canli_trades for k in r})
DAMGA = {"kaynak": "prosedür (kart aşama-2: replay_seed)",
         "strategy_version": "prosedür (kart aşama-2: 5)",
         "id": "defter yazarının sayaç ürünü (broker._id → T00001…)"}
tasinabilir = [c for c in LIVE_COLS if c in cmb_alanlar and cmb_dolu.get(c, 0) > 0]
damgali = [c for c in LIVE_COLS if c in DAMGA]
eksik = [c for c in LIVE_COLS if c not in tasinabilir and c not in damgali]
sema = {
    "kaynak_dosya": str(CMB), "sha256": sha(CMB), "n_satir": len(cmb),
    "cmb_alanlari": {k: {"var": sum(1 for r in cmb if k in r), "dolu": cmb_dolu[k]}
                     for k in cmb_alanlar},
    "canli_trades_alanlari": canli_alanlar,
    "TASINABILIR (veriden)": tasinabilir,
    "DAMGALANIR (veriden DEĞİL, prosedürden)": {k: DAMGA[k] for k in damgali},
    "EKSIK (uydurulamaz — None kalır)": eksik,
    "cmb_fazlasi (canlı şemada yok)": [k for k in cmb_alanlar if k not in LIVE_COLS],
    "ozet": (f"canlı şema {len(LIVE_COLS)} alan · 032 artefaktından taşınabilen {len(tasinabilir)} · "
             f"prosedürel damga {len(damgali)} · UYDURULAMAZ EKSİK {len(eksik)}"),
}

# ---- 3) İki dünyanın defterleri ----------------------------------------------------------------
live_rows = [t for t in canli_trades if t.get("kaynak") == "live_paper"]
seed_rows = [t for t in canli_trades if t.get("kaynak") == "replay_seed"]
A = seed_rows + live_rows                                  # bugünkü hâl (97)

B_seed = []
for i, r in enumerate(cmb, 1):
    row = {"id": f"T{i:05d}", "kaynak": "replay_seed", "strategy_version": 5}
    for c in ("ts_open", "ts_close", "ticker", "r_multiple", "pnl_dollars", "exit_reason",
              "bars_held", "regime", "setup", "qty"):
        if r.get(c) is not None:
            row[c] = r[c]
    B_seed.append(row)
B_seed.sort(key=lambda t: (str(t.get("ts_close") or ""), t["id"]))
B = B_seed + live_rows                                     # 885 + 2 = 887


# ---- 4) Dünya kurulumu -------------------------------------------------------------------------
def kur(ad: str, trades: list) -> Path:
    d = SB / ad
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for f in BASE.iterdir():
        if f.name == "meridian.db":
            continue                                       # DB YOK → store dosya çağında koşar
        shutil.copy2(f, d / f.name)
    (d / "trades.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n"
                                            for t in trades))
    (d / "trade_plans.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n"
                                                 for t in dump["plans"]))
    (d / "scoreboard.json").write_text(json.dumps(dump["scoreboard"], ensure_ascii=False))
    (d / "portfolio.json").write_text(json.dumps(dump["portfolio"], ensure_ascii=False))
    (d / "shadow_books.json").write_text(json.dumps(dump["shadow_books"], ensure_ascii=False))
    (d / "equity_curve.json").write_text(json.dumps(dump["equity"], ensure_ascii=False))
    (d / "bars").mkdir(exist_ok=True)
    (d / "history").mkdir(exist_ok=True)
    return d


sys.path.insert(0, str(REPO))
os.environ["MERIDIAN_DB"] = "off"


def olc(dunya_dir: Path) -> dict:
    """TEK dünyanın tüm tüketici çıktıları. Her ölçüm ayrı try — biri düşerse ötekiler ölçülür."""
    import importlib
    from meridian import config
    config.STATE = dunya_dir
    config.BARS = dunya_dir / "bars"
    config.HISTORY = dunya_dir / "history"
    import meridian.store as store
    import meridian.storage as storage
    for m in (store, storage):
        importlib.reload(m)
    from meridian import (analytics, ledgerstamp, skills, component_ic, threshold_curve,
                          shadowlaw, score as score_mod, validation, dataset, regime_trigger,
                          counterfactual)
    for m in (analytics, ledgerstamp, skills, component_ic, threshold_curve, shadowlaw,
              regime_trigger, counterfactual):
        importlib.reload(m)
    res: dict = {}

    def gir(ad, fn):
        try:
            res[ad] = fn()
        except Exception as e:
            res[ad] = {"_olculemedi": f"{type(e).__name__}: {e}",
                       "_iz": traceback.format_exc().splitlines()[-4:]}

    tr = store.read_jsonl("trades.jsonl")
    goal = config.goal()
    res["_defter"] = {"n": len(tr), **ledgerstamp.counts(tr)}

    # (1) KALİBRASYON — skor→sonuç
    def _sc():
        c = analytics.score_calibration()
        if c is None:
            return {"_None": "örneklem < 30 — uydurma istatistik yok"}
        return {"n": c["n"], "n_real": c["n_real"], "n_cf": c["n_cf"],
                "katmanlar": c["katmanlar"], "gercek_kaynak": c["gercek_kaynak"],
                "verdict": c["verdict"]}
    gir("kalibrasyon_score_calibration", _sc)

    # (2) LLM kalibrasyonu
    def _llm():
        c = analytics.llm_opinion_calibration()
        return {k: c.get(k) for k in ("n_pairs", "buckets", "cf_pairs", "promoted", "r_gap",
                                      "n_plans_with_opinion")}
    gir("kalibrasyon_llm", _llm)

    # (3) DSR / PBO
    def _trio():
        t = analytics.validation_trio()
        return {"dsr_canli": t["dsr_canli"], "n_trials": t["n_trials"],
                "pbo": t["pbo"], "defter": t["defter"]}
    gir("dsr_pbo_validation_trio", _trio)

    # (4) KARNE KAPILARI
    def _edge():
        e = analytics.edge_verdict()
        return {"passed": e["passed"], "failed": e.get("failed"),
                "unmeasured": e["unmeasured"], "zayif": e.get("zayif"),
                "verdict": e["verdict"],
                "criteria": {k: {kk: v.get(kk) for kk in ("status", "value", "esik", "n",
                                                          "anlamli", "kaynak")}
                             for k, v in e["criteria"].items()}}
    gir("karne_edge_verdict", _edge)

    def _res():
        r = analytics.result_verdict()
        return {"passed": r["passed"], "failed": r.get("failed"),
                "unmeasured": r["unmeasured"], "zayif": r.get("zayif"),
                "verdict": r["verdict"],
                "criteria": {k: {kk: v.get(kk) for kk in ("status", "value", "esik", "n", "ci",
                                                          "anlamli")}
                             for k, v in r["criteria"].items()}}
    gir("karne_result_verdict", _res)

    def _var():
        v = shadowlaw.variance_attribution(tr, goal, n_boot=400, seed=20260813)
        if v is None:
            return {"_None": "defter blok kurulamayacak kadar boş/biçimsiz"}
        return {k: v.get(k) for k in ("n_trades", "span_days", "block_days", "n_blocks",
                                      "n_valid", "eski_paylar", "v3_paylar", "sd_dusus",
                                      "ort_dusus", "dusus_p05", "dusus_p95",
                                      "dd_veto_gurultunun_disinda", "para_payi_tek_terim",
                                      "margin_scale", "ret_scale_k")}
    gir("karne_variance_attribution", _var)

    # (5) SKILLS KARNESİ + EKSEN-2
    def _skill():
        a = analytics.skill_attribution()
        return {"skills": [s for s in a.get("skills", []) if (s.get("n") or 0) > 0],
                "n_skill_gercek_katmanli": sum(1 for s in a.get("skills", [])
                                               if (s.get("n") or 0) > 0)}
    gir("skills_attribution", _skill)
    gir("skills_axis2_teshis", lambda: {k: v for k, v in skills.axis2_diagnosis().items()
                                        if k in ("sayim", "aktif_payda", "esik")})
    gir("skills_oneriler", lambda: skills.recommend_from_attribution())

    # (6) CF DEFTERİ & NEAR-MISS (tohumu okumuyor — kanıt olarak yine ölçülür)
    def _nm():
        n = analytics.near_miss_report()
        return {"resolved_total": n["resolved_total"], "n_kova": len(n["buckets"]),
                "prov": n.get("_kaynak")}
    gir("near_miss", _nm)
    gir("cf_defteri_n", lambda: {"resolved_entered":
                                 len(counterfactual.resolved_rows(entered_only=True))})

    # (7) HERMES / EBEVEYN ZİNCİRİ (davranış kapıları — SALT SAYIM, hiçbir şey tetiklenmez)
    def _parent():
        st = config.load_strategy()
        v, par = int(st.get("version", 1)), st.get("parent")
        cur = [t for t in tr if t.get("strategy_version") == v]
        pr = [t for t in tr if t.get("strategy_version") == par]
        ms = int(goal["min_sample"])
        return {"version": v, "parent": par, "min_sample": ms,
                "n_cur": len(cur), "n_parent": len(pr),
                "cur_min_sample_gecti": len(cur) >= ms,
                "parent_min_sample_gecti": len(pr) >= ms,
                "rollback_kapisi": ("AÇILIR — evaluate_outcomes/check_and_rollback ÖLÇER"
                                    if len(cur) >= ms else
                                    "KAPALI — cur_trades < min_sample (return None)"),
                "cur_score": score_mod.score(cur, goal) if len(cur) >= ms else None,
                "parent_score": score_mod.score(pr, goal) if len(pr) >= ms else None}
    gir("hermes_ebeveyn_zinciri", _parent)

    def _reflect():
        hs = json.loads((dunya_dir / "hermes_status.json").read_text()) \
            if (dunya_dir / "hermes_status.json").exists() else {}
        base = hs.get("last_reflect_at", 97)
        every = int(goal.get("reflection_every") or 5)
        since = max(0, len(tr) - int(base))
        return {"last_reflect_at_kalici": base, "defter_n": len(tr),
                "trades_since_last_reflection": since, "reflection_every": every,
                "trades_until_next": max(0, every - since),
                "sayi_kapisi_acik": since >= every,
                "not": "gün-aralığı (horizon) kapısı AYRICA vardır; burada yalnız SAYI kolu"}
    gir("hermes_reflect_sayaci", _reflect)

    # (8) N4 / ÖRNEKLEM SAYAÇLARI
    def _ls():
        s = analytics.learning_scorecard(goal)
        return {"trades_total": s["trades_total"], "defter": s["defter"],
                "min_sample": s["min_sample"], "loop_state": s["loop_state"],
                "verdict": s["verdict"],
                "regime_budget_triggers": s.get("regime_budget_triggers")}
    gir("orneklem_learning_scorecard", _ls)

    # (9) BİLEŞEN IC + EŞİK EĞRİSİ (canlıda n=95/97 gösteriyorlardı)
    def _cic():
        c = component_ic.component_ic(write=True)
        if c is None:
            return {"_None": "component_ic ölçemedi (sandbox'ta state/bars YOK — bar tabanı şart)"}
        return {"verdict": c.get("verdict"), "n_gozlem": c.get("n_gozlem"),
                "layers": c.get("layers"), "anlamli_sayim": c.get("anlamli_sayim")}
    gir("component_ic", _cic)

    def _tc():
        c = threshold_curve.build()
        if c is None:
            return {"_None": "threshold_curve ölçemedi (örneklem/eşleşme yetersiz)"}
        return {"verdict": c.get("verdict"), "n": c.get("n"),
                "katmanlar": c.get("katmanlar"), "gercek": c.get("gercek"),
                "canli_esik": c.get("canli_esik")}
    gir("threshold_curve", _tc)

    # (10) MAE + gece/gündüz + kötümser
    gir("mae_profile", lambda: {k: (analytics.mae_profile() or {}).get(k)
                                for k in ("n", "verdict")})
    gir("net_kotumser", lambda: analytics.net_kotumser())
    gir("regime_trigger", lambda: regime_trigger.DeferredRegimeBudgetTrigger().evaluate(tr))
    gir("portfolio_realized_pnl",
        lambda: json.loads((dunya_dir / "portfolio.json").read_text()).get("realized_pnl"))

    # SIEVE — hangi tüketici KAÇ satır düşürdü (şema eksikliğinin fiyatı)
    def _sieve():
        s = json.loads((dunya_dir / "sieve.json").read_text()) \
            if (dunya_dir / "sieve.json").exists() else {}
        return {k: {"in": v.get("in"), "out": v.get("out"), "drops": v.get("drops")}
                for k, v in (s.get("stages") or {}).items()}
    gir("sieve_eleme_muhasebesi", _sieve)
    return res


sonuc = {"sema_uyumu": sema,
         "dunya_A": {"tanim": "canlı defterin bugünkü hâli", "n": len(A),
                     "kirilim": dict(Counter(t.get("kaynak") for t in A))},
         "dunya_B": {"tanim": "EDG-032 C+mb (885) + aynı 2 live_paper", "n": len(B),
                     "kirilim": dict(Counter(t.get("kaynak") for t in B))}}

for ad, rows in (("A", A), ("B", B)):
    d = kur(ad, rows)
    sonuc[f"olcum_{ad}"] = olc(d)

OUT.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))
print(f"[edg036] yazıldı: {OUT}")
print(json.dumps(sema["ozet"], ensure_ascii=False))
