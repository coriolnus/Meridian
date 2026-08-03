"""ÖNCE/SONRA + FARK-ATFI derleyicisi. Kollar `kosum.py`nin (karne_olcum harness'i) çıktısıdır;
burada YALNIZ okuma/kıyas var — ikinci bir ölçüm motoru YOK."""
from __future__ import annotations

import collections
import json
import pathlib

KT = pathlib.Path(__file__).resolve().parent
OLD = KT.parent / "karne_olcum"


def kol(p: pathlib.Path) -> dict:
    return json.loads(p.read_text())


def para(d: dict) -> dict:
    sd = (d.get("para") or {}).get("search_detail") or {}
    ru = sd.get("realized_usd") or {}
    return {"para_v3_search": sd.get("score"), "pnl_usd": ru.get("pnl_usd"),
            "hedef_usd": ru.get("hedef_usd"), "span_days": sd.get("span_days"),
            "total_return": sd.get("total_return"), "max_drawdown": sd.get("max_drawdown"),
            "kirpildi": ru.get("kirpildi"), "n": sd.get("n")}


def defter(d: dict) -> dict:
    t = d.get("_trades_tum") or []
    pn = [x["pnl_dollars"] for x in t if x.get("pnl_dollars") is not None]
    g = [x for x in pn if x > 0]
    l = [x for x in pn if x < 0]
    return {"n": len(t), "n_pnl": len(pn), "net_usd": round(sum(pn), 2) if pn else None,
            "profit_factor": round(sum(g) / abs(sum(l)), 4) if l else None,
            "n_kazanan": len(g), "n_kaybeden": len(l),
            "friksiyon_usd": round(sum(x.get("costs") or 0 for x in t), 2) if t else None}


def satir(ad: str, d: dict) -> dict:
    im = d["imza"]
    return {"kol": ad, "motor": d["motor"], "state": d["state_dizini"],
            "sure_sn": d["sure_sn"], "olcum_zamani": d["olcum_zamani"],
            "heat_hard_r": ((d.get("goal_limits") or {}).get("heat_hard_r")),
            **{k: im[k] for k in ("oos_score", "para_search", "n_trades_total", "oos_n",
                                  "search_n", "confirm_n", "avg_r", "win_rate", "sharpe",
                                  "max_drawdown", "total_return", "is_score", "holdout_score")},
            "digest_tum": im["trade_digest_tum"][:16],
            "digest_search": im["trade_digest_search"][:16],
            "plan_digest": im["plan_digest"][:16], "equity_digest": im["equity_digest"][:16],
            "para_detay": para(d), "replay_defteri": defter(d),
            "equity_tam": d.get("equity_tam"), "equity_oos": d.get("equity_oos"),
            "full_detail": d.get("full_detail"),
            "mtm_max_dd": (d.get("mtm_dd_veto") or {}).get("max_mtm_dd"),
            "fold_avg_r_mean": d.get("fold_avg_r_mean")}


