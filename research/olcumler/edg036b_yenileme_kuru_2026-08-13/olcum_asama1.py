"""EDG-2026-036b AŞAMA-1 KURU KOŞUM (YEREL izole sandbox; canlıya HİÇBİR ŞEY yazılmaz).

DÜNYALAR
  A          canlı defterin BUGÜNKÜ hâli — 97 işlem (95 replay_seed sv=4 + 2 live_paper sv=3),
             409 plan, canlı portfolio (realized_pnl 277,98$)
  B          YENİLEME — KART NİYETİ (koruyucu): 885 TAM-SATIR tohum işlemi (`kaynak=replay_seed`,
             `strategy_version=5`) + AYNI 2 live_paper satırı BİT-AYNI; plan defteri =
             run.py:276-283 `_keep` + 2 live_paper planı KORUNARAK; portfolio DOKUNULMAZ
  B_sv3      B ile aynı, tek fark tohumun `strategy_version=3` damgası (replay'in kendi ürettiği)
  B_svTOHUM  B ile aynı, tohum AYRI SÜRÜM-UZAYINDA (`strategy_version=90`) — kartın hükümde
             önerdiği "tohum ayrı sürüm-uzayı" seçeneğinin ölçümü
  B_literal  `run.py replay_seed` NE YAPIYORSA O: trades.jsonl TAMAMEN ezilir (live_paper YOK
             OLUR), trade_plans.jsonl TAMAMEN ezilir (live planlar YOK OLUR), portfolio
             `_reset_book_to` kimliğiyle yeniden kurulur (realized_pnl = Σ tohum K/Z)

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden). Tohum satırları TAM-SATIR defterinden gelir
(kırpma YOK); yalnız `kaynak` damgası prosedürden basılır (`ledgerstamp.stamp_rows`) ve
`strategy_version` dünya-parametresidir — ikisi de raporda AYRICA beyan edilir.

kullanım: olcum_asama1.py <sandbox_kok> <cikti.json>
"""
import hashlib
import importlib
import json
import os
import shutil
import sys
import traceback
from collections import Counter
from pathlib import Path

REPO = Path("/Users/erdemozturk/AI-Trading")
SB = Path(sys.argv[1])
BASE = SB / "base"
OUT = Path(sys.argv[2])
D036B = REPO / "research/olcumler/edg036b_yenileme_kuru_2026-08-13"

# TOHUM KAYNAĞI: gerçek yenileme yolu run.py:190-191 `with_gate_detail=True` koşar → gd defteri.
TAM_GD = D036B / "islemler_tam_kontrolgd.json"
TAM_STD = D036B / "islemler_tam_kontrol.json"
PLAN_GD = D036B / "planlar_yenileme_kontrolgd.json"
SEED_SV = {"B": 5, "B_sv3": 3, "B_svTOHUM": 90, "B_literal": 5}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_rows(rows) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
                                     default=str).encode()).hexdigest()


sys.path.insert(0, str(REPO))
os.environ["MERIDIAN_DB"] = "off"
# İZOLASYON ÖNCE: config.STATE daha ilk ithalde sandbox'a çevrilir ki hiçbir modül canlı/yerel
# `state/` dizinine dokunmasın (ithal anında yazım yok, ama sıra disiplini ucuz).
from meridian import config as _cfg0                          # noqa: E402
_cfg0.STATE = BASE
_cfg0.BARS = BASE / "bars"
_cfg0.HISTORY = BASE / "history"
from meridian import ledgerstamp as _ls0                      # noqa: E402  (damga sabitleri)

# ---- taban okuma ------------------------------------------------------------------------------
canli_trades = [json.loads(l) for l in (BASE / "trades.jsonl").read_text().splitlines() if l.strip()]
canli_plans = [json.loads(l) for l in (BASE / "trade_plans.jsonl").read_text().splitlines() if l.strip()]
canli_port = json.loads((BASE / "portfolio.json").read_text())

live_rows = [t for t in canli_trades if t.get("kaynak") == "live_paper"]
seed_rows_canli = [t for t in canli_trades if t.get("kaynak") == "replay_seed"]
live_plan_ids = {t.get("plan_id") for t in live_rows if t.get("plan_id")}
live_plans = [p for p in canli_plans if p.get("id") in live_plan_ids]

tam = json.loads(TAM_GD.read_text())
tam_std = json.loads(TAM_STD.read_text())
plan_keep = json.loads(PLAN_GD.read_text())

