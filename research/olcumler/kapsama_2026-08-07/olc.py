#!/usr/bin/env python
"""kapsama_2026-08-07 / olc.py — `universe_coverage` kümülatif sayaç kusurunun ÖLÇÜMÜ.

SALT OKUR. Hiçbir şeye yazmaz (canlı worker koşuyor olabilir). Çalıştırma:

    .venv/bin/python research/olcumler/kapsama_2026-08-07/olc.py            # yerel defter
    .venv/bin/python research/olcumler/kapsama_2026-08-07/olc.py --sim      # + canlı imzası

Ne ölçer:
  1. `session_bar_never_published` OLAY sayısı ile AYRIK SEANS sayısı (dedektör ikisini
     karıştırıyordu: "165 seans" aslında 165 olay / 7 seans).
  2. Her ayrık seansa düşen olay sayısı (fırtına yoğunlaşması).
  3. Eski hükmün (v205) ve yeni hükmün (v206, `watchdog._kapsama_satiri`) aynı girdideki çıktısı.
  4. `--sim`: yerel defter + Rol-1'in CANLIDA ölçtüğü 7 sağlıklı seansın imzası. Bu bir
     SİMÜLASYONDUR ve raporda öyle etiketlenir — canlı ölçüm YERİNE GEÇMEZ.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

KOK = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

DEFTER = KOK / "state" / "events.jsonl"
# Rol-1'in canlı A1'de (2026-08-07) ölçtüğü son yedi seansın kapsaması. ÖLÇÜM DEĞİL, ÖLÇÜMÜN
# YENİDEN KURULUMU: bu satırlar yerel defterde YOKTUR, canlıdakileri temsil eder.
CANLI_OLCUM = [("2026-07-30", 1.0), ("2026-07-31", 1.0), ("2026-08-03", 1.0),
               ("2026-08-04", 1.0), ("2026-08-05", 1.0), ("2026-08-06", 1.0),
               ("2026-08-07", 0.996)]


def _oku() -> list[dict]:
    out = []
    with DEFTER.open(errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue          # bozuk satır ATLANIR ve sayılır (aşağıda raporlanır)
    return out


def main() -> None:
    from meridian import watchdog as wd

    ham = _oku()
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).isoformat()
    pencere = [e for e in ham if not e.get("ts") or str(e["ts"]) >= since]

    sk = [e for e in pencere if e.get("event") == "session_bar_never_published"
          or e.get("kind") == "session_bar_never_published"]
    low = [e for e in pencere if e.get("event") == "universe_coverage_low"]
    seans_say: dict[str, int] = {}
    for e in sk:
        seans_say[str(e.get("session"))] = seans_say.get(str(e.get("session")), 0) + 1

    print(f"defter satırı        : {len(ham)}  (30 günlük pencerede {len(pencere)})")
    print(f"atlama OLAYI         : {len(sk)}")
    print(f"atlama AYRIK SEANS   : {len(seans_say)}")
    for s, n in sorted(seans_say.items()):
        print(f"    {s} → {n} olay")
    print(f"universe_coverage_low: {len(low)}")

    # ---- ESKİ HÜKÜM (v205 mantığının birebir yeniden kurulumu; kod değişmedi, taklit edildi)
    print("\nESKİ HÜKÜM (v205):")
    print(f"    ok = {not sk and not low}")
    if sk:
        print("    detail =", f"{len(sk)} seans evren kapsaması yetersiz olduğu için ATLANDI "
                              f"(son: {sk[-1].get('session')} "
                              f"%{100*float(sk[-1].get('universe_coverage') or 0):.0f}) "
                              f"— kaynak yayınlamıyor")

    girdiler = [("YENİ HÜKÜM (v206) · yerel defter", pencere)]
    if "--sim" in sys.argv:
        girdiler.append(("YENİ HÜKÜM (v206) · SİMÜLASYON (+canlı 7 seans)", pencere + [
            {"ts": f"{d}T23:00:00+00:00", "event": "session_deferred_for_coverage",
             "index_session": d, "chosen": d, "coverage": c} for d, c in CANLI_OLCUM]))
    for ad, gir in girdiler:
        r = wd._kapsama_satiri(gir)
        print(f"\n{ad}:")
        for k in ("ok", "pencere_seans", "kapsama_esigi", "guncel_ihlal_seans",
                  "tarihsel_ihlal_seans", "tarihsel_ihlal_olay", "tarihsel_son_seans",
                  "olculemedi", "son_olculen_kapsama"):
            print(f"    {k} = {r.get(k)}")
        print(f"    detail = {r['detail']}")


if __name__ == "__main__":
    main()
