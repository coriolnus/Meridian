"""cf defteri YENİDEN-TÜRETİMİ — deponun kendi yolu (`cf_backfill.run`), sandbox state'e.
Argümanlar: start end (YYYY-MM-DD). Yeni ölçüm motoru YOK; yalnız üretim fonksiyonu çağrılır."""
from __future__ import annotations
import datetime as dt, json, os, pathlib, sys

SANDBOX = pathlib.Path(__file__).resolve().parent
os.environ["MERIDIAN_ROOT"] = str(SANDBOX)
sys.path.insert(0, str(SANDBOX))
from meridian import config                                   # noqa: E402
config.STATE = SANDBOX / "state_cf"
config.HISTORY = config.STATE / "history"
config.BARS = config.STATE / "bars"
config.HISTORY.mkdir(parents=True, exist_ok=True)
from meridian import cf_backfill                              # noqa: E402
assert str(pathlib.Path(cf_backfill.__file__).resolve()).startswith(str(SANDBOX)), "YANLIŞ MOTOR"

start, end = (sys.argv[1] if len(sys.argv) > 1 else None), (sys.argv[2] if len(sys.argv) > 2 else None)
t0 = dt.datetime.now()
out = cf_backfill.run(start=start, end=end, progress_every=50)
out["sure_sn"] = round((dt.datetime.now() - t0).total_seconds(), 1)
out["start"], out["end"] = start, end
out["motor"] = str(pathlib.Path(cf_backfill.__file__).resolve())
(SANDBOX / f"cf_sonuc_{start}_{end}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
print("CF BİTTİ", json.dumps({k: v for k, v in out.items() if k != "bars_integrity"}, ensure_ascii=False, default=str), flush=True)