# TOHUM ÖZDEŞLİĞİ: gate-detay AÇIK/KAPALI işlem defterleri AYNI mı? (dünya değişmemiş olmalı)
tohum_ozdeslik = {
    "gd_vs_std_islem_ayni": tam == tam_std,
    "gd_sha_satirlar": sha_rows(tam), "std_sha_satirlar": sha_rows(tam_std),
    "n_gd": len(tam), "n_std": len(tam_std),
}


def seed_kur(sv: int) -> list:
    """TAM satırları defter satırına çevir: kırpma YOK; `kaynak` damgası ledgerstamp'ten,
    `strategy_version` dünya parametresinden (prosedürel damga — veriden GELMEZ)."""
    rows = []
    for r in tam:
        row = dict(r)
        row["strategy_version"] = sv
        rows.append(row)
    return _ls0.stamp_rows(rows, _ls0.REPLAY_SEED)


DUNYALAR = {
    "A": {"tanim": "canlı defterin bugünkü hâli",
          "trades": canli_trades, "plans": canli_plans, "portfolio": canli_port},
}
for ad in ("B", "B_sv3", "B_svTOHUM"):
    s = seed_kur(SEED_SV[ad])
    DUNYALAR[ad] = {
        "tanim": f"yenileme (koruyucu) — 885 tohum sv={SEED_SV[ad]} + 2 live_paper BİT-AYNI",
        "trades": s + live_rows,
        "plans": plan_keep + live_plans,
        "portfolio": canli_port,
    }
_sl = seed_kur(SEED_SV["B_literal"])
_realized = round(sum(float(t.get("pnl_dollars") or 0) for t in _sl), 2)
from meridian.score import START_EQUITY as _SE                # noqa: E402

DUNYALAR["B_literal"] = {
    "tanim": "run.py replay_seed HARFİ HARFİNE — defterlerin TAMAMI ezilir, kitap yeniden kurulur",
    "trades": _sl,
    "plans": plan_keep,
    "portfolio": {**canli_port, "cash": round(_SE + _realized, 2), "realized_pnl": _realized,
                  "last_id": len(_sl), "positions": {}, "armed": [], "pending_exits": {}},
}


# ---- dünya kurulumu ---------------------------------------------------------------------------
def kur(ad: str, w: dict) -> Path:
    d = SB / ad
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for f in BASE.iterdir():
        if f.is_file():
            shutil.copy2(f, d / f.name)
    (d / "trades.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n"
                                            for t in w["trades"]))
    (d / "trade_plans.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n"
                                                 for p in w["plans"]))
    (d / "portfolio.json").write_text(json.dumps(w["portfolio"], ensure_ascii=False))
    # BAR TABANI: yerel önbelleğe SALT-OKUNUR sembolik bağ (component_ic/threshold_curve bar ister;
    # 036'nın ilk kuru koşumunda bağ YOKTU ve iki tüketici "ölçülemedi" dönmüştü).
    b = d / "bars"
    if not b.exists():
        b.symlink_to(REPO / "state" / "bars")
    (d / "history").mkdir(exist_ok=True)
    return d


