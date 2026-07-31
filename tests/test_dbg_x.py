import json, sys
sys.path.insert(0, "/Users/erdemozturk/AI-Trading/tests")
from meridian import config, storage, dbmigrate
import test_storage_v142 as T

def test_dbg(sandbox_state):
    T._seed_files(sandbox_state)
    gercek = storage.read_entity
    def _bozuk(name):
        out = gercek(name)
        return out[:-1] if name == "trades.jsonl" and isinstance(out, list) else out
    storage.read_entity = _bozuk
    r = dbmigrate.apply()
    storage.read_entity = gercek
    print("ok:", r["ok"], r.get("hata"))
    c = storage.connect()
    print("dbpath:", storage.db_path(), "exists:", storage.db_path().exists())
    print("conn file:", list(c.execute("PRAGMA database_list")))
    print("tablolar:", [x["name"] for x in c.execute("SELECT name FROM sqlite_master")])
    print("conns:", list(storage._CONNS))
    storage.close_all()
