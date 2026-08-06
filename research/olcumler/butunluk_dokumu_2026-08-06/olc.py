#!/usr/bin/env python3
"""olc.py — bütünlük dökümünün ÖLÇÜM KODU (RAPOR.md'nin tekrar-üretilebilirlik ayağı).

EDG-016 DERSİ: "measured" statüsü kanıt + damga + KOD üçlüsü depoya girince tamamdır — damga kodsuz
yaşayamaz. Bu betik, RAPOR.md'deki her sayının nereden geldiğini tek komutla yeniden üretir.

SALT OKUMA. Canlıya ssh YOK, üretim state'ine yazım YOK: girdi, Mac'teki A1 yedeğinden
(`backups/a1/state-YYYY-MM-DD.tar.gz`) geçici bir dizine açılmış state KOPYASIDIR ve tüm dedektörler
`persist=False` ile koşar (taban ilerletilmez — `/api/diagnostics`in kendi kuralıyla aynı).

KULLANIM:
    mkdir -p /tmp/bd && tar -xzf backups/a1/state-2026-08-04.tar.gz -C /tmp/bd
    MERIDIAN_ROOT=/tmp/bd python research/olcumler/butunluk_dokumu_2026-08-06/olc.py

ÖLÇÜM PENCERESİNİN DÜRÜST SINIRI: yedek 2026-08-05T02:33 (Mac çekimi) ile alınmıştır ve içindeki
`events.jsonl` son satırı 2026-08-04T23:28:53Z'dir. 2026-08-05 ve 2026-08-06 canlı olayları BU
ÖLÇÜMDE YOKTUR; operatörün 24 saatlik alarm dağılımı o pencerenin DIŞINDADIR ve rapor bunu her
sayıda açıkça belirtir.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import os
import sys


def _iso(ts):
    return None if not ts else dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    if not os.environ.get("MERIDIAN_ROOT"):
        print("MERIDIAN_ROOT ayarlanmadı — CANLI state'e koşmayı reddediyorum (salt-okuma sözleşmesi)",
              file=sys.stderr)
        return 2
    from meridian import store, watchdog

    out: dict = {"olcum_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "kaynak": os.environ["MERIDIAN_ROOT"]}

    # ---- 1) YEDİ DEDEKTÖR (persist=False — taban ilerletilmez) ---------------------------------
    rep = watchdog.integrity_report(persist=False)
    out["integrity"] = rep
    out["ozet"] = {
        "starved": [s["name"] for s in rep["production"].get("starved") or []],
        "askida": [s["name"] for s in rep["production"].get("askida") or []],
        "conservation_unexplained": rep["conservation"].get("unexplained"),
        "coherence_stale": rep["coherence"].get("stale"),
        "monotonicity_regressions": rep["monotonicity"].get("regressions"),
        "ownership_lost": rep["ownership"].get("lost"),
        "parity_dusen": [r["check"] for r in rep["parity"].get("rows", []) if not r.get("ok")],
    }

    # ---- 2) MANDAL (hangi ihlaller ALARMLANMIŞ hâlde duruyor) ----------------------------------
    out["latch"] = store.read_json("integrity_alarmed.json", [])

    # ---- 3) ALARM DAĞILIMI (olay defterinden; mandal geçişleri değil ALARM satırları) -----------
    tok, mech, gaps, daymech = (collections.Counter() for _ in range(4))
    n_rows, son = 0, None
    for line in open(os.path.join(os.environ["MERIDIAN_ROOT"], "state", "events.jsonl")):
        try:
            e = json.loads(line)
        except ValueError:  # sessiz-yutma DEĞİL: bozuk satır sayılır ve raporun sonunda yazılır
            out["bozuk_satir"] = out.get("bozuk_satir", 0) + 1
            continue
        n_rows += 1
        son = e.get("ts") or son
        a = e.get("alarm")
        if not a:
            continue
        tok[a] += 1
        if a == "MECHANISM_STALE":
            m = e.get("mechanism") or e.get("kind") or "?"
            mech[m] += 1
            daymech[(str(e.get("ts"))[:10], m)] += 1
            if e.get("gap_h") is not None:
                gaps[(m, round(float(e["gap_h"]), 1))] += 1
    out["defter"] = {"satir": n_rows, "son_ts": son}
    out["alarm"] = {"jetonlar": dict(tok), "mechanism_stale_dagilimi": dict(mech.most_common()),
                    "gun_x_mekanizma": {f"{d}|{m}": c for (d, m), c in sorted(daymech.items())},
                    "gap_dagilimi": {f"{m}|{g}": c for (m, g), c in gaps.most_common()}}

    # ---- 4) TÜREV BAYATLIĞININ KAYNAK DAMGALARI (arka-uçtan bağımsız) --------------------------
    out["damgalar"] = {n: _iso(store.mtime(n)) for n in
                       ("scoreboard.json", "hypotheses.jsonl", "self_review.json",
                        "score_calibration.json", "near_miss.json", "trades.jsonl",
                        "trade_plans.jsonl", "counterfactuals.jsonl")}

    # ---- 5) KURAKLIK SINIFININ ÖLÇÜMÜ (eleme defteri — "üretmiyor" mu "sayamıyor" mu) ----------
    sv = store.read_json("sieve.json", {}) or {}
    out["eleme"] = {k: v for k, v in sv.items()
                    if k in ("shadow_model.terfi", "llm_opinion_calibration.gercek",
                             "component_ic.eslesme", "threshold_curve.eslesme")}
    out["llm_calibration"] = {k: v for k, v in (store.read_json("llm_calibration.json", {}) or {}).items()
                              if k in ("n_pairs", "cf_pairs", "n_plans_with_opinion",
                                       "last_opinion_plan_date")}
    sm = store.read_json("shadow_model.json", {}) or {}
    out["shadow_model"] = {"n_fit": sm.get("n_fit"), "brier_train": sm.get("brier_train"),
                           "fit_ts": sm.get("fit_ts"), "fit_attempt_ts": sm.get("fit_attempt_ts"),
                           "fit_fingerprint_var": sm.get("fit_fingerprint") is not None,
                           "kaynak_generated": (sm.get("_kaynak") or {}).get("generated"),
                           "promotion": sm.get("promotion")}
    out["brain_cooldown"] = store.read_json("brain_cooldown.json", {})

    json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=str)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
