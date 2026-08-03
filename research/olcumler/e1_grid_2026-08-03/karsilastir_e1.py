"""E1 GRID DERLEYİCİSİ — kollar `kosum.py`nin çıktısıdır; burada YALNIZ okuma/kıyas var,
ikinci bir ölçüm motoru YOK. Çıktı: sonuc_e1.json (makine-okunur).

HÜKÜM CÜMLESİ KURULMAZ: kartın kill#1 eşiği (dolmama > %40) SAYIYLA yan yana konur.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

SB = pathlib.Path(__file__).resolve().parent
DEPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
KT = DEPO / "research/olcumler/karne_tazeleme_2026-08-03"
KO = DEPO / "research/olcumler/karne_olcum"
ESKI_SB = SB.parent / "karne_tazeleme"

GRID = ["a_mkt", "a_cnl", "b_mkt", "b_cnl", "c_mkt", "c_cnl"]
REF = ["ref_limitsiz"]
ETIKET = {
    "a_mkt": "min(0,25·ATR14, %0,5) × marketable_limit",
    "a_cnl": "min(0,25·ATR14, %0,5) × cancel",
    "b_mkt": "min(0,5·ATR14, %1,0) × marketable_limit  [MEVCUT VARSAYILAN]",
    "b_cnl": "min(0,5·ATR14, %1,0) × cancel",
    "c_mkt": "min(1,0·ATR14, %1,5) × marketable_limit",
    "c_cnl": "min(1,0·ATR14, %1,5) × cancel",
    "ref_limitsiz": "REFERANS (grid dışı): koşulsuz-açılış — limit tavanı bağlamaz",
}
KILL1 = 0.40


def kol(ad: str) -> dict:
    return json.loads((SB / f"kol_{ad}.json").read_text())


def defter(d: dict) -> dict:
    t = d.get("_trades_tum") or []
    pn = [x["pnl_dollars"] for x in t if x.get("pnl_dollars") is not None]
    g = [x for x in pn if x > 0]
    l = [x for x in pn if x < 0]
    return {"n": len(t), "net_usd": round(sum(pn), 2) if pn else None,
            "profit_factor": round(sum(g) / abs(sum(l)), 4) if l else None,
            "n_kazanan": len(g), "n_kaybeden": len(l),
            "friksiyon_usd": round(sum(x.get("costs") or 0 for x in t), 2) if t else None}


def satir(ad: str) -> dict:
    d = kol(ad)
    im, dl, kt = d["imza"], d["dolum"], d["kotumser"]
    kd = d["kacan_dolum"]
    sd = (d.get("para") or {}).get("search_detail") or {}
    return {
        "kol": ad, "etiket": ETIKET[ad],
        "entry_law": d["entry_law"],
        "goal_execution_v2": d["goal_execution_v2"],
        # --- dolum ---
        "cagri_n": dl["cagri_n"], "dolan_n": dl["dolan_n"], "dolmayan_n": dl["dolmayan_n"],
        "dolmama_orani": dl["dolmama_orani"],
        "dolmama_orani_yalniz_limit": dl["dolmama_orani_yalniz_limit"],
        "kill1_esik": KILL1,
        "dolmama_esik_farki": (None if dl["dolmama_orani"] is None
                               else round(dl["dolmama_orani"] - KILL1, 4)),
        "ret_nedenleri": dl["ret_nedenleri"],
        "motor_sayaci_esit_mi": (dl["ret_nedenleri"] == dl["motorun_kendi_sayaci_entry_rejects"]),
        # --- para / skor ---
        "net_usd": defter(d)["net_usd"],
        "net_usd_kotumser": kt["tum_replay"]["net_kotumser"],
        "kotumser_ek_maliyet": kt["tum_replay"]["ek_maliyet"],
        "search_net_usd": kt["search"]["net"],
        "search_net_usd_kotumser": kt["search"]["net_kotumser"],
        "para_v3_search": im["para_search"],
        "oos_score": im["oos_score"],
        "is_score": im["is_score"], "holdout_score": im["holdout_score"],
        "n_trades_total": im["n_trades_total"], "oos_n": im["oos_n"], "search_n": im["search_n"],
        "avg_r": im["avg_r"], "win_rate": im["win_rate"], "sharpe": im["sharpe"],
        "total_return_oos": im["total_return"],
        "max_drawdown_islem_oos": im["max_drawdown"],
        "mtm_max_dd_veto": (d.get("mtm_dd_veto") or {}).get("max_mtm_dd"),
        "mtm_max_dd_tam_pencere": (d.get("equity_tam") or {}).get("mtm_max_dd"),
        "tam_pencere_getiri": (d.get("equity_tam") or {}).get("toplam_getiri"),
        "profit_factor": defter(d)["profit_factor"],
        "friksiyon_usd": defter(d)["friksiyon_usd"],
        "search_pnl_usd": ((sd.get("realized_usd") or {}).get("pnl_usd")),
        "search_hedef_usd": ((sd.get("realized_usd") or {}).get("hedef_usd")),
        # --- kaçan dolum (betimleyici) ---
        "kacan_n": kd["n_dolmayan"],
        "kacan_ufuk_eksik": kd["n_ufuk_eksik"],
        "kacan_limit_r10": kd["yalniz_entry_missed_limit"]["r_10"],
        "kacan_limit_ret10": kd["yalniz_entry_missed_limit"]["ret_10"],
        "kacan_tum_r10": kd["tum_dolmayan"]["r_10"],
        # --- imza ---
        "skor_none_nedeni": ((d.get("oos_detail") or {}).get("reason")
                             if im["oos_score"] is None else None),
        "min_sample": (d.get("oos_detail") or {}).get("min_sample"),
        "karartma_vetosu_plan_n": sum(
            1 for p in (d.get("_plan_log") or [])
            if any("kazanç öncesi karartma" in str(r) for r in (p.get("gate_reasons") or []))),
        "plan_n": len(d.get("_plan_log") or []),
        "digest_tum": im["trade_digest_tum"][:16], "digest_search": im["trade_digest_search"][:16],
        "plan_digest": im["plan_digest"][:16], "equity_digest": im["equity_digest"][:16],
        "gap_gozlemi": d["gap_gozlemi"],
        "sure_sn": d["sure_sn"], "n_sembol": d["n_sembol"],
        "calendar": [d["calendar_ilk"], d["calendar_son"]],
    }


def kacan_eslesmesi(ad: str, ref: dict) -> dict:
    """Kaçan planların ref_limitsiz kolunda GERÇEKLEŞEN karşılığı (varsa).
    YOL-BAĞIMLIDIR: limitsiz kolun defteri farklı bir portföy yolunda oluştu; eşleşme
    'aynı planın limitsiz motorda ne yaptığı'nın betimidir, temiz bir karşı-olgu DEĞİL."""
    d = kol(ad)
    ref_islem = {}
    for t in ref["_trades_tum"]:
        ref_islem.setdefault((t.get("ticker"), str(t.get("ts_open"))[:10]), t)
    eslesen, r_top, usd_top = [], 0.0, 0.0
    kacan = [c for c in d["_fill_cagrilari"] if c["sonuc"] == "entry_missed_limit"]
    for c in kacan:
        t = ref_islem.get((c["ticker"], c["date"]))
        if t is None:
            continue
        eslesen.append({"ticker": c["ticker"], "date": c["date"],
                        "r": t.get("r_multiple"), "usd": t.get("pnl_dollars"),
                        "exit_reason": t.get("exit_reason")})
        r_top += float(t.get("r_multiple") or 0.0)
        usd_top += float(t.get("pnl_dollars") or 0.0)
    return {"kacan_limit_n": len(kacan), "eslesen_n": len(eslesen),
            "kapsama": (round(len(eslesen) / len(kacan), 4) if kacan else None),
            "toplam_r": round(r_top, 4), "toplam_usd": round(usd_top, 2),
            "ort_r": (round(r_top / len(eslesen), 4) if eslesen else None),
            "kazanan_n": sum(1 for e in eslesen if (e["usd"] or 0) > 0),
            "ornekler": eslesen[:15],
            "uyari": ("yol-bağımlı: limitsiz kolun portföy yolu farklıdır; eşleşmeyen kaçan "
                      "planlar o kolda slot/ısı/eş-anlılık nedeniyle hiç açılmamış olabilir")}


def main() -> None:
    tablo = [satir(a) for a in GRID + REF]
    t = {s["kol"]: s for s in tablo}
    out = {"olcum": "EXE-2026-001 · E1 icra grid",
           "kart": "research/cards/EXE-2026-001-entry-execution.yaml (OKUNDU, DEĞİŞTİRİLMEDİ)",
           "tablo": tablo}

    # ---------- DETERMİNİZM KAPISI ----------
    kt_j = json.loads((KT / "karsilastirma.json").read_text())
    kt_sonra = {s["kol"]: s for s in kt_j["tablo"]}["SONRA_guncel"]
    b = t["b_mkt"]
    kapi = {
        "iddia": ("b_mkt (mevcut varsayılan hücre) karne_tazeleme_2026-08-03 `guncel` kolunu "
                  "BİREBİR üretmelidir: aynı motor, aynı state, aynı goal.yaml"),
        "digest_esit": all(b[k] == kt_sonra[k2] for k, k2 in
                           (("digest_tum", "digest_tum"), ("digest_search", "digest_search"),
                            ("plan_digest", "plan_digest"), ("equity_digest", "equity_digest"))),
        "skor_esit": (b["oos_score"] == kt_sonra["oos_score"]
                      and b["para_v3_search"] == kt_sonra["para_search"]
                      and b["n_trades_total"] == kt_sonra["n_trades_total"]
                      and b["net_usd"] == kt_sonra["replay_defteri"]["net_usd"]),
        "b_mkt": {k: b[k] for k in ("digest_tum", "digest_search", "plan_digest", "equity_digest",
                                    "oos_score", "para_v3_search", "n_trades_total", "net_usd")},
        "karne_tazeleme_guncel": {"digest_tum": kt_sonra["digest_tum"],
                                  "digest_search": kt_sonra["digest_search"],
                                  "plan_digest": kt_sonra["plan_digest"],
                                  "equity_digest": kt_sonra["equity_digest"],
                                  "oos_score": kt_sonra["oos_score"],
                                  "para_v3_search": kt_sonra["para_search"],
                                  "n_trades_total": kt_sonra["n_trades_total"],
                                  "net_usd": kt_sonra["replay_defteri"]["net_usd"]},
    }
    # ikinci kapı: referans limitsiz kol ↔ karne_olcum `e1_oncesi_icra` (ESKİ motor 505603b)
    ko = json.loads((KO / "sonuc.json").read_text())
    ko_dig = ko["kol_digest_matrisi"]["e1_oncesi_icra"]
    kapi2 = {
        "iddia": ("ref_limitsiz, karne_olcum `e1_oncesi_icra` kolunun BUGÜNKÜ motordaki "
                  "karşılığıdır; fark BEKLENİR ve tek kalemdir: replay-PIT düzeltmesi "
                  "(89d4497) — karne_tazeleme §3.1'de MMM tek işlemi olarak ölçüldü"),
        "ref_limitsiz_digest": {k: t["ref_limitsiz"][k] for k in
                                ("digest_tum", "digest_search", "plan_digest", "equity_digest")},
        "karne_olcum_e1_oncesi_icra_digest": {k: v[:16] for k, v in ko_dig.items()},
        "digest_esit": (t["ref_limitsiz"]["digest_tum"] == ko_dig["digest_tum"][:16]),
        "iddia_entry_missed_limit_sifir": t["ref_limitsiz"]["ret_nedenleri"].get(
            "entry_missed_limit", 0),
    }
    # ESKİ MOTOR (505603b) LİMİTSİZ KOLU — karne_olcum `e1_oncesi_icra`nın BİREBİR yeniden üretimi.
    # Varsa: (a) o kolun digest'ini doğrular, (b) `ref_limitsiz` ile arasındaki TEK değişken
    # (motor: 505603b → HEAD) ölçülmüş olur.
    eski_p = SB / "eski_motor" / "kol_e1oncesi_eski.json"
    if eski_p.exists():
        e = json.loads(eski_p.read_text())
        eim = e["imza"]
        ed = defter(e)
        kapi2["eski_motor_kolu"] = {
            "amac": ("karne_olcum `e1_oncesi_icra` kolunun BİREBİR yeniden üretimi: 505603b motoru "
                     "+ o ölçümün 2026-08-01 state'i + AYNI bayrak (limit_pct_cap 0,01→0,10). "
                     "Eski motor replay'de `fill_entry`e atr GEÇİRMEZ, bu yüzden atr_mult atıldır."),
            "motor": e["motor"], "entry_law": e["entry_law"],
            "digest": {"digest_tum": eim["trade_digest_tum"][:16],
                       "digest_search": eim["trade_digest_search"][:16],
                       "plan_digest": eim["plan_digest"][:16],
                       "equity_digest": eim["equity_digest"][:16]},
            "karne_olcum_ile_digest_esit": all(
                eim[a][:16] == ko_dig[b][:16] for a, b in
                (("trade_digest_tum", "digest_tum"), ("trade_digest_search", "digest_search"),
                 ("plan_digest", "plan_digest"), ("equity_digest", "equity_digest"))),
            "skorlar": {"oos_score": eim["oos_score"], "is_score": eim["is_score"],
                        "para_search": eim["para_search"],
                        "n_trades_total": eim["n_trades_total"], "oos_n": eim["oos_n"],
                        "net_usd": ed["net_usd"], "dolum": [e["dolum"]["dolan_n"],
                                                            e["dolum"]["cagri_n"]],
                        "ret_nedenleri": e["dolum"]["ret_nedenleri"]},
            "karne_olcum_kayitli": {"oos_score": ko["karne"]["e1_oncesi_icra"]["oos_score"],
                                    "is_score": ko["karne"]["e1_oncesi_icra"]["is_score"],
                                    "para_v3_search": ko["karne"]["e1_oncesi_icra"]["para_v3_search"],
                                    "n_trades_total": ko["karne"]["e1_oncesi_icra"]["n_trades_total"],
                                    "oos_n": ko["karne"]["e1_oncesi_icra"]["oos_n"]},
            "MOTOR_FARKI_eski_vs_bugun": {
                "n_trades_total": [eim["n_trades_total"], t["ref_limitsiz"]["n_trades_total"]],
                "oos_score": [eim["oos_score"], t["ref_limitsiz"]["oos_score"]],
                "is_score": [eim["is_score"], t["ref_limitsiz"]["is_score"]],
                "para_search": [eim["para_search"], t["ref_limitsiz"]["para_v3_search"]],
                "net_usd": [ed["net_usd"], t["ref_limitsiz"]["net_usd"]],
                "karartma_vetosu_plan_n": [
                    sum(1 for p in (e.get("_plan_log") or [])
                        if any("kazanç öncesi karartma" in str(r)
                               for r in (p.get("gate_reasons") or []))),
                    t["ref_limitsiz"]["karartma_vetosu_plan_n"]],
                "islem_kumesi": None},
        }
        A = {(x.get("ticker"), str(x.get("ts_open"))[:10]) for x in e["_trades_tum"]}
        B = {(x.get("ticker"), str(x.get("ts_open"))[:10])
             for x in kol("ref_limitsiz")["_trades_tum"]}
        kapi2["eski_motor_kolu"]["MOTOR_FARKI_eski_vs_bugun"]["islem_kumesi"] = {
            "yalniz_eski_n": len(A - B), "yalniz_bugun_n": len(B - A), "ortak_n": len(A & B),
            "yalniz_eski": sorted(f"{a}@{b}" for a, b in A - B)[:30],
            "yalniz_bugun": sorted(f"{a}@{b}" for a, b in B - A)[:30]}
    else:
        kapi2["eski_motor_kolu"] = {"olculdu": False,
                                    "neden": "eski motor kolu bu turda koşulmadı/bitmedi"}
    out["determinizm_kapisi"] = {"birincil_b_mkt": kapi, "ikincil_ref_limitsiz": kapi2}

    # ---------- MOTOR DAMGASI (bayt eşitlik) ----------
    r = subprocess.run(["diff", "-rq", "--exclude=__pycache__", str(DEPO / "meridian"),
                        str(SB / "meridian")], capture_output=True, text=True)
    r2 = subprocess.run(["diff", "-rq", "--exclude=__pycache__", str(DEPO / "meridian"),
                         str(ESKI_SB / "motor_guncel" / "meridian")], capture_output=True,
                        text=True)
    out["motor_damgasi"] = {
        "sandbox_vs_depo_diff_rc": r.returncode, "sandbox_vs_depo_cikti": r.stdout.strip(),
        "depo_vs_karne_tazeleme_motoru_diff_rc": r2.returncode,
        "kod_damgasi": json.loads((SB / "kod_damgasi.json").read_text()),
    }

    # ---------- GAP BACAĞI: yapısal gözlem (iddia değil ölçüm) ----------
    ciftler = [("a_mkt", "a_cnl"), ("b_mkt", "b_cnl"), ("c_mkt", "c_cnl")]
    out["gap_bacagi"] = {
        "olcum": {f"{x}_vs_{y}": {
            "digest_tum_esit": t[x]["digest_tum"] == t[y]["digest_tum"],
            "plan_digest_esit": t[x]["plan_digest"] == t[y]["plan_digest"],
            "equity_digest_esit": t[x]["equity_digest"] == t[y]["equity_digest"],
            "net_usd": [t[x]["net_usd"], t[y]["net_usd"]],
            "dolmama_orani": [t[x]["dolmama_orani"], t[y]["dolmama_orani"]],
            "entry_gap_veto_reddi": [t[x]["ret_nedenleri"].get("entry_gap_veto", 0),
                                     t[y]["ret_nedenleri"].get("entry_gap_veto", 0)]}
            for x, y in ciftler},
        "gap_at_submit_dagilimi": {a: t[a]["gap_gozlemi"] for a in GRID + REF},
        "kaynak": ("replay `fill_entry`e `gap_at_submit` GEÇİRMEZ (backtest.py:232-236 argüman "
                   "listesi) → argüman None → `broker.fill_entry` gap vetosu dalına giremez. "
                   "broker.py bunu BEYAN EDİLMİŞ kapsam farkı olarak yazar."),
    }

    # ---------- KAÇAN DOLUMLARIN LİMİTSİZ KOLDAKİ KARŞILIĞI ----------
    ref = kol("ref_limitsiz")
    out["kacan_dolum_eslesmesi"] = {a: kacan_eslesmesi(a, ref) for a in GRID}

    # ---------- KILL#1 SATIRI (sayı, hüküm cümlesi YOK) ----------
    out["kill1_dolmama_vs_esik"] = {
        "esik": KILL1,
        "tanim": ("kart kill_criteria[0]: 'dolum oranını kabul edilebilir tutamıyorsa "
                  "(dolmama >%40)'. Payda = fill_entry çağrısına ulaşan plan sayısı."),
        "hucreler": {a: {"dolmama_orani": t[a]["dolmama_orani"],
                         "esik_farki": t[a]["dolmama_esik_farki"],
                         "esigin_ustunde_mi": (None if t[a]["dolmama_orani"] is None
                                               else t[a]["dolmama_orani"] > KILL1),
                         "cagri_n": t[a]["cagri_n"], "dolmayan_n": t[a]["dolmayan_n"],
                         "yalniz_limit_orani": t[a]["dolmama_orani_yalniz_limit"]}
                     for a in GRID + REF},
    }

    # ---------- E2 / ölçülemeyenler ----------
    out["olculemedi"] = {
        "E2_gercek_slipaj": ("None — canlı dolum verisi ister (fill − resmî açılış). Bu ölçüm "
                             "replay defteridir; `alpaca_fill_price` 95/95 satırda YOK, "
                             "`analytics.pessimistic_band_update` ampirik bandı hâlâ None "
                             "döndürür (n_dolan eşiği dolmadı)."),
        "kaçan_planların_gerçek_getirisi": ("None — kaçan plan HİÇ AÇILMADI; bu raporda yalnız "
                                            "(a) ham barlardan hipotetik ileri-getiri ve "
                                            "(b) limitsiz kolun yol-bağımlı defteri var."),
    }

    (SB / "sonuc_e1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    # --- konsol özeti ---
    print(f"{'kol':14s} {'dolan/cagri':12s} {'dolmama':8s} {'net$':10s} {'kotumser$':11s} "
          f"{'PARA-v3':9s} {'oos':8s} {'n':5s} {'mtmDD':7s} digest")
    for s in tablo:
        print(f"{s['kol']:14s} {str(s['dolan_n'])+'/'+str(s['cagri_n']):12s} "
              f"{str(s['dolmama_orani']):8s} {str(s['net_usd']):10s} "
              f"{str(s['net_usd_kotumser']):11s} {str(s['para_v3_search']):9s} "
              f"{str(s['oos_score']):8s} {str(s['n_trades_total']):5s} "
              f"{str(s['mtm_max_dd_tam_pencere']):7s} {s['digest_tum'][:12]}")
    print("\nDETERMİNİZM b_mkt:", kapi["digest_esit"], kapi["skor_esit"])
    print("ref_limitsiz entry_missed_limit:", kapi2["iddia_entry_missed_limit_sifir"])
    print("GAP çiftleri:", {k: v["digest_tum_esit"] for k, v in out["gap_bacagi"]["olcum"].items()})


if __name__ == "__main__":
    main()
