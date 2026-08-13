"""EDG-036b — CANLI SALT-OKUMA ÇIKARIMI (A1'de stdin ile koşar; DİSKE TEK BAYT YAZMAZ).

`ssh -i key ubuntu@IP 'python3 -' < uzak_saltokuma.py > cikti.b64` deseniyle çalışır:
betik uzak diske YAZILMAZ, yalnız stdout'a gzip+base64 JSON basar.

DB `mode=ro` URI ile açılır. `meridian.store` KULLANILMAZ (store.read_* → db_backed() →
bayat-defter süzgeci `.migrated` yeniden adlandırması yapabilir = YAZIM).
SIR DIŞLAMASI: auth.json + token/secret/key/cred adı geçen dosyalar ASLA okunmaz.
"""
import base64
import gzip
import json
import os
import sqlite3
import sys

STATE = "/opt/meridian/state"
DB = os.path.join(STATE, "meridian.db")

# boyut/alaka dışı bırakılanlar (defter ölçümüne girmez) + SIR dosyaları
DISLA_TAM = {
    "events.jsonl", "dashboard.log", "intraday_decisions.jsonl", "probe_cache.json",
    "massive_grouped_last.json", "inc_cache.json", "agent_calls.jsonl", "agent_traces.jsonl",
    "bar_same_evening.json", "meridian.db", "meridian.db-wal", "meridian.db-shm",
    "meridian.db.yedek", "barsarchive.log",
    "auth.json",                       # SIR — okunmaz
}
DISLA_PARCA = ("secret", "token", "credential", "cred_", "apikey", "api_key", "password", ".env")
MAX_BAYT = 6_000_000                   # tek dosya tavanı (defterler bunun altında)

out = {"_beyan": "SALT-OKUMA. Uzak diske hiçbir yazım yapılmadı; DB mode=ro.",
       "state": STATE}

# ---- 1) DB: şema + satırlar (mode=ro) ---------------------------------------------------------
con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
con.row_factory = sqlite3.Row
out["db_tablolar"] = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
out["sema"] = {}
for tbl in ("trades", "trade_plans"):
    out["sema"][tbl] = [{"cid": r[0], "ad": r[1], "tip": r[2], "notnull": r[3], "pk": r[5]}
                        for r in con.execute("PRAGMA table_info(%s)" % tbl)]

dump = {}
for tbl, ad in (("trades", "trades"), ("trade_plans", "plans")):
    rows = []
    for r in con.execute("SELECT * FROM %s ORDER BY rowid" % tbl):
        d = dict(r)
        d.pop("seq", None)
        ex = d.pop("extra_json", None)
        if ex:
            try:
                d.update(json.loads(ex))
            except Exception:
                pass
        rows.append({k: v for k, v in d.items() if v is not None})
    dump[ad] = rows
for tbl, ad in (("scoreboard", "scoreboard"), ("portfolio", "portfolio"),
                ("shadow_books", "shadow_books")):
    try:
        r = con.execute("SELECT doc_json FROM %s LIMIT 1" % tbl).fetchone()
        dump[ad] = json.loads(r[0]) if r else None
    except Exception as e:
        dump[ad] = {"_okunamadi": "%s: %s" % (type(e).__name__, e)}
dump["equity"] = {"points": [[r[0], r[1]] for r in
                             con.execute("SELECT ts, equity FROM equity_curve ORDER BY rowid")]}
con.close()
out["dump"] = dump

# ---- 2) CANLI trade_plans ALAN MUHASEBESİ (ham; hüküm YOK) ------------------------------------
plans = dump["plans"]
alan = {}
for p in plans:
    for k, v in p.items():
        b = alan.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}})
        b["var"] += 1
        if v is not None:
            b["dolu"] += 1
        b["tipler"][type(v).__name__] = b["tipler"].get(type(v).__name__, 0) + 1
out["plan_alan_sayimi"] = alan
out["plan_n"] = len(plans)
out["trade_n"] = len(dump["trades"])
# kaynak kırılımı (varsa) — tohum/canlı ayrımı plan defterinde de var mı?
kir = {}
for p in plans:
    k = str(p.get("kaynak"))
    kir[k] = kir.get(k, 0) + 1
out["plan_kaynak_kirilimi"] = kir
sv = {}
for p in plans:
    k = "sv=%s" % p.get("strategy_version")
    sv[k] = sv.get(k, 0) + 1
out["plan_sv_kirilimi"] = sv
out["plan_ornek_satir"] = plans[-1] if plans else None
out["plan_ornek_satir_ilk"] = plans[0] if plans else None

# ---- 3) STATE metin dosyaları (defter ölçümünün sandbox tabanı) --------------------------------
dosyalar = {}
atlanan = []
for ad in sorted(os.listdir(STATE)):
    p = os.path.join(STATE, ad)
    if not os.path.isfile(p):
        continue
    dad = ad.lower()
    if ad in DISLA_TAM or any(x in dad for x in DISLA_PARCA):
        atlanan.append({"ad": ad, "neden": "dışlama listesi (boyut/alaka/SIR)"})
        continue
    try:
        sz = os.path.getsize(p)
    except OSError as e:
        atlanan.append({"ad": ad, "neden": "stat: %s" % e})
        continue
    if sz > MAX_BAYT:
        atlanan.append({"ad": ad, "neden": "boyut %d > tavan %d" % (sz, MAX_BAYT)})
        continue
    try:
        with open(p, "rb") as f:
            dosyalar[ad] = base64.b64encode(f.read()).decode()
    except Exception as e:
        atlanan.append({"ad": ad, "neden": "okuma: %s: %s" % (type(e).__name__, e)})
out["dosyalar_b64"] = dosyalar
out["dosya_atlanan"] = atlanan
out["dosya_n"] = len(dosyalar)

ham = json.dumps(out, default=str).encode()
sys.stdout.write(base64.b64encode(gzip.compress(ham, 6)).decode())
