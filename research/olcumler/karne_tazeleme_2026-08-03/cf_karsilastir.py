"""cf defteri ÖNCE/SONRA — üç defter: canlı snapshot (state/counterfactuals.jsonl, 2026-07-30),
cf_taban (ESKİ kod: takvim vetosu AÇIK), cf_guncel (kardeş-PIT düzeltmesi UYGULANMIŞ).
Yalnız okuma/kıyas; ölçüm motoru `cf_backfill.run`dur ve o zaten koştu."""
from __future__ import annotations

import collections
import json
import pathlib

KT = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/erdemozturk/AI-Trading")


def oku(p: pathlib.Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def ozet(rows: list[dict], ad: str) -> dict:
    v = collections.Counter(r.get("verdict") for r in rows)
    rs = [float(r["r_multiple"]) for r in rows if r.get("r_multiple") is not None]
    plan = [r for r in rows if r.get("verdict") in ("GO", "REVIEW", "NO_GO")]
    tarih = sorted({r.get("date") for r in rows if r.get("date")})
    ex = collections.Counter(r.get("exit_reason") for r in rows if r.get("exit_reason"))
    return {"defter": ad, "n_satir": len(rows), "n_plan_satiri": len(plan),
            "n_near_miss": v.get("NEAR_MISS", 0),
            "verdict": dict(v), "taken": sum(1 for r in rows if r.get("taken")),
            "entered": sum(1 for r in rows if r.get("entered")),
            "n_r": len(rs), "ort_r": round(sum(rs) / len(rs), 4) if rs else None,
            "kazanan_oran": round(sum(1 for x in rs if x > 0) / len(rs), 4) if rs else None,
            "toplam_r": round(sum(rs), 2) if rs else None,
            "ilk_tarih": tarih[0] if tarih else None, "son_tarih": tarih[-1] if tarih else None,
            "n_gun": len(tarih), "exit_reason": dict(ex)}


def main() -> None:
    canli = oku(REPO / "state" / "counterfactuals.jsonl")
    taban = oku(KT / "cf_taban" / "state_cf" / "counterfactuals.jsonl")
    guncel = oku(KT / "cf_guncel" / "state_cf" / "counterfactuals.jsonl")
    out = {"ozetler": [ozet(canli, "canli_snapshot_2026-07-30"),
                       ozet(taban, "cf_taban_ESKI_KOD"),
                       ozet(guncel, "cf_guncel_KARDES_PIT")]}

    # --- TEK-DEĞİŞKEN A/B: iki yeniden-türetim AYNI kodla koştu, TEK fark takvim vetosu ---
    ta = {r["id"]: r for r in taban}
    gu = {r["id"]: r for r in guncel}
    ortak = sorted(set(ta) & set(gu))
    fark = [{"id": i, "ticker": ta[i].get("ticker"), "date": ta[i].get("date"),
             "taban_verdict": ta[i].get("verdict"), "guncel_verdict": gu[i].get("verdict"),
             "taban_taken": ta[i].get("taken"), "guncel_taken": gu[i].get("taken")}
            for i in ortak
            if ta[i].get("verdict") != gu[i].get("verdict") or ta[i].get("taken") != gu[i].get("taken")]
    out["ab_tek_degisken"] = {
        "ortak_id": len(ortak), "yalniz_taban": len(set(ta) - set(gu)),
        "yalniz_guncel": len(set(gu) - set(ta)),
        "farkli_satir_n": len(fark), "farkli_satirlar": fark[:60],
        "taban_sayaci": json.loads((KT / "cf_taban" / "cf_sonuc_2022-01-01_2026-07-30.json").read_text()
                                   ).get("earnings_gate")
        if (KT / "cf_taban" / "cf_sonuc_2022-01-01_2026-07-30.json").exists() else None,
        "guncel_sayaci": json.loads((KT / "cf_guncel" / "cf_sonuc_2022-01-01_2026-07-30.json").read_text()
                                    ).get("earnings_gate")
        if (KT / "cf_guncel" / "cf_sonuc_2022-01-01_2026-07-30.json").exists() else None,
    }
    for ad in ("cf_taban", "cf_guncel"):
        p = KT / ad / "cf_sonuc_2022-01-01_2026-07-30.json"
        if p.exists():
            d = json.loads(p.read_text())
            out.setdefault("kosum_ozetleri", {})[ad] = {
                k: d.get(k) for k in ("sessions", "opened", "resolved", "still_open",
                                      "earnings_gate", "sure_sn")}
            out["kosum_ozetleri"][ad]["bars_integrity"] = {
                k: (d.get("bars_integrity") or {}).get(k)
                for k in ("ledger_symbols", "rows_excluded", "ledger_rev", "generated_at")}
            out["kosum_ozetleri"][ad]["bars_integrity"]["uygulanan_sembol_n"] = len(
                (d.get("bars_integrity") or {}).get("applied") or {})
    (KT / "cf_karsilastirma.json").write_text(json.dumps(out, ensure_ascii=False, indent=1,
                                                         default=str))
    print(json.dumps({"ozetler": out["ozetler"],
                      "ab": {k: v for k, v in out["ab_tek_degisken"].items()
                             if k != "farkli_satirlar"},
                      "kosum": out.get("kosum_ozetleri")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
