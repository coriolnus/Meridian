"""WP3/28d · CANLI Ağustos rejim-olay izleri (SALT-OKUMA; emsal exe007). Soru: canlı sistem
2026-08-01→22 arasında kendini HANGİ rejimde gördü (TESHIS 08-13'te 'canlı rejim chop' diyordu)?
events.jsonl'daki rejim taşıyan olaylar + regime.json'ın o pencerede aldığı değerler (varsa
history). Yazma yok."""
import json
cikti = {"olaylar": [], "_hata": None}
try:
    for line in open("state/events.jsonl"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ts = str(e.get("ts", ""))
        if ts >= "2026-07-25" and ("regime" in e or "chop" in json.dumps(e)[:400]):
            cikti["olaylar"].append({"ts": ts, "event": e.get("event"),
                                     "regime": e.get("regime"),
                                     "detail": str(e.get("detail", ""))[:80]})
except Exception as ex:
    cikti["_hata"] = f"{type(ex).__name__}: {ex}"
cikti["olaylar"] = cikti["olaylar"][-120:]
print(json.dumps(cikti))
