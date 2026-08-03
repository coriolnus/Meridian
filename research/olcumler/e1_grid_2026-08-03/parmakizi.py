"""GERÇEK state/ parmak izi — koşumlardan ÖNCE ve SONRA. Salt-ölçüm kanıtı.
karne_tazeleme_2026-08-03 desenının aynısı: dosya yolu -> (mtime_ns, boyut)."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

GERCEK = pathlib.Path("/Users/erdemozturk/AI-Trading/state")
OUT = pathlib.Path(__file__).resolve().parent


def parmak() -> dict:
    d = {}
    for p in sorted(GERCEK.rglob("*")):
        if p.is_symlink() or not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        d[str(p.relative_to(GERCEK))] = [st.st_mtime_ns, st.st_size]
    return d


def sha(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def main() -> None:
    faz = sys.argv[1]
    now = parmak()
    if faz == "once":
        (OUT / "state_parmakizi_once.json").write_text(
            json.dumps({"parmak": now, "sha": sha(now), "n": len(now)}, indent=1))
        print(json.dumps({"faz": "once", "n": len(now), "sha": sha(now)}))
        return
    before = json.loads((OUT / "state_parmakizi_once.json").read_text())
    old = before["parmak"]
    degisen = {k: [old[k], now[k]] for k in old if k in now and old[k] != now[k]}
    out = {"dosya_once": len(old), "dosya_simdi": len(now), "degisen": degisen,
           "yeni": sorted(set(now) - set(old)), "silinen": sorted(set(old) - set(now)),
           "sha_once": before["sha"], "sha_simdi": sha(now)}
    (OUT / "state_parmakizi_sonra.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "degisen"} |
                     {"degisen_n": len(degisen)}, indent=1))


if __name__ == "__main__":
    main()