# ---- TEK DÜNYANIN TÜM TÜKETİCİLERİ ------------------------------------------------------------
def olc(dd: Path) -> dict:
    from meridian import config
    config.STATE = dd
    config.BARS = dd / "bars"
    config.HISTORY = dd / "history"
    config.reload_config()
    import meridian.store as store
    import meridian.storage as storage
    for m in (store, storage):
        importlib.reload(m)
    from meridian import (analytics, ledgerstamp, skills, component_ic, threshold_curve,
                          shadowlaw, score as score_mod, sieve, versioning, rollback,
                          regime_trigger, counterfactual)
    for m in (analytics, ledgerstamp, skills, component_ic, threshold_curve, shadowlaw,
              sieve, versioning, rollback, regime_trigger, counterfactual):
        importlib.reload(m)
    res: dict = {}

    def gir(ad, fn):
        try:
            res[ad] = fn()
        except Exception as e:
            res[ad] = {"_olculemedi": f"{type(e).__name__}: {e}",
                       "_iz": traceback.format_exc().splitlines()[-4:]}

    tr = store.read_jsonl("trades.jsonl")
    pl = store.read_jsonl("trade_plans.jsonl")
    goal = config.goal()
    res["_defter"] = {"n": len(tr), "n_plan": len(pl), **ledgerstamp.counts(tr)}

    # (1) KORUNUM — plan ↔ işlem birleşmesi (yenilemenin kırdığı iddia edilen eksen)
    def _kor():
        pid = {p.get("id") for p in pl}
        eslesen = sum(1 for t in tr if t.get("plan_id") in pid)
        oksuz = [t.get("plan_id") for t in tr if t.get("plan_id") not in pid][:5]
        kir = Counter(t.get("kaynak") for t in tr if t.get("plan_id") not in pid)
        return {"n_islem": len(tr), "n_plan": len(pl), "plan_bulan_islem": eslesen,
                "aciklanamayan_islem": len(tr) - eslesen,
                "aciklanamayan_kaynak_kirilimi": dict(kir),
                "ornek_oksuz_plan_id": oksuz,
                "islemsiz_plan_n": len(pid) - len({t.get("plan_id") for t in tr
                                                   if t.get("plan_id") in pid})}
    gir("korunum_plan_islem", _kor)

    # (2) KALİBRASYON
    def _sc():
        c = analytics.score_calibration()
        if c is None:
            return {"_None": "örneklem < eşik — uydurma istatistik yok"}
        return {"n": c.get("n"), "n_real": c.get("n_real"), "n_cf": c.get("n_cf"),
                "katmanlar": c.get("katmanlar"), "gercek_kaynak": c.get("gercek_kaynak"),
                "verdict": c.get("verdict")}
    gir("score_calibration", _sc)

    def _llm():
        c = analytics.llm_opinion_calibration()
        return {k: c.get(k) for k in ("n_pairs", "buckets", "cf_pairs", "promoted", "r_gap",
                                      "n_plans_with_opinion")}
    gir("llm_calibration", _llm)

    # (3) DSR / PBO
    def _trio():
        t = analytics.validation_trio()
        return {"dsr_canli": t.get("dsr_canli"), "n_trials": t.get("n_trials"),
                "pbo": t.get("pbo"), "defter": t.get("defter")}
    gir("dsr_pbo_validation_trio", _trio)

    # (4) FAZ-6 KİLİTLERİ
    def _edge():
        e = analytics.edge_verdict()
        return {"passed": e.get("passed"), "failed": e.get("failed"),
                "unmeasured": e.get("unmeasured"), "zayif": e.get("zayif"),
                "verdict": e.get("verdict"),
                "criteria": {k: {kk: v.get(kk) for kk in ("status", "value", "esik", "n",
                                                          "anlamli", "kaynak")}
                             for k, v in (e.get("criteria") or {}).items()}}
    gir("edge_verdict", _edge)

    def _res():
        r = analytics.result_verdict()
        return {"passed": r.get("passed"), "failed": r.get("failed"),
                "unmeasured": r.get("unmeasured"), "zayif": r.get("zayif"),
                "verdict": r.get("verdict"),
                "criteria": {k: {kk: v.get(kk) for kk in ("status", "value", "esik", "n", "ci",
                                                          "anlamli")}
                             for k, v in (r.get("criteria") or {}).items()}}
    gir("result_verdict", _res)

    def _var():
        v = shadowlaw.variance_attribution(tr, goal, n_boot=400, seed=20260813)
        if v is None:
            return {"_None": "defter blok kurulamayacak kadar boş/biçimsiz"}
        return {k: v.get(k) for k in ("n_trades", "span_days", "block_days", "n_blocks",
                                      "n_valid", "eski_paylar", "v3_paylar", "sd_dusus",
                                      "ort_dusus", "dusus_p05", "dusus_p95",
                                      "dd_veto_gurultunun_disinda", "para_payi_tek_terim",
                                      "margin_scale", "ret_scale_k")}
    gir("variance_attribution", _var)

    # (5) SKILLS
    def _skill():
        a = analytics.skill_attribution()
        return {"skills": [s for s in a.get("skills", []) if (s.get("n") or 0) > 0],
                "n_skill_gercek_katmanli": sum(1 for s in a.get("skills", [])
                                               if (s.get("n") or 0) > 0)}
    gir("skills_attribution", _skill)
    def _ax2():
        a = skills.axis2_diagnosis()
        kov = a.get("kovalar") or {}
        return {"kova_sayilari": {k: len(v) for k, v in kov.items()},
                "gercek_islem_tasiyan_skill_n": sum(
                    1 for v in kov.values() for s in v if (s.get("n") or 0) > 0),
                **{k: v for k, v in a.items() if k not in ("kovalar",)
                   and len(json.dumps(v, default=str)) < 400}}
    gir("skills_axis2", _ax2)

    # (6) CF / NEAR-MISS
    def _nm():
        n = analytics.near_miss_report()
        return {"resolved_total": n.get("resolved_total"), "n_kova": len(n.get("buckets") or {})}
    gir("near_miss", _nm)
    gir("cf_defteri_n", lambda: {"resolved_entered":
                                 len(counterfactual.resolved_rows(entered_only=True))})
    def _cff():
        c = analytics.cf_fidelity()
        if c is None:
            return {"_None": "cf_fidelity ölçemedi (kesişim yetersiz) — uydurulmadı"}
        return {k: c.get(k) for k in ("n", "corr", "mean_diff_r", "fidelity_ok",
                                      "eksik_mekanizmalar", "eksik_friksiyon")}
    gir("cf_fidelity", _cff)

    # (7) HERMES yansıma sayacı + ebeveyn zinciri
    def _reflect():
        p = dd / "hermes_status.json"
        hs = json.loads(p.read_text()) if p.exists() else {}
        base = hs.get("last_reflect_at", 97)
        every = int(goal.get("reflection_every") or 5)
        since = max(0, len(tr) - int(base))
        return {"last_reflect_at_kalici": base, "defter_n": len(tr),
                "trades_since_last_reflection": since, "reflection_every": every,
                "trades_until_next": max(0, every - since), "sayi_kapisi_acik": since >= every}
    gir("hermes_reflect_sayaci", _reflect)

    # (8) ÖRNEKLEM
    def _ls():
        s = analytics.learning_scorecard(goal)
        return {"trades_total": s.get("trades_total"), "defter": s.get("defter"),
                "min_sample": s.get("min_sample"), "loop_state": s.get("loop_state"),
                "verdict": s.get("verdict")}
    gir("learning_scorecard", _ls)

    # (9) BİLEŞEN IC + EŞİK EĞRİSİ (bar tabanı bu koşumda BAĞLI)
    def _cic():
        c = component_ic.component_ic(write=True)
        if c is None:
            return {"_None": "component_ic ölçemedi (None döndü)"}
        return {"verdict": c.get("verdict"), "n_gozlem": c.get("n_gozlem"),
                "layers": c.get("layers"), "anlamli_sayim": c.get("anlamli_sayim")}
    gir("component_ic", _cic)

    def _tc():
        c = threshold_curve.build()
        if c is None:
            return {"_None": "threshold_curve ölçemedi (örneklem/eşleşme yetersiz)"}
        return {"verdict": c.get("verdict"), "n_gozlem": c.get("n_gozlem"),
                "canli_min_score": c.get("canli_min_score"), "min_n": c.get("min_n"),
                "katmanlar": c.get("katmanlar"), "cf_sadakat": c.get("cf_sadakat")}
    gir("threshold_curve", _tc)

    # (10) MAE / kötümser / rejim tetikleyici / kitap
    def _mae():
        m = analytics.mae_profile()
        if m is None:
            return {"_None": "mae_profile ölçemedi (örneklem/alan yetersiz) — uydurulmadı"}
        return {k: v for k, v in m.items() if not isinstance(v, (list,))
                or len(json.dumps(v, default=str)) < 400}
    gir("mae_profile", _mae)
    gir("net_kotumser", lambda: analytics.net_kotumser())
    gir("regime_trigger", lambda: regime_trigger.DeferredRegimeBudgetTrigger().evaluate(tr))
    gir("portfolio_realized_pnl",
        lambda: json.loads((dd / "portfolio.json").read_text()).get("realized_pnl"))

    # (11) ÜÇ KRİTİK BAYRAK -------------------------------------------------------------------
    def _sieve():
        rp = sieve.report()
        return {"ok": sieve.ok(), "violations": rp.get("violations"),
                "n_violation": len(rp.get("violations") or []),
                "kritik_n": sum(1 for v in (rp.get("violations") or [])
                                if str(v.get("severity", v.get("seviye", ""))).lower()
                                in ("kritik", "critical", "hard")),
                "stages": {k: {"in": v.get("in"), "out": v.get("out"), "drops": v.get("drops")}
                           for k, v in (rp.get("stages") or {}).items()},
                "esik": {"SEMA_ESCALATE_FRAC": getattr(sieve, "SEMA_ESCALATE_FRAC", None),
                         "SEMA_ESCALATE_MIN_N": getattr(sieve, "SEMA_ESCALATE_MIN_N", None)}}
    gir("BAYRAK_sieve", _sieve)

    def _drift():
        dr = shadowlaw.variance_drift(tr, goal)
        return {"olculdu": dr.get("olculdu"), "kayma": dr.get("kayma"),
                "kayitli_n_trades": dr.get("kayitli_n_trades"),
                "yururlukteki_MONEY_GATE_MARGIN": shadowlaw.MONEY_GATE_MARGIN,
                "yururlukteki_DD_VETO_MARGIN": shadowlaw.DD_VETO_MARGIN,
                "olcum_ozet": {k: (dr.get("olcum") or {}).get(k)
                               for k in ("margin_scale", "sd_dusus", "ort_dusus",
                                         "dd_veto_gurultunun_disinda", "para_payi_tek_terim",
                                         "n_trades", "n_blocks", "block_days")}}
    gir("BAYRAK_shadowlaw_drift", _drift)

    def _rb():
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
        return {
            "version": v, "parent": par, "ship_eval_regime": ereg, "min_sample": ms,
            "n_cur": len(cur), "n_parent": len(pr), "erken_return_None": len(cur) < ms,
            "cur_score": cur_score, "par_score_ham": par_score, "par_score": par_score2,
            "par_score_yolu": yol, "rollback_if_worse_by": goal.get("rollback_if_worse_by"),
            "ham_delta": (None if (cur_score is None or par_score2 is None)
                          else round(cur_score - par_score2, 4)),
            "KAPI_ACILIYOR": (None if (cur_score is None or par_score2 is None) else
                              bool((cur_score - par_score2)
                                   < -float(goal["rollback_if_worse_by"]))),
            "not": ("nihai karar `_karar_girdisi` (would_have replay'i) ile verilir — o replay bar "
                    "tabanı ister ve BURADA KOŞULMADI; rapor karar noktasına KADARki girdilerdir")}
    gir("BAYRAK_rollback_kapisi", _rb)

    # (12) live_paper BİT-AYNILIĞI + kaynak ayrımı
    def _lp():
        lp = [t for t in tr if t.get("kaynak") == "live_paper"]
        return {"n": len(lp), "sha_satirlar": sha_rows(lp),
                "pnl_toplam": round(sum(float(t.get("pnl_dollars") or 0) for t in lp), 2),
                "id_ler": [t.get("id") for t in lp],
                "plan_id_ler": [t.get("plan_id") for t in lp]}
    gir("live_paper_satirlari", _lp)
    return res


