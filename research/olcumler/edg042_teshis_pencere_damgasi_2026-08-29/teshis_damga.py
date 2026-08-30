# TEŞHİS (ölçüm DEĞİL, karta işlenmez): E2 K1 satırlarının `pencere` damgası ile
# dolumun DEFTERE YAZILDIĞI an tutuyor mu? Salt-okuma; hiçbir şey yazılmaz.
import json
from meridian import store
rows = store.read_jsonl("entry_execution.jsonl")
k1 = [r for r in rows if r.get("motor") == "ayna" and r.get("karar") == "submitted"
      and r.get("fill") is not None]
alan = ("date", "ticker", "pencere", "fill_kaydedildi", "ts", "fill_status")
print(json.dumps({"n": len(k1),
                  "satirlar": [{k: r.get(k) for k in alan} for r in k1]}, ensure_ascii=False))
