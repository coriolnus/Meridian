"""storage.py — defter varlıklarının (`ENTITIES` kaydı) SQLite arka ucu: `state/meridian.db` + WAL + tek transaction.

NE YAPAR. `ENTITIES` kaydındaki varlıkları (kanonik ad → tablo + tür rows/doc/series; sayı ve adlar
YALNIZ kayıtta yazılıdır — Kademe A+B'nin defter çekirdeği + Kademe C'nin iki öğrenme defteri)
SQLite'ta tutar. Dosya çağında iki sınıf açıktı: süreçler-arası oku-değiştir-yaz
yarışı (RLock yalnız aynı süreçte anlam taşır; canlı worker + pano API + sprint aynı dosyaya
yazabiliyordu) ve atomik olmayan JSONL ekleme (çökme yarım satır bırakır). SQLite ikisini
YAPISAL olarak kapatır: kazanç ŞEMA değil, atomiklik + süreçler-arası kilittir (WAL +
busy_timeout). Uygulama kodu bu modülü DOĞRUDAN çağırmaz; `store.py` yönlendirir ve çağıranlar
aynı dict/list yapılarını alır — depolama migrasyonu, davranış migrasyonu değil.

KİLİT GİRİŞLER. `active(ad)` anahtarlama kapısı: DB dosyası/şeması yoksa her şey dosyadan sürer;
şemaya SONRADAN giren bir varlık (`DAMGA_KAPILI`) ayrıca kendi `migrated_at` damgasını ister — damga
dolana dek dosyadan okunur (Kademe C R1: DB'nin var olduğu bir makinede yeni varlığın BOŞ okunma penceresi).
`connect()` (yol başına tek bağlantı; `create=False` SİGORTADIR — sqlite3.connect olmayan yolu
sessizce yaratır ve boş doğan bir DB defterleri boş okuturdu; yaratma yetkisi yalnız
`ensure_schema`/dbmigrate yolunda). `read_entity`/`write_entity` ortak yüzeyi; `read_rows`/
`append_row`/`replace_rows`, `read_doc`/`write_doc`, `read_series`/`write_series`; `meta`/`stamp`
(entity_meta damgası — dosya çağındaki mtime'ın karşılığı, önbellek anahtarı + tazelik ölçümü);
`backup_to` (çevrimiçi yedek — WAL modunda cp/tar sessizce eksik kopya verir); `close_connections`.
`db_path()` her çağrıda `config.STATE`ten türetilir: yol dondurmak ölçüm sandbox'larını kırar.

DEĞİŞMEZLER. Tip koruma (parite sözleşmesi): tipli kolonlar sorgulanabilirlik içindir, DOĞRULUK
kaynağı değil — tipi uymayan alan (−0.0 dahil: REAL kolon işaret bitini kaybeder) ayrıca
`extra_json`a yazılır ve okumada extra KAZANIR; SQLite tip afinitesi veriyi sessizce değiştiremez.
`MERIDIAN_DB=off` TEK BAŞINA GERİ DÖNÜŞ DEĞİLDİR (eski "acil geri dönüş anahtarı" beyanı
YANLIŞLANDI): kaynaklar `.migrated` adında dururken anahtarı çeken operatör o defterleri BOŞ okur
ve ilk yazımda ayrışık ikinci bir kitap doğar — geri dönüş kolu `dbmigrate --geri-al`dır; yarım
hâl varsayılmaz, ÖLÇÜLÜR ve süreç başına bir kez beyan edilir (`db_off_kaynaklar_arsivde`).
SİMETRİĞİ (P2): DB dosyası hiç YOKKEN kanonik defter dosyaları duruyorsa süreç başına bir kez
`yerel_donmus_defter` damgalanır — bu makinedeki defter donmuş fotoğraf olabilir, canlı DB başka
makinede olabilir; süreç-içi dedektör bu ayrışmayı yapısal olarak göremez (envanter 2026-08-22 #4).
Okur/yazar: yalnız `state/meridian.db` (+ -wal/-shm).
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from . import config

DB_NAME = "meridian.db"
# 1: Kademe A+B defter çekirdeği (2026-07-31). 2: Kademe C öğrenme defterleri (TSK-020, 2026-09-28) —
# yeni tablolar `CREATE IF NOT EXISTS` ile doğar, eski tablolara dokunulmaz; sürüm satırı `apply_schema`
# içinde (yani çağıranın transaction'ında) eklenir, düşen migrasyon onu da geri alır.
SCHEMA_VERSION = 2
# Taşınmış kaynak dosyanın son eki. TEK KAYNAK BURADADIR: `dbmigrate` bunu içe aktarır. İki yerde
# iki sabit olsaydı, biri değiştiğinde `MERIDIAN_DB=off` uyarısı arşivleri sessizce göremez olurdu.
MIGRATED_SUFFIX = ".migrated"

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
# Kademe C (TSK-020, 2026-09-28): öğrenme katmanının iki defteri.
HYPOTHESES = "hypotheses.jsonl"
VALIDATION = "validation_ledger.jsonl"

# Tipli kolonlar. Tipler CANLI defterden ÖLÇÜLDÜ (state/trades.jsonl 95 satır ×
# state/trade_plans.jsonl 390 satır — her alanın tipi tek değerliydi), uydurulmadı. Ölçüm dışı
# kalan alanlar (skill_chain, targets, gate_checks, …) extra_json'da yaşar: sözleşme (ledgers.py)
# onları serbest bırakır ve tipli bir kolona zorlamak şemayı defterin kendisinden daha katı yapardı.
_COLS: dict[str, tuple[tuple[str, str], ...]] = {
    # TSK-150(a) (2026-09-05): `trades.id` (`T%05d`) GERÇEK ANAHTAR DEĞİLDİR — gerçek anahtar
    # `seq` (yukarıdaki DDL: `seq INTEGER PRIMARY KEY`, aşağıda `id TEXT` UNIQUE KISITI YOK).
    # `id` bir İNSAN ETİKETİDİR ve İLERİ YÖNLÜ TEKİLDİR: `broker.PaperBroker` sınıfının `_id` sayacı sayacı ile
    # `loop._load_broker`/`loop._persist_trade`teki çarpışma reddi (TSK-150(a) D1/D2) bundan sonra
    # üretilen id'lerin tekilliğini korur, ama GEÇMİŞTE (tohum genişletme, last_id gerisi) yazılmış
    # 16 çift zaten mevcuttur ve bu dilim onları YENİDEN NUMARALAMAZ — operatör kararı bekler.
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
        # deftere HENÜZ basılmadı (migrasyon Rol-1'de) — kolon boş kalır, uydurulmaz.
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
    # KADEME C KOLONLARI — A1 canlı defterinden ÖLÇÜLDÜ (Rol-1, 2026-09-28: hypotheses 60 satır/25 anahtar,
    # validation_ledger 398 satır/32 anahtar, 0 bozuk). Kural: HER satırda bulunan ve tek tipli (None'a
    # izinli) skaler alan tipli kolon olur. Kolona ZORLANMAYANLAR `extra_json`da yaşar:
    #   * tipi KARIŞIK — `old`/`new` (float + int + None): REAL kolon int'i float'a çevirir, parite düşerdi;
    #   * İÇ İÇE — reject_reasons/backtest/realized_detail/vs_benchmark_at_ship · degisen_params/oos_ozet/
    #     oos_components (sqlite3 liste/sözlük bağlayamaz; `seri` istisnası aşağıda);
    #   * SEYREK / SONRADAN DOĞAN — hyp: status_ts, note, overfit_suspect, realized_delta, calibration_hit,
    #     outcome_ts; val: yasa_surumu, oos_para, incumbent_para, dd_ok, candidate_dd, incumbent_dd,
    #     pencere_id, dd_mtm_* ve `ret_seri`/`ret_n` (TSK-077: kod yazıyor, canlıda 2026-09-28'de HENÜZ YOK —
    #     ölçülmemiş bir alanın tipini kolona dondurmak uydurma olurdu; extra_json hiçbir şey kaybettirmez).
    # None'a izinli kolonlar (hyp `version_to` None58/int2; val `eval_regime`, `oos_score`,
    # `incumbent_oos`, `sharpe_gozlem`, `dsr`, `varyans_kaynagi`) güvenlidir: `_matches(None, …)` False
    # döner, anahtar `extra_json`a `null` olarak da yazılır ve okumada extra KAZANIR — anahtarın varlığı korunur.
    # TEK İSTİSNA `seri` ("JSON" kolon): iç içe ama SÖZLEŞMEDE ZORUNLU (`ledgers.CONTRACTS` — PBO'nun ortak
    # takvim ızgarası anahtarı). `watchdog.EQUIVALENT_TRUTHS["defter_sema_kapsami"]` her zorunlu alanın
    # tipli bir kolonu olmasını ister; extra_json'a gömülse dedektör AYRIK derdi. JSON kolonu değeri
    # `json.dumps` metni olarak taşır (TEXT afinitesi; `json_extract` ile sorgulanır) — JSON gidiş-dönüşü
    # int/float/-0.0/None ayrımını korur, parite digesti değişmez.
    HYPOTHESES: (
        ("id", "TEXT"), ("ts", "TEXT"), ("variable", "TEXT"), ("rationale", "TEXT"),
        ("predicted_direction", "TEXT"), ("predicted_delta", "REAL"), ("confidence", "REAL"),
        ("regime", "TEXT"), ("source", "TEXT"), ("version_from", "INTEGER"),
        ("version_to", "INTEGER"), ("status", "TEXT"), ("market_regime", "TEXT"),
    ),
    VALIDATION: (
        ("ts", "TEXT"), ("fingerprint", "TEXT"), ("etiket", "TEXT"), ("eval_regime", "TEXT"),
        ("oos_score", "REAL"), ("incumbent_oos", "REAL"), ("passes", "BOOL"),
        ("gate_law", "TEXT"), ("fold_wins", "TEXT"), ("tail_ok", "BOOL"),
        ("k_probes", "INTEGER"), ("erosion_queries", "INTEGER"), ("n_trials", "INTEGER"),
        ("sharpe_gozlem", "REAL"), ("dsr", "REAL"), ("varyans_kaynagi", "TEXT"), ("beyan", "TEXT"),
        ("seri", "JSON"),
    ),
}
# Mantıksal tip → SQLite kolon tipi. BOOL ve JSON SQLite'ta yoktur: BOOL 0/1 INTEGER, JSON `json.dumps`
# metni (TEXT). Okumada `_cols_to_row` mantıksal tipi geri kurar.
_SQL_TIP = {"BOOL": "INTEGER", "JSON": "TEXT"}

_TABLE = {TRADES: "trades", PLANS: "trade_plans", SCOREBOARD: "scoreboard",
          PORTFOLIO: "portfolio", EQUITY: "equity_curve", SHADOW_BOOKS: "shadow_books",
          HYPOTHESES: "hypotheses", VALIDATION: "validation_ledger"}
_KIND = {TRADES: "rows", PLANS: "rows", EQUITY: "series",
         SCOREBOARD: "doc", PORTFOLIO: "doc", SHADOW_BOOKS: "doc",
         HYPOTHESES: "rows", VALIDATION: "rows"}

ENTITIES: tuple[str, ...] = (TRADES, PLANS, SCOREBOARD, PORTFOLIO, EQUITY, SHADOW_BOOKS,
                             HYPOTHESES, VALIDATION)
ROW_ENTITIES = tuple(n for n in ENTITIES if _KIND[n] == "rows")
DOC_ENTITIES = tuple(n for n in ENTITIES if _KIND[n] == "doc")

# VARLIĞIN DOĞDUĞU ŞEMA SÜRÜMÜ — kayıtta olmayan 1'dir (Kademe A+B: DB ile AYNI koşuda doğdular).
# NEDEN BİR KAPI GEREKİYOR (Kademe C R1, tasarım 2026-09-28): `active()` DB DÜZEYİNDE karar verir — DB
# dosyası + şema varsa kayıttaki HER ad için True. Şemaya SONRADAN giren bir varlık için bu, kodun
# dağıtıldığı an (veri henüz taşınmadan) okumaların DB'ye gitmesi demektir: tablo yoksa istisna, tablo
# `CREATE IF NOT EXISTS` ile doğmuşsa BOŞ defter — öğrenme geçmişi "yok" görünür. Kademe A+B'de bu
# pencere YOKTU, çünkü o varlıklar DB ile aynı migrasyon koşusunda doğdu.
# NEDEN ESKİLERE UYGULANMAZ: kapı genel olsaydı `kaynak_yok` diye taşınan (damgasız ama DB'de YAZILAN)
# bir eski varlık dosyaya dönerdi — göçten sonra DB'ye yazılmış kayıtlar görünmez olur, ayrışık ikinci
# kitap doğardı (`test_bayat_defter_kalintisi_v234` gocsuz çivisi bu davranışı çiviler). A1'de altısı
# damgalı (ölçüldü 2026-09-28) ama ortam bağımsız garanti "eskiler hiç kapıya girmez"dir.
_DOGDUGU_SURUM: dict[str, int] = {HYPOTHESES: 2, VALIDATION: 2}
DAMGA_KAPILI: tuple[str, ...] = tuple(n for n in ENTITIES if _DOGDUGU_SURUM.get(n, 1) > 1)


def table_of(name: str) -> str | None:
    """Kanonik varlık adının SQLite tablo adı; kayıtta yoksa `None`."""
    return _TABLE.get(name)


def kind_of(name: str) -> str | None:
    """Varlığın türü — "rows" | "doc" | "series"; kayıtta yoksa `None`."""
    return _KIND.get(name)


# ---- BAĞLANTI ----------------------------------------------------------------------------------
# TEK BAĞLANTI, TEK KİLİT. sqlite3 bağlantısı iş parçacıkları arasında paylaşılabilir ama
# EŞZAMANLI kullanılamaz; `check_same_thread=False` + süreç-içi RLock bunu sağlar. SÜREÇLER arası
# eşzamanlılık WAL + busy_timeout'un işidir (çekirdeğin kendisi, bizim değil).
_CONNS: dict[str, sqlite3.Connection] = {}
_GUARD = threading.RLock()
_SCHEMA_OK: set = set()
# `MERIDIAN_DB=off` uyarısı YOL BAŞINA BİR KEZ ölçülür (C5). `active()` her okumada çağrılır;
# ölçümü önbelleğe almasaydık her `read_json` varlık başına bir `stat()` ve potansiyel bir olay satırı üretirdi.
_OFF_OLCULDU: set = set()
# D2 DAMGA ÖNBELLEĞİ — (db yolu, varlık) çiftleri, YALNIZ damga DOLUYKEN ve COMMIT edilmiş okumada
# girer. Damgasız sonuç ÖNBELLEĞE ALINMAZ: göç (`dbmigrate --uygula`) BAŞKA bir süreçte COMMIT edilir ve
# bu süreç bir sonraki okumada onu görmelidir (bedeli: damgasız varlığın her okuması tek `entity_meta`
# sorgusu — v579 bedel çivisi ölçer). Damga geri ALINMAZ (yalnız `--geri-al` DB'yi kenara alır → dosya
# yok dalı önbelleği düşürür; `close_connections` da temizler).
_DAMGA_OK: set = set()
# `yerel_donmus_defter` damgası da YOL BAŞINA BİR KEZ (P2 — `db_off`un simetriği, aynı gerekçe).
_YEREL_OLCULDU: set = set()
_SUREC_BASI = time.time()   # fotoğraf şartının çapası: bu süreç doğduğunda duvar saati

PRAGMAS = (("journal_mode", "wal"), ("synchronous", "normal"),
           ("busy_timeout", 5000), ("foreign_keys", 1))


def db_path() -> Path:
    """DB yolu — HER ÇAĞRIDA `config.STATE`ten türetilir (sandbox'lar STATE'i değiştirir)."""
    return Path(config.STATE) / DB_NAME


def _dict_row(cursor, row):
    """sqlite3 `row_factory`: satırı demet yerine {kolon adı: değer} sözlüğü olarak verir."""
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


def close_connections() -> None:
    """Tüm bağlantıları kapat (testler ve sandbox söküm yolları için).

    ADI BİLEREK `close_all` DEĞİL: `alpaca.close_all` TÜM POZİSYONLARI DÜZLEŞTİREN
    yetki-yasası çağrısıdır ve dedektörü (`test_authority_boundaries_v77`) AST'de ATTRIBUTE ADINA
    bakar — bu modülde hipotetik bir `close_all()` masum bir bağlantı kapatması olduğu hâlde ihlal olarak yakalanırdı.
    Dedektör daraltılmaz (paranoyak kalır); isim uzayı ayrık tutulur."""
    with _GUARD:
        for c in _CONNS.values():
            try:
                c.close()
            except sqlite3.Error:  # sessiz-yutma: kapatma sırasında düşen bağlantı zaten kullanılamaz durumda; kapatma denemesi çağıranı düşüremez ve açık kalan tanıtıcıyı süreç sonu toplar
                pass
        _CONNS.clear()
        _SCHEMA_OK.clear()
        _DAMGA_OK.clear()               # aynı gerekçe: disk gerçeği değişti, damga ölçümü taşınmaz
        # `_OFF_OLCULDU` DA TEMİZLENİR: bu çağrı disk gerçeğinin DEĞİŞTİĞİ anlarda yapılır
        # (`--geri-al`, karantina, test sökümü) — ölçümü taşımak, önbelleği diskteki gerçeğin
        # ötesinde tutmak olurdu (`_SCHEMA_OK` ile aynı gerekçe).
        _OFF_OLCULDU.clear()


# ---- ŞEMA --------------------------------------------------------------------------------------
def _ddl() -> list[str]:
    """Şemanın tüm DDL ifadelerini üretir: `schema_version`, `entity_meta`, `ENTITIES` kaydındaki
    her varlığın tablosu ve indeksler. Hepsi `IF NOT EXISTS` — idempotenttir, var olan veriye dokunmaz
    (v1 DB'de yalnız Kademe C tabloları doğar)."""
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
        cols = ",".join(f'  "{c}" {_SQL_TIP.get(t, t)}' for c, t in _COLS[name])
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


def apply_schema(conn: sqlite3.Connection) -> None:
    """Şema ifadeleri — TRANSACTION YÖNETMEZ (çağıran açar/kapatır); `do_replace_rows` ile aynı desen.

    NEDEN AYRILDI. `ensure_schema` KENDİ `BEGIN…COMMIT`ini atıyordu ve `dbmigrate`
    onu migrasyon transaction'ından ÖNCE çağırıyordu. Sonuç ölçüldü: migrasyon KAYNAK_BOZUK ya da
    PARİTE_TUTMADI ile düşse bile şema COMMIT edilmiş kalıyor, `active()` "dosya var + şema sürümü
    var" görüp True dönüyor ve altı defter BOŞ okunuyordu — yani `connect` docstring'inin adıyla
    yasakladığı hâl ("migrasyon yapılmadan yapılmış gibi görünen bir geçiş"). Şemayı çağıranın
    transaction'ına sokabilmek, o geri almanın ŞEMAYI DA götürmesini sağlar: düşen bir migrasyondan
    sonra geride şemasız (yani `active()`in False dediği) bir dosya kalır.

    `_SCHEMA_OK` önbelleğine BURADA YAZILMAZ: bu ifadeler henüz COMMIT edilmemiş olabilir ve
    geri alınabilir bir gerçeği önbelleğe yazmak, önbelleği diskteki gerçeğin ötesine geçirirdi.
    Damgayı yalnız COMMIT'i kendisi atan `ensure_schema` düşürür."""
    for stmt in _ddl():
        conn.execute(stmt)
    row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    # SÜRÜM YÜKSELTMESİ DE BURADA (Kademe C): eskiden yalnız "hiç sürüm yok" dalı vardı — v1 bir DB'ye
    # yeni tablolar eklenir ama sürüm 1'de kalırdı ve `--durum` şemanın gerçeğini söylemezdi. Satır
    # EKLENİR (güncellenmez): `schema_version` bir geçmiştir, hangi sürümün NE ZAMAN geldiğini taşır.
    if row is None or row["v"] is None or int(row["v"]) < SCHEMA_VERSION:
        conn.execute("INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                     (SCHEMA_VERSION, time.time()))
    for name in ENTITIES:
        conn.execute("INSERT OR IGNORE INTO entity_meta(entity, present, rev, updated_at, n) "
                     "VALUES (?, 0, 0, 0, 0)", (name,))


def ensure_schema(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """İdempotent şema kurulumu + sürüm damgası. DB dosyasını YARATMA yetkisi olan tek yol."""
    c = conn or connect(create=True)
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            apply_schema(c)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
    _SCHEMA_OK.add(str(db_path()))
    return c


def schema_version(conn: sqlite3.Connection | None = None) -> int | None:
    """DB'de kayıtlı en yüksek şema sürümü; tablo yoksa ya da dosya SQLite değilse `None`
    (sürüm UYDURULMAZ — `active()` bunu "DB devrede değil" diye okur)."""
    c = conn or connect()
    try:
        with _GUARD:
            row = c.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        return None if row is None else row["v"]
    except sqlite3.DatabaseError:  # sessiz-yutma: tablo yoksa/dosya DB değilse SÜRÜM YOKTUR ve dönen None tam olarak bunu söyler — çağıran (active) bunu "DB devrede değil" diye okur, varsayılan bir sürüm UYDURULMAZ
        return None


def disabled_by_env() -> bool:
    """`MERIDIAN_DB=off`: DB dosyası dursa bile dosya yoluna dönülür.

    BU BİR GERİ DÖNÜŞ DEĞİL, BİR ANAHTARDIR. Dosyalar `.migrated` adında duruyorsa dosya yolu BOŞ
    okur; geri dönüş kolu `dbmigrate --geri-al`dır (modül docstring'i). Anahtarın bu yarım hâli
    `_acil_anahtar_beyani()` tarafından ölçülüp beyan edilir."""
    return os.environ.get("MERIDIAN_DB", "").strip().lower() in ("0", "off", "false", "no")


def _acil_anahtar_beyani() -> None:
    """`MERIDIAN_DB=off` çekilmiş AMA defterler hâlâ arşivdeyse SÜREÇ BAŞINA BİR KEZ uyar (C5).

    ÖLÇÜLEN HÂL: anahtar açık + `meridian.db` DOSYASI duruyor + kanonik ada sahip kaynak YOK ama
    `<ad>.migrated` VAR. Bu üçlü tam olarak "operatör acil anahtarı çekti ve defterler boş okunmaya
    başladı" demektir: `store._path` kanonik ada bakar, bulamaz, çağıranın varsayılanına düşer —
    ölçüldü (denetim C5): trades n=0, portfolio/scoreboard/equity VARSAYILAN, `stamp`=(0,0).

    NEDEN REDDETMEK DEĞİL DE UYARMAK. Bu kod yolu bir OKUMA kapısıdır ve kriz anında çekilen bir
    anahtarın ardından koşar; istisna fırlatmak panoyu ve worker'ı topyekûn düşürürdü — yani
    operatörün elindeki son gözlem yüzeyini de alırdı. Eksik olan şey KARAR değil BEYAN'dı: hangi
    defterlerin arşivde olduğu ve kolun adı (`--geri-al`) tek satırda önüne gelir.

    ÖLÇÜM ÖNBELLEĞE ALINIR (`_OFF_OLCULDU`) ama DB dosyası YOKKEN alınmaz: dosya yoksa ortada
    "yarım geri dönüş" hâli de yoktur ve o durum aynı süreç içinde migrasyonla değişebilir."""
    p = db_path()
    if not p.exists():                      # tek `stat` — DB yoksa anlatılacak bir hâl yok
        return
    key = str(p)
    if key in _OFF_OLCULDU:
        return
    _OFF_OLCULDU.add(key)
    state = Path(config.STATE)
    arsivde = [n for n in ENTITIES
               if not (state / n).exists() and (state / (n + MIGRATED_SUFFIX)).exists()]
    if not arsivde:
        return
    try:
        from . import obs
        obs.warn("db_off_kaynaklar_arsivde", db=key, arsivde=arsivde, n=len(arsivde),
                 detail=("MERIDIAN_DB=off çekili ve DB devre dışı, AMA bu defterlerin dosya "
                         "karşılığı `.migrated` adında — kanonik addan okuyan her çağrı BOŞ "
                         "varsayılana düşer (geri dönüş DEĞİL, boş defter). Geri dönüş kolu: "
                         "`python -m meridian.dbmigrate --geri-al` (DB kenara alınır, arşivler "
                         "asıl adlarına döner, hiçbir veri silinmez)."))
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; BEYAN denemesi bir okuma kapısını düşüremez ve kararı (dosya yoluna dön) zaten çağıran uyguluyor — hâl her yeni süreçte yeniden ölçülür
        pass


def _yerel_defter_beyani(p: Path) -> None:
    """DB dosyası YOKKEN kanonik defter dosyaları duruyorsa SÜREÇ BAŞINA BİR KEZ damgala (P2).

    `db_off_kaynaklar_arsivde`nin SİMETRİĞİ (denetim P2; envanter 2026-08-22 §4.2-#4): o beyan
    "DB dünyasında defterler arşivde, boş okunuyor" yarım hâlini anlatır; bu damga TERSİNİ —
    süreç `meridian.db` OLMAYAN bir makinede kayıttaki defterleri DOSYADAN kanonik okuyor. Süreç-içi
    hiçbir dedektör bunu ayrışma olarak GÖREMEZ: kendi gördüğü tek kitap zaten bu dosyalar
    ("göç hiç olmamış" dünyasından ayırt edilemez). Ölçülen vaka (08-22): yerel `trades.jsonl`
    95 satır / `portfolio.last_date` 2026-07-28'de DONUK, canlı DB başka makinede 97/409 —
    yani bu makinedeki defter donmuş bir FOTOĞRAF olabilir. Damga o körlüğün beyanıdır.

    KARAR DEĞİL BEYAN: okuma davranışı bit-bit aynı kalır (dosyadan sürer) — `db_off` beyanıyla
    aynı gerekçe: istisna fırlatmak panoyu/worker'ı düşürür, eksik olan karar değil beyandı.
    OKUYUCUSU (YASA 6): `obs.warn` → `state/events.jsonl` → pano + `obs.recent` —
    `db_off_kaynaklar_arsivde` ile AYNI teşhis yüzeyi.

    ÖNBELLEK SİMETRİSİ: `_acil_anahtar_beyani` DB dosyası VARKEN önbelleğe alır ("dosya yoksa
    hâl migrasyonla değişebilir"); burası tam tersi — DB YOKKEN, ve yalnız anlatılacak hâl
    (en az bir kanonik dosya) varken alır: boş sandbox'ta alınmaz, çünkü dosyalar aynı süreçte
    yazılıp hâl sonradan doğabilir. `MERIDIAN_DB=off` dünyası buraya hiç gelmez (`active()`
    daha önce döner) — o dünyanın beyanı `_acil_anahtar_beyani`nındır."""
    key = str(p)
    if key in _YEREL_OLCULDU:
        return
    state = Path(config.STATE)
    mevcut = [n for n in ENTITIES if (state / n).exists()]
    if not mevcut:
        return                      # anlatılacak hâl yok — önbellek ALINMAZ, hâl bu süreçte doğabilir
    # FOTOĞRAF ŞARTI (2026-08-23 düzeltmesi; v150 yakaladı): tehlike "DONMUŞ fotoğraf"tır — bu
    # sürecin ÇAĞINDA doğmuş dosyalar (test kum-havuzları, taze tohumlama) o tehlikeyi TANIMSIZ
    # kılar ve damga her taze sandbox'ta bir gürültü satırına dönerdi (yol-başına önbellek ×
    # test-başına taze yol = süreç boyu sel). En yeni defter mtime'ı süreç başlangıcından
    # YENİYSE sus — önbelleksiz (dosyalar eskiyebilir, hâl sonraki çağrıda yeniden ölçülür).
    try:
        en_yeni = max((state / n).stat().st_mtime for n in mevcut)
    except OSError:
        return                      # sessiz-yutma: mtime okunamayan dosya yarış/silinme anıdır; beyan bir sonraki çağrıya kalır
    if en_yeni >= _SUREC_BASI:
        return
    _YEREL_OLCULDU.add(key)         # obs'tan ÖNCE: beyan denemesi tekrar giriş üretmesin
    try:
        from . import obs
        obs.warn("yerel_donmus_defter", db=key, mevcut=mevcut, n=len(mevcut),
                 detail=("Bu makinede `meridian.db` YOK; bu defterler DOSYADAN kanonik okunuyor. "
                         "Migrasyon-sonrası dünyada bu, defterin DONMUŞ bir fotoğraf olabileceği "
                         "anlamına gelir — canlı DB başka bir makinede olabilir ve süreç-içi "
                         "dedektör bu ayrışmayı göremez. Okuma davranışı değişmedi; buradan "
                         "okunan sayıları canlıya dayandırmadan önce bu damgayı yan yana okuyun."))
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; beyan bir okuma kapısını düşüremez — okuma dosyadan aynen sürer, hâl her yeni süreçte yeniden ölçülür
        pass


def active(name: str | None = None) -> bool:
    """Bu varlık ŞU AN DB'den mi okunuyor? (DB dosyası yoksa: HAYIR — davranış birebir bugünkü.)

    İKİ DÜZEY. `active()` (adsız) DB-DÜZEYİ sorudur: DB dosyası + şema var ve anahtar açık mı. Ad
    verilirse ek olarak: kayıtta mı, ve `DAMGA_KAPILI` bir varlıksa (şemaya sonradan girdi) DB'de
    `migrated_at` damgası DOLU mu (D2, Kademe C R1). Damga dolana dek o varlık DOSYADAN okunur; göç
    COMMIT'i onu tek hamlede DB'ye geçirir — arada boş okuma anı yoktur. Eski varlıklar kapıdan muaftır
    (gerekçe `_DOGDUGU_SURUM` üstünde)."""
    if name is not None and name not in _TABLE:
        return False
    if disabled_by_env():
        _acil_anahtar_beyani()
        return False
    p = db_path()
    key = str(p)
    if not p.exists():
        _SCHEMA_OK.discard(key)
        for n in DAMGA_KAPILI:
            _DAMGA_OK.discard((key, n))
        _yerel_defter_beyani(p)     # P2 damgası: DB'siz dünyada dosyalar kanonik — donmuş fotoğraf olabilir
        return False
    if key not in _SCHEMA_OK:
        if schema_version(connect(p)) is None:
            return False
        if len(_SCHEMA_OK) > 64:    # sandbox'lar süreç ömrü boyunca birikmesin
            _SCHEMA_OK.clear()
        _SCHEMA_OK.add(key)
    if name is None or name not in DAMGA_KAPILI:
        return True
    return _damgali(p, name)


def _damgali(p: Path, name: str) -> bool:
    """D2 kapısının ölçümü: varlığın `entity_meta.migrated_at` damgası DOLU mu?

    SORGU İSTİSNASI YUTULMAZ: `entity_meta` okunamıyorsa DB bozuktur ve eski varlıkların okuması da
    düşecektir; burada False dönüp dosyaya düşmek, damgalı bir varlığı `.migrated` arşivinin yanındaki
    BOŞ kanonik yoldan okutmak — yani R1'in kendisini — üretirdi. Satır YOKSA (v1 DB: Kademe C tabloları
    ve damga satırları henüz doğmadı) cevap dürüstçe "damgasız"dır.

    ÖNBELLEK YALNIZ COMMIT EDİLMİŞ DAMGAYA: bağlantı süreç-içi paylaşımlıdır ve açık bir transaction
    (dbmigrate'in tek transaction'ı) kendi COMMIT edilmemiş damgasını görür. O an önbelleğe yazılan bir
    damga ROLLBACK'ten sonra SİLİNMİŞ bir gerçeği taşırdı ve süreç varlığı boş tablodan okurdu
    (v579 çivisi). Transaction içindeyken cevap verilir ama önbelleğe yazılmaz."""
    key = (str(p), name)
    if key in _DAMGA_OK:
        return True
    c = connect(p)
    with _GUARD:
        rec = c.execute("SELECT migrated_at FROM entity_meta WHERE entity=?", (name,)).fetchone()
        islemde = c.in_transaction
    damgali = bool(rec and rec.get("migrated_at"))
    if damgali and not islemde:
        if len(_DAMGA_OK) > 256:    # sandbox'lar süreç ömrü boyunca birikmesin (_SCHEMA_OK deseni)
            _DAMGA_OK.clear()
        _DAMGA_OK.add(key)
    return damgali


def table_exists(name: str, conn: sqlite3.Connection | None = None) -> bool:
    """Varlığın tablosu DB'de VAR mı? v1 bir DB'de (Kademe C göçünden önce) iki öğrenme defterinin
    tablosu YOKTUR — onları okumaya kalkan rapor (`dbmigrate.db_state`) istisnayla çökerdi; soru önce sorulur."""
    tbl = _TABLE.get(name)
    if tbl is None:
        return False
    c = conn or connect()
    with _GUARD:
        rec = c.execute("SELECT 1 AS x FROM sqlite_master WHERE type='table' AND name=?",
                        (tbl,)).fetchone()
    return rec is not None


# ---- SATIR ↔ KOLON ÇEVİRİSİ --------------------------------------------------------------------
def _isaretli_sifir(val: Any) -> bool:
    """`-0.0` mı? (`val == 0.0` her iki sıfır için de True'dur; ayrım YALNIZ işaret bitindedir.)

    NEDEN AYRI BİR SORU (property testi buldu — elle yazılmış hiçbir
    örnek testi bunu aramamıştı): SQLite'ın REAL kolonu negatif sıfırın İŞARETİNİ KAYBEDER.
        sqlite> CREATE TABLE t(x REAL); INSERT INTO t VALUES(-0.0); SELECT x FROM t;  →  0.0
    Tip afinitesi savunması (`_matches`) bu sızıntıya YAPISAL OLARAK kördü: `-0.0` GERÇEKTEN bir
    `float`tur, yani tip UYUYOR, alan yalnız kolona yazılıyor ve `extra_json` kaçış yolu hiç
    devreye girmiyordu. Modül başlığındaki "tip afinitesi sessizce veriyi değiştiremez" vaadi tam
    burada delikti.

    ZARARI TEORİK DEĞİL, OPERASYONEL: `dbmigrate` parite digestini `json.dumps` ile hesaplar ve
    JSON `-0.0` ile `0.0`ı FARKLI yazar. Canlı defterde tek bir `-0.0` bulunsaydı kaynak digesti
    ile DB digesti tutmaz ve MİGRASYON TAMAMEN GERİ ALINIRDI — üstelik hata mesajı yalnız "digest
    tutmadı" derdi, nedenini kimse bulamazdı. Canlı defter BUGÜN tarandı: 0 örnek (yani kusur
    LATENT'ti, aktif değil). Ama `round(-1e-9, 4)` → `-0.0`tır ve bu depo her yerde `round` kullanır;
    yani ilk örneğin doğması an meselesiydi.

    ÇÖZÜM YENİ MEKANİZMA DEĞİL, VAR OLANIN DOĞRU TETİKLENMESİ: değer "kolonun sadakatle taşıyamadığı"
    sınıfa alınır → `extra_json`a da yazılır → okumada extra KAZANIR. Kolon yine dolar (0.0),
    yani sorgulanabilirlik kaybolmaz; DOĞRULUK extra'da yaşar."""
    return isinstance(val, float) and val == 0.0 and math.copysign(1.0, val) < 0


def _matches(val: Any, typ: str) -> bool:
    """Değer kolonun tipine SADAKATLE sığıyor mu? `bool`/`int` ayrımı korunur ve `-0.0` REAL'e
    uymuyor sayılır (işaret biti kolonda kaybolur) — uymayan alan `extra_json`a düşürülür. JSON
    kolonu yalnız liste/sözlük taşır (skaler/None → extra_json)."""
    if typ == "BOOL":
        return isinstance(val, bool)
    if typ == "INTEGER":
        return isinstance(val, int) and not isinstance(val, bool)
    if typ == "REAL":
        return isinstance(val, float) and not _isaretli_sifir(val)
    if typ == "JSON":
        return isinstance(val, (list, dict))
    return isinstance(val, str)


def _scalar(val: Any) -> bool:
    """Değer sqlite3'ün doğrudan bağlayabileceği bir skaler mi (None/str/int/float/bool)?
    Liste/sözlük için False döner — o alanlar kolonda NULL kalır, doğruluğu `extra_json` taşır."""
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
            vals.append(int(v) if typ == "BOOL" else
                        json.dumps(v, ensure_ascii=False) if typ == "JSON" else v)
        else:
            # Tip uyuşmuyor: kolona (sorgulanabilirlik için) skalerse yine yaz, DOĞRULUĞU
            # extra_json taşısın. Skaler değilse kolon NULL kalır — sqlite3 liste/sözlük kabul etmez.
            # JSON kolonu uyuşmayan değerde HEP NULL: kolon yalnız `json.dumps` metni taşısın ki okuma
            # onu belirsizliksiz geri kurabilsin (ham bir dizge JSON'a benzeyip yanlış çözülebilirdi).
            vals.append(v if typ != "JSON" and _scalar(v) and not isinstance(v, bool) else None)
            extra[col] = v
    return vals, (json.dumps(extra, ensure_ascii=False) if extra else None)


def _cols_to_row(name: str, rec: dict) -> dict:
    """DB satırını defter sözlüğüne çevirir (`_row_to_cols`in tersi): NULL kolonlar atlanır,
    BOOL kolonlar `bool`a döner ve `extra_json` en son birleştirilir — yani extra KAZANIR."""
    spec = _COLS[name]
    out: dict = {}
    for col, typ in spec:
        v = rec.get(col)
        if v is None:
            continue
        if typ == "JSON":
            try:
                out[col] = json.loads(v)
            except (TypeError, json.JSONDecodeError):  # sessiz-yutma: SESSİZ DEĞİL — JSON kolonunu yalnız `_row_to_cols` doldurur (`json.dumps` metni); çözülemeyen değer dış müdahaledir, alan düşer ve `dbmigrate` parite digesti bunu koşuda ölçüp migrasyonu düşürür (bozuk extra_json ile aynı sınıf)
                pass
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
    """Varlık damgasını ilerlet. `env=None` → zarfa DOKUNMA (COALESCE). `env=dict` → MEVCUT zarfın
    ÜSTÜNE BİRLEŞTİR.

    NEDEN BİRLEŞTİRME (LATENT kusurun kapanışı). Buradaki `COALESCE(?, env_json)`
    "None ise koru" demek istiyordu ama TEK env yazarı olan `do_write_series` env'i HER ZAMAN bir
    dict olarak verir (`{}` bile `'{}'` yazılır) — yani koruma hiçbir zaman devreye girmiyordu ve
    zarf her seri yazımında BÜTÜN OLARAK EZİLİYORDU. Eğrinin tek yazarı `run.py`dir ve o yalnız
    `{"version", "points"}` yazar; `sermaye.uygula`nın koyduğu `reset_isaretleri` işareti onun
    SAHİPLENDİĞİ bir anahtar değildir. Yani bir sonraki re-seed, kitapta patlamış olan aynı kusuru
    (2026-08-04 vakası: sahibi olmadığı alanı ezen tam-belge yazarı) EĞRİDE tekrarlayacaktı.
    Birleştirme, sahipliği yazarın kendi anahtarlarıyla sınırlar: yabancı zarf anahtarı yaşar,
    sahiplenilen anahtar güncellenir (`version` yeni değerini alır — birleştirme dondurma değildir).
    """
    env_json = None
    if env is not None:
        mevcut: dict = {}
        row = conn.execute("SELECT env_json FROM entity_meta WHERE entity=?", (name,)).fetchone()
        if row and row["env_json"]:
            try:
                yuk = json.loads(row["env_json"])
                mevcut = yuk if isinstance(yuk, dict) else {}
            except json.JSONDecodeError:  # sessiz-yutma: eski zarf okunamadı — birleştirilecek bir şey YOK ve yeni zarf tam olarak yazılır; okunamayan zarfı korumak, bozuk baytları sonsuza kadar taşımak olurdu (aynı satır `read_series`te de ölçülüyor)
                mevcut = {}
        env_json = json.dumps({**mevcut, **env}, ensure_ascii=False)
    conn.execute("UPDATE entity_meta SET present=?, rev=rev+1, updated_at=?, n=?, "
                 "env_json=COALESCE(?, env_json) WHERE entity=?",
                 (1 if present else 0, time.time(), int(n), env_json, name))


def _select_rows(c: sqlite3.Connection, name: str, limit: int | None = None) -> list[dict]:
    """Satırları `seq` sırasıyla seçer ve defter sözlüğüne çevirir — TRANSACTION YÖNETMEZ, `_GUARD`
    ALMAZ (çağıran alır). `read_rows` ile `update_rows` AYNI okumayı paylaşsın diye ayrıldı: iki kopya
    sessizce ayrışan iki okuma olurdu."""
    tbl = _TABLE[name]
    if limit:
        recs = c.execute(f"SELECT * FROM {tbl} ORDER BY seq DESC LIMIT ?", (int(limit),)).fetchall()
        recs.reverse()
    else:
        recs = c.execute(f"SELECT * FROM {tbl} ORDER BY seq").fetchall()
    return [_cols_to_row(name, r) for r in recs]


def read_rows(name: str, limit: int | None = None) -> list[dict]:
    """Satır defterini ekleme sırasıyla (`seq`) okur. `limit` verilirse SON `limit` satır alınır
    ve sıra yeniden eskiden yeniye çevrilir — `store.read_jsonl(limit=…)` sözleşmesiyle aynı."""
    c = connect()
    with _GUARD:
        return _select_rows(c, name, limit)


def update_rows(name: str, fn) -> list[dict]:
    """ATOMİK OKU-DEĞİŞTİR-YAZ (Kademe C D3): oku → `fn(satırlar)` → (True dönerse) tamamını yaz, üçü
    TEK `BEGIN IMMEDIATE` içinde; `fn` istisna atarsa ROLLBACK.

    NEDEN (R2, tasarım 2026-09-28). `store.read_jsonl` + `store.write_jsonl` çifti iki AYRI adımdı: okuma
    transaction DIŞINDA, yazma "hepsini sil + yaz". Arada başka bir süreç (öğrenme: `memory.record`)
    satır eklerse yeniden yazım onu SİLER. `BEGIN IMMEDIATE` yazma kilidini okumadan ÖNCE alır: diğer
    yazarın eklemesi `busy_timeout` boyunca BEKLER ve COMMIT'ten SONRA iner — kaybolmaz.

    SÖZLEŞME `store.update_jsonl` ile aynı: `fn` satır listesini YERİNDE değiştirir, True dönerse yazılır
    (False → yazım yok, damga ilerlemez). Dönüş: `fn`in gördüğü (ve değiştirdiği) liste. `fn` içinde
    G/Ç yapılmamalıdır — yazma kilidi `fn` boyunca tutulur (obs uyarısı gibi yan etkiler çağıranda,
    transaction'dan SONRA)."""
    c = connect()
    with _GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            rows = _select_rows(c, name)
            if fn(rows):
                do_replace_rows(c, name, rows)
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
    return rows


def append_row(name: str, row: dict) -> None:
    """Satır defterine tek satır ekler ve damgayı ilerletir — ikisi TEK `BEGIN IMMEDIATE`
    transaction'ında, hata hâlinde ROLLBACK (JSONL eklemenin yarım satır bırakma sınıfı kapanır)."""
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
    """TRANSACTION YÖNETMEZ — çağıran açar/kapatır. `dbmigrate` kayıttaki varlıkları TEK transaction'da
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
    """Tekil belgeyi tek transaction'da yazar (`do_write_doc` + COMMIT/ROLLBACK sarmalayıcısı)."""
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
        # `_isaretli_sifir` kapısı BURADA DA GEREKLİ (aynı gerekçe, ikinci yazım yolu): eğrinin
        # bir noktası `-0.0` ise kanonik yol onu yalnız REAL kolona yazar ve işaret kaybolur.
        # Kanonik-dışı sayılıp `extra_json`a düşerse nokta HAM hâliyle korunur (okuma yolu zaten
        # extra_json'u önceler). Kolon yine dolar — `ix_equity_ts` sorguları etkilenmez.
        if isinstance(p, (list, tuple)) and len(p) == 2 and isinstance(p[0], str) \
                and isinstance(p[1], float) and not _isaretli_sifir(p[1]):
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
    """Nokta serisini zarfıyla birlikte tek transaction'da yazar (`do_write_series` sarmalayıcısı)."""
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
    """Varlığı türüne göre okur (doc → `read_doc`, series → `read_series`, aksi → `read_rows`).
    `store.py`nin yönlendirdiği ortak okuma yüzeyi."""
    kind = _KIND[name]
    if kind == "doc":
        return read_doc(name)
    if kind == "series":
        return read_series(name)
    return read_rows(name)


def write_entity(name: str, payload: Any) -> None:
    """Varlığı türüne göre TAMAMEN yazar (doc → `write_doc`, series → `write_series`, aksi →
    `replace_rows`). `store.py`nin yönlendirdiği ortak yazma yüzeyi; her yol kendi transaction'ını
    açar."""
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
    """Varlığın damgasına migrasyon kanıtını basar: `migrated_at` + kaynak `source_digest`.
    TRANSACTION YÖNETMEZ — `dbmigrate` bunu kendi tek transaction'ı içinde çağırır."""
    c = conn or connect()
    c.execute("UPDATE entity_meta SET migrated_at=?, source_digest=? WHERE entity=?",
              (time.time(), digest, name))


def unmark_migrated(name: str, *, conn: sqlite3.Connection | None = None) -> None:
    """`mark_migrated`in tersi: `migrated_at` + `source_digest` temizlenir — okuma kapısı (`active`) varlığı
    DOSYAYA döndürür (Kademe C tur 2 F1, `dbmigrate --geri-al --varlik`). TRANSACTION YÖNETMEZ; tablo
    satırlarına DOKUNMAZ (kanıt olarak kalır).

    YALNIZ `DAMGA_KAPILI` VARLIK — aksi `ValueError`. Eski varlığın okuma kapısı YOKTUR: damgasını sökmek
    okumayı dosyaya döndürmez, ama bir sonraki `--uygula` onu "taşınmamış" sayıp tablosunu kaynak dosyayla
    EZER — sessiz veri kaybı yolu. Politika `dbmigrate`te de reddeder; bu satır mekanizmanın kendi sigortası."""
    if name not in DAMGA_KAPILI:
        raise ValueError(f"{name}: damga yalnız şemaya sonradan giren (kapılı) varlıklarda sökülebilir "
                         f"— kapılılar: {list(DAMGA_KAPILI)}")
    c = conn or connect()
    c.execute("UPDATE entity_meta SET migrated_at=NULL, source_digest=NULL WHERE entity=?", (name,))
    _DAMGA_OK.discard((str(db_path()), name))   # erken düşürmek güvenli taraftır (en kötü: bir sorgu fazla)
