"""storage.py — DEFTER ÇEKİRDEĞİNİN SQLite ARKA UCU (WP-H/H9, Kademe A).

NEDEN VAR. Bugüne kadar altı defter dosyaydı (JSON/JSONL) ve `store.py` onları atomik yazıyordu.
Atomiklik TEK bir yazım için doğruydu ama şu iki sınıf açıktı:

  * OKU-DEĞİŞTİR-YAZ yarışı SÜREÇLER ARASINDA: `store.file_lock` bir `threading.RLock`tur, yani
    YALNIZ aynı süreçte anlam taşır. Canlı worker + pano API + sprint AYNI dosyaya yazabiliyordu;
    kaybeden yazım hiçbir yerde görünmüyordu (bu depoda belgeli tehlike sınıfı).
  * JSONL EKLEME ATOMİK DEĞİLDİ: çökme ya da disk dolması yarım satır bırakır; `store.read_jsonl`
    o satırı sessizce eler (`jsonl_rows_skipped` uyarısı bunu SAYAR ama kaybı geri getirmez).

SQLite ikisini de YAPISAL olarak kapatır: tek transaction + WAL + süreçler-arası kilit çekirdeğin
kendisindedir. Kazanç ŞEMA DEĞİL, ATOMİKLİK + SÜREÇLER-ARASI KİLİTtir — bu yüzden tekil-belgeler
(scoreboard/portfolio/shadow_books) tek-satır-belge tablosudur; aşırı-normalizasyon yapılmadı.

DIŞ İMZALAR DEĞİŞMEZ. Bu modülü uygulama kodu DOĞRUDAN çağırmaz; `store.py` altı defter adını
buraya yönlendirir ve çağıranlar bugünkü dict/list yapılarını almaya devam eder. Bu bir DEPOLAMA
migrasyonudur, davranış migrasyonu DEĞİL.

ANAHTARLAMA KAPISI (`active`). DB YOKSA her şey eskisi gibi dosyadan okur/yazar. DB `dbmigrate`
ile DOĞDUĞU an altı defter DB'ye geçer. Yani kod dağıtımı ile veri geçişi AYRI iki olaydır:
Rol-1 bakım penceresinde `python -m meridian.dbmigrate --uygula` koşana kadar davranış birebir
bugünküdür. `MERIDIAN_DB=off` acil geri dönüş anahtarıdır (dosyalar `.migrated` ekiyle DURUYOR).

YOL ÇAĞRI ANINDA ÇÖZÜLÜR. `config.STATE` ölçüm sandbox'larında (testler, sprint, mutasyon)
değiştirilir; modül yükleme anında yol dondurmak o sandbox'ları KIRAR — bu yüzden `db_path()`
her çağrıda `config.STATE`i okur ve bağlantı havuzu YOLA göre anahtarlanır.

TİP KORUMA (parite sözleşmesi). Tipli kolonlar sorgulanabilirlik içindir; DOĞRULUK kaynağı
değildir. Bir alanın Python tipi kolonun beklediğinden farklıysa (ör. `score` int beklenirken
float gelirse) alan AYRICA `extra_json`a yazılır ve okumada `extra_json` KAZANIR. Böylece
SQLite'ın tip afinitesi (60 → 60.0 dönüşümü) sessizce veriyi değiştiremez: parite digesti
`dbmigrate`de bunu ölçer ve eşleşmezse migrasyon BAŞARISIZ sayılır.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from . import config

DB_NAME = "meridian.db"
SCHEMA_VERSION = 1

# ---- VARLIK KAYDI ------------------------------------------------------------------------------
# Kanonik dosya adı → (tablo, tür). Tür üç değerlidir:
#   "rows"   : satır-tabanlı defter (JSONL) — tipli kolonlar + extra_json
#   "doc"    : tekil belge (JSON)          — tek satır (id=1), doc_json + updated_at
#   "series" : nokta serisi (JSON zarfı)   — tipli kolonlar + zarfın kalanı entity_meta.env_json'da
TRADES = "trades.jsonl"
PLANS = "trade_plans.jsonl"
SCOREBOARD = "scoreboard.json"
PORTFOLIO = "portfolio.json"
EQUITY = "equity_curve.json"
SHADOW_BOOKS = "shadow_books.json"

# Tipli kolonlar. Tipler CANLI defterden ÖLÇÜLDÜ (2026-07-31, state/trades.jsonl 95 satır ×
# state/trade_plans.jsonl 390 satır — her alanın tipi tek değerliydi), uydurulmadı. Ölçüm dışı
# kalan alanlar (skill_chain, targets, gate_checks, …) extra_json'da yaşar: sözleşme (ledgers.py)
# onları serbest bırakır ve tipli bir kolona zorlamak şemayı defterin kendisinden daha katı yapardı.
_COLS: dict[str, tuple[tuple[str, str], ...]] = {
    TRADES: (
        ("id", "TEXT"), ("plan_id", "TEXT"), ("ticker", "TEXT"), ("side", "TEXT"),
        ("ts_open", "TEXT"), ("ts_close", "TEXT"),
        ("entry", "REAL"), ("exit", "REAL"), ("qty", "INTEGER"),
        ("r_multiple", "REAL"), ("r_multiple_expected", "REAL"),
        ("pnl_pct", "REAL"), ("pnl_dollars", "REAL"), ("costs", "REAL"),
        ("exit_reason", "TEXT"), ("strategy_version", "INTEGER"),
        ("regime", "TEXT"), ("setup", "TEXT"), ("score", "INTEGER"),
        ("exploration", "BOOL"), ("scaled_out", "BOOL"),
        ("bars_held", "INTEGER"), ("mfe_r", "REAL"), ("mae_r", "REAL"),
        # `kaynak` = ledgerstamp'in KAYNAK DAMGASI (live_paper | replay_seed | belirsiz). Canlı
        # deftere HENÜZ basılmadı (BT-1 migrasyonu Rol-1'de) — kolon boş kalır, uydurulmaz.
        ("kaynak", "TEXT"),
    ),
    PLANS: (
        ("id", "TEXT"), ("date", "TEXT"), ("ticker", "TEXT"), ("side", "TEXT"),
        ("entry_trigger", "REAL"), ("stop", "REAL"), ("profit_target", "REAL"),
        ("size_r", "REAL"), ("r_multiple_expected", "REAL"),
        ("regime_at_plan", "TEXT"), ("strategy_version", "INTEGER"),
        ("sector", "TEXT"), ("score", "INTEGER"), ("setup", "TEXT"),
        ("gate_verdict", "TEXT"), ("broker_status", "TEXT"),
        ("dormant_setup", "BOOL"), ("exploration", "BOOL"), ("p_win_shadow", "REAL"),
    ),
    EQUITY: (("ts", "TEXT"), ("equity", "REAL")),
}

_TABLE = {TRADES: "trades", PLANS: "trade_plans", SCOREBOARD: "scoreboard",
          PORTFOLIO: "portfolio", EQUITY: "equity_curve", SHADOW_BOOKS: "shadow_books"}
_KIND = {TRADES: "rows", PLANS: "rows", EQUITY: "series",
         SCOREBOARD: "doc", PORTFOLIO: "doc", SHADOW_BOOKS: "doc"}

ENTITIES: tuple[str, ...] = (TRADES, PLANS, SCOREBOARD, PORTFOLIO, EQUITY, SHADOW_BOOKS)
ROW_ENTITIES = tuple(n for n in ENTITIES if _KIND[n] == "rows")
DOC_ENTITIES = tuple(n for n in ENTITIES if _KIND[n] == "doc")


def table_of(name: str) -> str | None:
    return _TABLE.get(name)


def kind_of(name: str) -> str | None:
    return _KIND.get(name)


# ---- BAĞLANTI ----------------------------------------------------------------------------------
# TEK BAĞLANTI, TEK KİLİT. sqlite3 bağlantısı iş parçacıkları arasında paylaşılabilir ama
# EŞZAMANLI kullanılamaz; `check_same_thread=False` + süreç-içi RLock bunu sağlar. SÜREÇLER arası
# eşzamanlılık WAL + busy_timeout'un işidir (çekirdeğin kendisi, bizim değil).
_CONNS: dict[str, sqlite3.Connection] = {}
_GUARD = threading.RLock()
_SCHEMA_OK: set = set()

PRAGMAS = (("journal_mode", "wal"), ("synchronous", "normal"),
           ("busy_timeout", 5000), ("foreign_keys", 1))


def db_path() -> Path:
    """DB yolu — HER ÇAĞRIDA `config.STATE`ten türetilir (sandbox'lar STATE'i değiştirir)."""
    return Path(config.STATE) / DB_NAME


def _dict_row(cursor, row):
    return {d[0]: row[i] for i, d in enumerate(cursor.description)}


def connect(path: Path | str | None = None, *, create: bool = False) -> sqlite3.Connection:
    """Süreç başına (ve YOL başına) tek bağlantı. PRAGMA'lar bağlantı ömrü boyunca geçerlidir.

    `create=False` VARSAYILANDIR VE BİR SİGORTADIR. `sqlite3.connect` var olmayan bir yolu SESSİZCE
    YARATIR; yanlış bir okuma yolu (ya da sandbox'sız bir test) canlı `state/`e BOŞ bir
    `meridian.db` bırakabilirdi. O dosya bir kez doğduğunda `active()` onu görür ve — şeması
    tamamlanmışsa — uygulama defterleri BOŞ okumaya başlar: migrasyon yapılmadan yapılmış gibi
    görünen bir geçiş, en tehlikeli hâl. Yaratma yetkisi YALNIZ `dbmigrate`/`ensure_schema`
    yolundadır; okuma yolları `active()` kapısından geçtiği için dosya zaten VARdır."""
    p = Path(path) if path is not None else db_path()
    key = str(p)
    with _GUARD:
        conn = _CONNS.get(key)
        if conn is not None:
            return conn
        if create:
            p.parent.mkdir(parents=True, exist_ok=True)
        elif not p.exists():
            raise FileNotFoundError(
                f"SQLite defteri yok: {p} — `connect(create=True)` yalnız migrasyon yolunundur. "
                f"Okuma yolları `storage.active()` kapısından geçmeli.")
        conn = sqlite3.connect(key, check_same_thread=False, isolation_level=None, timeout=5.0)
        conn.row_factory = _dict_row
        for pragma, val in PRAGMAS:
            conn.execute(f"PRAGMA {pragma}={val}")
        _CONNS[key] = conn
        return conn


def pragma_state(conn: sqlite3.Connection | None = None) -> dict:
    """Açık PRAGMA'ların CANLI değeri — iddia değil ölçüm (testin okuduğu yüzey)."""
    c = conn or connect()
    out = {}
    with _GUARD:
        for p, _ in PRAGMAS:
            row = c.execute(f"PRAGMA {p}").fetchone()
            # Sütun adı PRAGMA adıyla AYNI DEĞİLDİR (`busy_timeout` → `timeout`); ada göre
            # okumak KeyError verirdi. Tek sütunlu sonuç: ilk değeri al.
            out[p] = None if not row else next(iter(row.values()))
    return out


def close_all() -> None:
    """Tüm bağlantıları kapat (testler ve sandbox söküm yolları için)."""
    with _GUARD:
        for c in _CONNS.values():
            try:
                c.close()
            except sqlite3.Error:  # sessiz-yutma: kapatma sırasında düşen bağlantı zaten kullanılamaz durumda; kapatma denemesi çağıranı düşüremez ve açık kalan tanıtıcıyı süreç sonu toplar
                pass
        _CONNS.clear()
        _SCHEMA_OK.clear()


# ---- ŞEMA --------------------------------------------------------------------------------------
def _ddl() -> list[str]:
    out = ["CREATE TABLE IF NOT EXISTS schema_version ("
           "  version INTEGER NOT NULL,"
           "  applied_at REAL NOT NULL)",
           # entity_meta: her varlığın DAMGASI. Üç işi var ve üçü de dosya çağında MTIME'ın
           # yaptığı işti: (a) `present` — belge VAR mı yok mu (boş belge ile yok olan belge AYNI
           # şey değildir), (b) `rev`/`updated_at` — önbellek anahtarı ve tazelik ölçümü
           # (analytics._nd_stamp, shadow_model.dataset_fingerprint, watchdog.coherence_report),
           # (c) `env_json` — equity_curve zarfının points DIŞINDAKİ anahtarları.
           "CREATE TABLE IF NOT EXISTS entity_meta ("
           "  entity TEXT PRIMARY KEY,"
           "  present INTEGER NOT NULL DEFAULT 0,"
           "  rev INTEGER NOT NULL DEFAULT 0,"
           "  updated_at REAL NOT NULL DEFAULT 0,"
           "  n INTEGER NOT NULL DEFAULT 0,"
           "  env_json TEXT,"
           "  migrated_at REAL,"
           "  source_digest TEXT)"]
    for name in ENTITIES:
        tbl, kind = _TABLE[name], _KIND[name]
        if kind == "doc":
            out.append(f"CREATE TABLE IF NOT EXISTS {tbl} ("
                       f"  id INTEGER PRIMARY KEY CHECK (id = 1),"
                       f"  doc_json TEXT NOT NULL,"
                       f"  updated_at REAL NOT NULL)")
            continue
        cols = ",".join(f'  "{c}" {t if t != "BOOL" else "INTEGER"}' for c, t in _COLS[name])
        out.append(f"CREATE TABLE IF NOT EXISTS {tbl} ("
                   f"  seq INTEGER PRIMARY KEY,"
                   f"{cols},"
                   f"  extra_json TEXT)")
    out += [
        "CREATE INDEX IF NOT EXISTS ix_trades_plan_id ON trades(plan_id)",
        "CREATE INDEX IF NOT EXISTS ix_trades_ts_close ON trades(ts_close)",
        "CREATE INDEX IF NOT EXISTS ix_trades_version ON trades(strategy_version)",
        "CREATE INDEX IF NOT EXISTS ix_plans_id ON trade_plans(id)",
        "CREATE INDEX IF NOT EXISTS ix_plans_date ON trade_plans(date)",
        "CREATE INDEX IF NOT EXISTS ix_equity_ts ON equity_curve(ts)",
    ]
    return out


def ensure_schema(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """İdempotent şema kurulumu + sürüm damgası. DB dosyasını YARATMA yetkisi olan tek yol."""
    c = conn or connect(create=True)
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            for stmt in _ddl():
                c.execute(stmt)
            row = c.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
            if row is None or row["v"] is None:
                c.execute("INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                          (SCHEMA_VERSION, time.time()))
            for name in ENTITIES:
                c.execute("INSERT OR IGNORE INTO entity_meta(entity, present, rev, updated_at, n) "
                          "VALUES (?, 0, 0, 0, 0)", (name,))
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
    _SCHEMA_OK.add(str(db_path()))
    return c


def schema_version(conn: sqlite3.Connection | None = None) -> int | None:
    c = conn or connect()
    try:
        with _GUARD:
            row = c.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        return None if row is None else row["v"]
    except sqlite3.DatabaseError:  # sessiz-yutma: tablo yoksa/dosya DB değilse SÜRÜM YOKTUR ve dönen None tam olarak bunu söyler — çağıran (active) bunu "DB devrede değil" diye okur, varsayılan bir sürüm UYDURULMAZ
        return None


def disabled_by_env() -> bool:
    """`MERIDIAN_DB=off` acil geri dönüş anahtarı: DB dosyası dursa bile dosya yoluna dönülür."""
    return os.environ.get("MERIDIAN_DB", "").strip().lower() in ("0", "off", "false", "no")


def active(name: str | None = None) -> bool:
    """Bu varlık ŞU AN DB'den mi okunuyor? (DB dosyası yoksa: HAYIR — davranış birebir bugünkü.)"""
    if name is not None and name not in _TABLE:
        return False
    if disabled_by_env():
        return False
    p = db_path()
    key = str(p)
    if not p.exists():
        _SCHEMA_OK.discard(key)
        return False
    if key in _SCHEMA_OK:
        return True
    if schema_version(connect(p)) is None:
        return False
    if len(_SCHEMA_OK) > 64:        # sandbox'lar süreç ömrü boyunca birikmesin
        _SCHEMA_OK.clear()
    _SCHEMA_OK.add(key)
    return True


# ---- SATIR ↔ KOLON ÇEVİRİSİ --------------------------------------------------------------------
def _matches(val: Any, typ: str) -> bool:
    if typ == "BOOL":
        return isinstance(val, bool)
    if typ == "INTEGER":
        return isinstance(val, int) and not isinstance(val, bool)
    if typ == "REAL":
        return isinstance(val, float)
    return isinstance(val, str)


def _scalar(val: Any) -> bool:
    return val is None or isinstance(val, (str, int, float, bool))


def _row_to_cols(name: str, row: dict) -> tuple[list, str | None]:
    """Satır → (kolon değerleri, extra_json). Tip uymazsa alan AYRICA extra_json'a düşer ve
    okumada extra KAZANIR — SQLite tip afinitesi veriyi sessizce değiştiremesin diye."""
    spec = _COLS[name]
    known = {c for c, _ in spec}
    vals: list = []
    extra = {k: v for k, v in row.items() if k not in known}
    for col, typ in spec:
        if col not in row:
            vals.append(None)
            continue
        v = row[col]
        if _matches(v, typ):
            vals.append(int(v) if typ == "BOOL" else v)
        else:
            # Tip uyuşmuyor: kolona (sorgulanabilirlik için) skalerse yine yaz, DOĞRULUĞU
            # extra_json taşısın. Skaler değilse kolon NULL kalır — sqlite3 liste/sözlük kabul etmez.
            vals.append(v if _scalar(v) and not isinstance(v, bool) else None)
            extra[col] = v
    return vals, (json.dumps(extra, ensure_ascii=False) if extra else None)


def _cols_to_row(name: str, rec: dict) -> dict:
    spec = _COLS[name]
    out: dict = {}
    for col, typ in spec:
        v = rec.get(col)
        if v is None:
            continue
        out[col] = bool(v) if typ == "BOOL" else v
    raw = rec.get("extra_json")
    if raw:
        try:
            out.update(json.loads(raw))
        except json.JSONDecodeError:  # sessiz-yutma: SESSİZ DEĞİL — bozuk extra tek satırın SERBEST alanlarını düşürür, tipli kolonlar (defterin sözleşmeli alanları) yerinde kalır ve `dbmigrate` parite digesti bunu koşuda ölçüp migrasyonu düşürür
            pass
    return out


# ---- SATIR DEFTERLERİ --------------------------------------------------------------------------
def _touch(conn, name: str, *, n: int, present: bool = True, env: dict | None = None) -> None:
    conn.execute("UPDATE entity_meta SET present=?, rev=rev+1, updated_at=?, n=?, "
                 "env_json=COALESCE(?, env_json) WHERE entity=?",
                 (1 if present else 0, time.time(), int(n),
                  json.dumps(env, ensure_ascii=False) if env is not None else None, name))


def read_rows(name: str, limit: int | None = None) -> list[dict]:
    tbl = _TABLE[name]
    c = connect()
    with _GUARD:
        if limit:
            recs = c.execute(f"SELECT * FROM {tbl} ORDER BY seq DESC LIMIT ?", (int(limit),)).fetchall()
            recs.reverse()
        else:
            recs = c.execute(f"SELECT * FROM {tbl} ORDER BY seq").fetchall()
    return [_cols_to_row(name, r) for r in recs]


def append_row(name: str, row: dict) -> None:
    tbl = _TABLE[name]
    cols = [c for c, _ in _COLS[name]]
    vals, extra = _row_to_cols(name, row)
    ph = ",".join("?" * (len(cols) + 1))
    q = f'INSERT INTO {tbl} ({",".join(chr(34) + c + chr(34) for c in cols)},extra_json) VALUES ({ph})'
    c = connect()
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            c.execute(q, (*vals, extra))
            n = c.execute(f"SELECT COUNT(*) AS n FROM {tbl}").fetchone()["n"]
            _touch(c, name, n=n)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise


def do_replace_rows(c: sqlite3.Connection, name: str, rows: list[dict]) -> int:
    """TRANSACTION YÖNETMEZ — çağıran açar/kapatır. `dbmigrate` altı varlığı TEK transaction'da
    taşıyabilsin diye ayrıldı: parite digesti tutmazsa hepsi birlikte geri alınır."""
    tbl = _TABLE[name]
    cols = [c2 for c2, _ in _COLS[name]]
    ph = ",".join("?" * (len(cols) + 1))
    q = f'INSERT INTO {tbl} ({",".join(chr(34) + x + chr(34) for x in cols)},extra_json) VALUES ({ph})'
    payload = []
    for r in rows:
        vals, extra = _row_to_cols(name, r)
        payload.append((*vals, extra))
    c.execute(f"DELETE FROM {tbl}")
    c.executemany(q, payload)
    _touch(c, name, n=len(payload))
    return len(payload)


def replace_rows(name: str, rows: list[dict]) -> None:
    """Defterin TAMAMINI tek transaction'da değiştirir (`store.write_jsonl` karşılığı)."""
    c = connect()
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            do_replace_rows(c, name, rows)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise


# ---- TEKİL BELGELER ----------------------------------------------------------------------------
def read_doc(name: str) -> Any:
    """Belge ya da YOK ise `None`. "Boş belge" ile "belge yok" ayrı hâllerdir: ikincisinde çağıran
    kendi varsayılanını kullanır (bugünkü `store.read_json(name, default)` sözleşmesi)."""
    tbl = _TABLE[name]
    c = connect()
    with _GUARD:
        rec = c.execute(f"SELECT doc_json FROM {tbl} WHERE id=1").fetchone()
    if rec is None:
        return None
    try:
        return json.loads(rec["doc_json"])
    except json.JSONDecodeError:  # sessiz-yutma: SESSİZ DEĞİL — çağıran (store.read_json) None'ı varsayılana çevirir ve `state_file_unreadable` uyarısı dosya yolundakiyle AYNI kanaldan basılır; burada ikinci bir uyarı log seli olurdu
        return None


def do_write_doc(c: sqlite3.Connection, name: str, doc: Any) -> None:
    """TRANSACTION YÖNETMEZ — bkz. `do_replace_rows` gerekçesi."""
    tbl = _TABLE[name]
    c.execute(f"INSERT INTO {tbl}(id, doc_json, updated_at) VALUES (1, ?, ?) "
              f"ON CONFLICT(id) DO UPDATE SET doc_json=excluded.doc_json, "
              f"updated_at=excluded.updated_at",
              (json.dumps(doc, ensure_ascii=False), time.time()))
    _touch(c, name, n=1)


def write_doc(name: str, doc: Any) -> None:
    c = connect()
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            do_write_doc(c, name, doc)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise


# ---- SERİ (equity_curve) -----------------------------------------------------------------------
POINTS_KEY = "points"


def read_series(name: str = EQUITY) -> Any:
    """Zarf + noktalar → bugünkü `{"version": …, "points": [[ts, equity], …]}` sözlüğü."""
    tbl = _TABLE[name]
    c = connect()
    with _GUARD:
        meta = c.execute("SELECT present, env_json FROM entity_meta WHERE entity=?",
                         (name,)).fetchone()
        recs = c.execute(f"SELECT * FROM {tbl} ORDER BY seq").fetchall()
    if meta is None or not meta["present"]:
        return None
    env = {}
    if meta["env_json"]:
        try:
            env = json.loads(meta["env_json"])
        except json.JSONDecodeError:  # sessiz-yutma: zarf okunamadıysa NOKTALAR yine döner (eğrinin kendisi kaybolmaz) ve eksik zarf anahtarı `dbmigrate` parite digestinde ölçülür — burada uyarı basmak okuma yolunu her çağrıda kirletirdi
            env = {}
    pts = []
    for r in recs:
        if r.get("extra_json"):
            try:
                pts.append(json.loads(r["extra_json"]))
                continue
            except json.JSONDecodeError:  # sessiz-yutma: ham nokta okunamadı — aşağıdaki tipli kolonlara düşülür; nokta KAYBOLMAZ, en kötü ihtimalle serbest biçimi yiter ve parite digesti bunu koşuda düşürür
                pass
        pts.append([r.get("ts"), r.get("equity")])
    return {**env, POINTS_KEY: pts}


def do_write_series(c: sqlite3.Connection, doc: Any, name: str = EQUITY) -> int:
    """TRANSACTION YÖNETMEZ — bkz. `do_replace_rows` gerekçesi."""
    tbl = _TABLE[name]
    env = {k: v for k, v in (doc or {}).items() if k != POINTS_KEY}
    pts = list((doc or {}).get(POINTS_KEY) or [])
    payload = []
    for p in pts:
        if isinstance(p, (list, tuple)) and len(p) == 2 and isinstance(p[0], str) \
                and isinstance(p[1], float):
            payload.append((p[0], p[1], None))
        else:
            ts = p[0] if isinstance(p, (list, tuple)) and p and isinstance(p[0], str) else None
            eq = p[1] if isinstance(p, (list, tuple)) and len(p) > 1 and isinstance(p[1], (int, float)) \
                and not isinstance(p[1], bool) else None
            payload.append((ts, eq, json.dumps(p, ensure_ascii=False)))
    c.execute(f"DELETE FROM {tbl}")
    c.executemany(f"INSERT INTO {tbl}(ts, equity, extra_json) VALUES (?,?,?)", payload)
    _touch(c, name, n=len(payload), env=env)
    return len(payload)


def write_series(doc: Any, name: str = EQUITY) -> None:
    c = connect()
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            do_write_series(c, doc, name)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise


# ---- ORTAK YÜZEY (store.py buradan çağırır) ----------------------------------------------------
def read_entity(name: str) -> Any:
    kind = _KIND[name]
    if kind == "doc":
        return read_doc(name)
    if kind == "series":
        return read_series(name)
    return read_rows(name)


def write_entity(name: str, payload: Any) -> None:
    kind = _KIND[name]
    if kind == "doc":
        write_doc(name, payload)
    elif kind == "series":
        write_series(payload, name)
    else:
        replace_rows(name, payload)


def meta(name: str) -> dict | None:
    """Varlığın damgası: {present, rev, updated_at, n, migrated_at, source_digest, env_json}.

    SÜTUN LİSTESİ ELLE YAZILMAZ (`SELECT *`): elle yazılan liste eskir ve eksik sütun SESSİZCE
    None döner — ilk sürümde `source_digest` tam olarak böyle kayboldu, `--durum` raporunda
    "kaynak digesti yok" diye okundu ve migrasyonun kendi kanıtı görünmez oldu."""
    c = connect()
    with _GUARD:
        rec = c.execute("SELECT * FROM entity_meta WHERE entity=?", (name,)).fetchone()
    return rec


def stamp(name: str) -> tuple | None:
    """Dosya çağındaki `(mtime_ns, size)` demetinin DB karşılığı: `(updated_at_ns, rev)`.
    İçeriği DEĞİŞMEDEN damganın değişmemesi tek şarttır (önbellek anahtarı olarak kullanılıyor)."""
    m = meta(name)
    if m is None:
        return None
    return (int(float(m["updated_at"]) * 1e9), int(m["rev"]))


def backup_to(hedef: Path | str) -> Path:
    """TUTARLI kopya — `sqlite3` çevrimiçi yedek API'siyle.

    NEDEN DOSYA KOPYALAMAK YETMEZ: WAL modunda defterin bir kısmı `-wal` dosyasındadır. `tar`/`cp`
    ile alınan bir kopya, `-wal` olmadan EKSİK ve `-wal` ile birlikte alınsa bile YARIŞLI olur
    (kopyalama sırasında checkpoint çalışabilir). Yedeğin sessizce eksik olması, yedek olmamasından
    daha kötüdür: geri yükleme gününe kadar görünmez."""
    src = connect()
    p = Path(hedef)
    p.parent.mkdir(parents=True, exist_ok=True)
    dst = sqlite3.connect(str(p))
    try:
        with _GUARD:
            src.backup(dst)
    finally:
        dst.close()
    return p


def mark_migrated(name: str, *, digest: str, conn: sqlite3.Connection | None = None) -> None:
    c = conn or connect()
    c.execute("UPDATE entity_meta SET migrated_at=?, source_digest=? WHERE entity=?",
              (time.time(), digest, name))