# ---- koşum ------------------------------------------------------------------------------------
sonuc = {
    "kart": "EDG-2026-036", "asama": "1 (kuru koşum — TEKRAR, düzeltilmiş artefaktla)",
    "olcum_ajani_beyani": (
        "SALT-ÖLÇÜM. Karta DOKUNULMADI, hüküm YAZILMADI, git komutu KOŞULMADI, repo koduna "
        "DOKUNULMADI. Canlıya YALNIZ salt-okuma (stdin betiği; DB mode=ro). Aşama-1 tamamen "
        "YEREL izole sandbox'ta koştu. UYDURMA YASAĞI: tohum satırları TAM-SATIR defterinden "
        "KIRPILMADAN alındı; yalnız `kaynak` damgası (ledgerstamp.stamp_rows) ve "
        "`strategy_version` (dünya parametresi) prosedürden basıldı."),
    "tohum_kaynagi": {
        "tam_satir_defteri": str(TAM_GD), "sha256": sha(TAM_GD), "n": len(tam),
        "plan_defteri": str(PLAN_GD), "plan_sha256": sha(PLAN_GD), "plan_n": len(plan_keep),
        "gate_detay": True,
        "gerekce": "run.py:190-191 gerçek yenileme yolu with_gate_detail=True koşar",
        "cost_model": json.loads((D036B / "sonuc_kontrolgd.json").read_text())
        .get("replay", {}).get("cost_model"),
        "gd_vs_std_ozdeslik": tohum_ozdeslik},
    "canli_taban": {"trades_n": len(canli_trades), "plans_n": len(canli_plans),
                    "kaynak_kirilimi": dict(Counter(t.get("kaynak") for t in canli_trades)),
                    "live_paper_plan_n": len(live_plans),
                    "portfolio_realized_pnl": canli_port.get("realized_pnl")},
    "dunyalar": {ad: {"tanim": w["tanim"], "n_islem": len(w["trades"]),
                      "n_plan": len(w["plans"]),
                      "kaynak_kirilimi": dict(Counter(t.get("kaynak") for t in w["trades"])),
                      "sv_kirilimi": dict(Counter(
                          f"{t.get('kaynak')}|sv={t.get('strategy_version')}"
                          for t in w["trades"]))}
                 for ad, w in DUNYALAR.items()},
}

for ad, w in DUNYALAR.items():
    d = kur(ad, w)
    print(f"[036b] ölçülüyor: {ad} (n={len(w['trades'])} plan={len(w['plans'])})", flush=True)
    sonuc[f"olcum_{ad}"] = olc(d)
    OUT.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))

OUT.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))
print(f"[036b] yazıldı: {OUT}")
