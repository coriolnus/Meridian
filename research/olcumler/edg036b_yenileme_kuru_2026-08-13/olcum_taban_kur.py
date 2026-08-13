"""EDG-036b — canlı SALT-OKUMA dökümünden YEREL izole sandbox tabanı kurar.

Girdi : uzak_saltokuma.py'nin gzip+base64 stdout'u (canlı diske hiçbir yazım yapılmadı)
Çıktı : <sandbox>/base/  — canlı state'in dosya-çağı kopyası (DB YOK; store dosya modunda koşar)

Bu betik CANLIYA DOKUNMAZ. Yalnız yerel dosya yazar.
kullanım: olcum_taban_kur.py <dump.b64> <sandbox_kok>
"""
import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

DUMP = Path(sys.argv[1])
SB = Path(sys.argv[2])
BASE = SB / "base"
BASE.mkdir(parents=True, exist_ok=True)

d = json.loads(gzip.decompress(base64.b64decode(DUMP.read_text())))

# 1) düz state dosyaları (SIR dosyaları uzakta zaten dışlandı)
n = 0
for ad, b64 in d["dosyalar_b64"].items():
    (BASE / ad).write_bytes(base64.b64decode(b64))
    n += 1

# 2) DB'den türetilen defterler — DOSYA ÇAĞI (MERIDIAN_DB=off ile store bunları okur)
dump = d["dump"]


def wjsonl(ad, rows):
    (BASE / ad).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


wjsonl("trades.jsonl", dump["trades"])
wjsonl("trade_plans.jsonl", dump["plans"])
for ad, obj in (("scoreboard.json", dump["scoreboard"]), ("portfolio.json", dump["portfolio"]),
                ("shadow_books.json", dump["shadow_books"]), ("equity_curve.json", dump["equity"])):
    (BASE / ad).write_text(json.dumps(obj, ensure_ascii=False))
(BASE / "bars").mkdir(exist_ok=True)
(BASE / "history").mkdir(exist_ok=True)

# 3) künye — hangi canlı hâlin kopyası?
kunye = {
    "kaynak": "ubuntu@130.61.126.87:/opt/meridian/state (SALT-OKUMA, DB mode=ro)",
    "dosya_n": n, "atlanan": d["dosya_atlanan"],
    "trades_n": len(dump["trades"]), "plans_n": len(dump["plans"]),
    "trades_sha256": hashlib.sha256((BASE / "trades.jsonl").read_bytes()).hexdigest(),
    "plans_sha256": hashlib.sha256((BASE / "trade_plans.jsonl").read_bytes()).hexdigest(),
    "canli_trade_plans_sema": d["sema"]["trade_plans"],
    "canli_trades_sema": d["sema"]["trades"],
    "plan_alan_sayimi": d["plan_alan_sayimi"],
    "plan_kaynak_kirilimi": d["plan_kaynak_kirilimi"],
    "plan_sv_kirilimi": d["plan_sv_kirilimi"],
    "portfolio_realized_pnl": (dump["portfolio"] or {}).get("realized_pnl"),
}
(SB / "taban_kunye.json").write_text(json.dumps(kunye, ensure_ascii=False, indent=1, default=str))
print(json.dumps({k: v for k, v in kunye.items()
                  if k not in ("canli_trade_plans_sema", "canli_trades_sema",
                               "plan_alan_sayimi", "atlanan")},
                 ensure_ascii=False, indent=1))
print("base:", BASE)