def main() -> None:
    kollar = {
        "ONCE_2026-08-01_rapor": kol(OLD / "kol_tam_guncel.json"),
        "taban_yeniden": kol(KT / "motor_taban" / "kol_taban.json"),
        "atrsiz": kol(KT / "motor_atrsiz" / "kol_atrsiz.json"),
        "heat45": kol(KT / "motor_guncel" / "kol_heat45.json"),
        "SONRA_guncel": kol(KT / "motor_guncel" / "kol_guncel.json"),
    }
    tablo = [satir(ad, d) for ad, d in kollar.items()]
    out = {"tablo": tablo}

    # --- DETERMİNİZM KAPISI: taban_yeniden, 2026-08-01 raporunun kolunu birebir üretmeli ---
    a, b = kollar["ONCE_2026-08-01_rapor"]["imza"], kollar["taban_yeniden"]["imza"]
    out["determinizm"] = {
        "digest_esit": all(a[k] == b[k] for k in ("trade_digest_tum", "trade_digest_search",
                                                  "plan_digest", "equity_digest")),
        "skor_esit": all(a[k] == b[k] for k in ("oos_score", "para_search", "n_trades_total",
                                                "oos_n", "is_score")),
        "farklar": {k: [a[k], b[k]] for k in a if a[k] != b[k]},
    }

    def d(x, y, alan):
        va, vb = x.get(alan), y.get(alan)
        if va is None or vb is None:
            return None
        return round(vb - va, 6)

    t = {s["kol"]: s for s in tablo}
    ALAN = ("oos_score", "para_search", "is_score", "n_trades_total", "oos_n", "search_n",
            "avg_r", "win_rate", "sharpe", "max_drawdown", "total_return")
    out["fark_atfi"] = {
        "REPLAY-PIT (taban_yeniden -> atrsiz; ikisi de ATR'siz, tek fark karartma vetosu)":
            {k: d(t["taban_yeniden"], t["atrsiz"], k) for k in ALAN},
        "E1 ATR BACAGI (atrsiz -> heat45; tek fark fill_entry'ye atr= gecmesi)":
            {k: d(t["atrsiz"], t["heat45"], k) for k in ALAN},
        "TOPLAM (taban_yeniden -> SONRA_guncel)":
            {k: d(t["taban_yeniden"], t["SONRA_guncel"], k) for k in ALAN},
        "KOD+diger (taban_yeniden -> heat45)":
            {k: d(t["taban_yeniden"], t["heat45"], k) for k in ALAN},
        "ISI 4,5R->5,0R (heat45 -> SONRA_guncel)":
            {k: d(t["heat45"], t["SONRA_guncel"], k) for k in ALAN},
    }
    out["defter_farki"] = {
        "REPLAY-PIT": {k: d(t["taban_yeniden"]["replay_defteri"], t["atrsiz"]["replay_defteri"], k)
                       for k in ("n", "net_usd", "profit_factor", "friksiyon_usd")},
        "E1_ATR": {k: d(t["atrsiz"]["replay_defteri"], t["heat45"]["replay_defteri"], k)
                   for k in ("n", "net_usd", "profit_factor", "friksiyon_usd")},
        "TOPLAM": {k: d(t["taban_yeniden"]["replay_defteri"], t["SONRA_guncel"]["replay_defteri"], k)
                   for k in ("n", "net_usd", "profit_factor", "friksiyon_usd")},
        "KOD+diger": {k: d(t["taban_yeniden"]["replay_defteri"], t["heat45"]["replay_defteri"], k)
                      for k in ("n", "net_usd", "profit_factor", "friksiyon_usd")},
        "ISI": {k: d(t["heat45"]["replay_defteri"], t["SONRA_guncel"]["replay_defteri"], k)
                for k in ("n", "net_usd", "profit_factor", "friksiyon_usd")},
    }
    # --- İŞLEM KÜMESİ AYRIŞMASI: hangi işlemler geldi/gitti (atfın nerede doğduğu) ---
    def anahtar(ts):
        return {(x.get("ticker"), str(x.get("ts_open"))[:10]) for x in ts}
    for ad_a, ad_b, etiket in (("taban_yeniden", "atrsiz", "REPLAY-PIT"),
                               ("atrsiz", "heat45", "E1_ATR"),
                               ("taban_yeniden", "heat45", "KOD"),
                               ("heat45", "SONRA_guncel", "ISI"),
                               ("taban_yeniden", "SONRA_guncel", "TOPLAM")):
        A = anahtar(kollar[ad_a]["_trades_tum"])
        B = anahtar(kollar[ad_b]["_trades_tum"])
        out.setdefault("islem_kume_farki", {})[etiket] = {
            "yalniz_once_n": len(A - B), "yalniz_sonra_n": len(B - A), "ortak_n": len(A & B),
            "yalniz_once": sorted(f"{a}@{b}" for a, b in A - B)[:40],
            "yalniz_sonra": sorted(f"{a}@{b}" for a, b in B - A)[:40]}
    # --- REPLAY-PIT'İN DOĞRUDAN ÖLÇÜSÜ: taban kolunda kaç plan takvim vetosu yedi ---
    for ad, d_ in kollar.items():
        pl = d_.get("_plan_log") or []
        VETO = "kazanç öncesi karartma"          # kapsam NOTU da 'karartma' der; TAM metin aranır
        kara = [p for p in pl
                if any(VETO in str(r) for r in (p.get("gate_reasons") or []))]
        notu = sum(1 for p in pl
                   if any("earnings_kapsami_yok" in str(r) for r in (p.get("gate_reasons") or [])))
        isi = sum(1 for p in pl
                  if any("sert tavanı" in str(r) for r in (p.get("gate_reasons") or [])))
        vd = collections.Counter(p.get("gate_verdict") for p in pl)
        out.setdefault("takvim_vetosu", {})[ad] = {
            "plan_n": len(pl), "karartma_VETOSU_plan_n": len(kara),
            "kapsam_notu_plan_n": notu, "isi_sert_tavan_gerekce_n": isi,
            "verdict_dagilimi": dict(vd),
            "ornekler": [f"{p.get('id')}|{p.get('gate_verdict')}" for p in kara][:20]}
    (KT / "karsilastirma.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                      default=str))
    print(json.dumps({"determinizm": out["determinizm"]["digest_esit"],
                      "fark_atfi": out["fark_atfi"],
                      "defter_farki": out["defter_farki"],
                      "islem_kume": {k: {kk: vv for kk, vv in v.items() if kk.endswith("_n")}
                                     for k, v in out["islem_kume_farki"].items()}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
