"""store.py — state persistence helpers. Atomic JSON writes, JSONL append, and numpy sanitization
so nothing on disk carries np.float64 (which breaks json). state/ is the only mutable directory.

WP-H/H9 (2026-07-31) — İKİ SERTLEŞTİRME + BİR YÖNLENDİRME, DIŞ İMZA DEĞİŞMEDEN:

  (B1) ATOMİK YAZIM ARTIK DAYANIKLI: mkstemp + write + **fsync** + os.replace + dizin fsync.
       `os.replace` yer değiştirmenin ATOMİK olduğunu garanti eder ama VERİNİN diske indiğini
       etmez — güç kesintisi/panic sonrası dosya var ama SIFIR baytlık olabilirdi. fsync o sınıfı
       kapatır. Dizin fsync'i yer değiştirmenin kendisini kalıcı kılar (en iyi çaba: bazı dosya
       sistemlerinde dizin fd'si fsync kabul etmez).

  (B2) `file_lock` ARTIK SÜREÇLER ARASI: `fcntl.flock` + `state/.locks/<ad>.lock`. Eski hâli
       `threading.RLock`ti, yani YALNIZ aynı süreçte anlam taşıyordu; canlı worker + pano API +
       sprint aynı dosyaya yazabiliyordu ve kaybeden yazım hiçbir yerde görünmüyordu. API AYNI
       (`with store.file_lock(ad):`), yeniden girişli (RLock) davranış AYNI — tüm mevcut
       çağıranlar bedavaya sertleşir.

  (A3) ALTI DEFTER SQLite'a YÖNLENDİRİLİR: `meridian/storage.py` DB dosyası VARSA (yani Rol-1
       bakım penceresinde `dbmigrate --uygula` koşulduysa) `trades.jsonl`, `trade_plans.jsonl`,
       `scoreboard.json`, `portfolio.json`, `equity_curve.json`, `shadow_books.json` okuma/yazması
       DB'ye gider. DB YOKSA davranış BİREBİR bugünküdür. Çağıranlar aynı dict/list yapılarını
       almaya devam eder: bu bir DEPOLAMA migrasyonudur, davranış migrasyonu DEĞİL.
"""
from __future__ import annotations
import fcntl
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any
import numpy as np

from . import config
from . import storage


def _state():
    return config.STATE


def _path(name: str) -> Path:
    return _state() / name if not os.path.isabs(name) else Path(name)


def db_backed(name: str) -> bool:
    """Bu ad ŞU AN SQLite'tan mı okunuyor? (Okuyucusu: dbmigrate, ledgerstamp, testler.)"""
    return storage.active(name) if not os.path.isabs(str(name)) else False


def sanitize(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to native python for JSON.

    SONLU OLMAYAN FLOAT → None (2026-07-26). Eski hâli np tiplerini çeviriyor ama NaN/±Inf'i OLDUĞU
    GİBİ geçiriyordu; oysa JSON'da böyle bir değer YOKTUR ve bu iki yerde birden patlar:
      * telde: Starlette `JSONResponse` gövdeyi `allow_nan=False` ile dump eder → tek bir NaN ucun
        tamamını HTTP 500'e çevirir (numpy sızıntısının yaptığının aynısı, başka kapıdan);
      * diskte: `json.dumps` varsayılanı `NaN` YAZAR, ama tarayıcıdaki `JSON.parse` onu reddeder →
        pano dosyayı hiç okuyamaz.
    NaN'ı geçiren bir sigorta sigorta değildir. Ayrıca NaN "ölçülemedi" demektir ve bu depoda
    ölçülmeyenin dürüst temsili None'dır (UYDURMA YASAĞI): 0.0'a ya da başka bir sayıya çevirmek
    okura ölçülmemiş bir değeri ölçülmüş gibi gösterirdi.
    """
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [sanitize(v) for v in obj.tolist()]
    # YERLİ float ayrı bir daldır ve np dallarından SONRA gelir: `np.float64` Python `float`ın alt
    # sınıfıdır, yani bu kontrol yukarı taşınsaydı np dalını gölgeler ve `np.float32` gibi float
    # OLMAYAN np tipleri sessizce elenirdi. Buradaki iş yalnız `float("nan")`/`float("inf")`:
    # numpy'ye hiç uğramadan (ör. sıfıra bölme koruması, dışarıdan gelen JSON) doğan sonsuzluklar.
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# Faz 1 (öneri 4c): atomik yazım gecikme telemetrisi. Disk darboğazı mkstemp+os.replace süresini
# uzatır — bu sessiz kalmamalı. Son 200 yazımın süresi tutulur; p95 > 50 ms olursa BİR KEZ uyarılır
# (obs kendisi de buradan yazar — warned bayrağı özyinelemeyi keser).
import time as _time
_IO = {"n": 0, "recent": [], "warned": False}


def _record_io(ms: float) -> None:
    _IO["n"] += 1
    r = _IO["recent"]
    r.append(ms)
    if len(r) > 200:
        del r[:len(r) - 200]
    if not _IO["warned"] and len(r) >= 20:
        srt = sorted(r)
        if srt[int(len(srt) * 0.95) - 1] > 50.0:
            _IO["warned"] = True
            try:
                from . import obs
                obs.warn("io_latency_high", p95_ms=round(srt[int(len(srt) * 0.95) - 1], 1), n=_IO["n"])
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass


def io_stats() -> dict:
    r = sorted(_IO["recent"])
    return {"writes": _IO["n"], "recent_n": len(r),
            "p50_ms": round(r[len(r) // 2], 2) if r else None,
            "p95_ms": round(r[int(len(r) * 0.95) - 1], 2) if len(r) >= 20 else None,
            "max_ms": round(max(r), 2) if r else None}


_CORRUPT_SEEN: set = set()      # dosya başına BİR kez uyar (turu 34)

# ---- DOSYA BAŞINA OKU-DEĞİŞTİR-YAZ KİLİDİ (N/A yeniden sorgulaması, 2026-07-21) ----
# BULGU: portfolio.json'u İKİ iş parçacığı yazıyordu — zamanlayıcı (daily_cycle) ve Hermes
# (LLM görüş damgası). Kilit yoktu: damga, döngünün ARADA yazdığı defteri (silahlı set, pozisyonlar,
# nakit) BAYAT bir kopyayla geri alabilirdi. memory.py'de aynı desen audit #19'da veri kaybettirmişti;
# burada kaybedilecek şey CANLI DEFTER. Aynı süreçteki iş parçacıkları için RLock yeterli.
#
# SÜREÇLER ARASI KATMAN (B2, 2026-07-31): RLock süreç-içiydi ve bu depoda BELGELİ bir tehlike
# sınıfıydı — canlı worker, pano API'si ve sprint AYNI dosyalara yazabiliyor; `update_scoreboard`
# gibi oku-değiştir-yaz yazarları kilitsizdi. `fcntl.flock` aynı kilidi süreçler arasına taşır:
# API aynı, çağıran aynı, garanti farklı. RLock KALIR (aynı süreçteki iplikler için flock YETMEZ:
# flock tanıtıcı başınadır ve aynı süreçte ikinci bir kilitleme anında geçer).
import threading as _th
_FILE_LOCKS: dict = {}
_LOCKS_GUARD = _th.Lock()
_FLOCK_WARNED: set = set()


class _FileLock:
    """`with store.file_lock(ad):` — süreç-içi RLock + süreçler-arası flock.

    Kilit dosyası `state/.locks/<ad>.lock`tur ve VERİ dosyasının kendisine kilitlenmez: veri
    dosyası `os.replace` ile yer değiştirdiği için inode'u değişir, ve inode'a bağlı bir flock
    yer değiştirmeden sonra BAŞKA bir dosyayı kilitliyor olurdu — yani kilit sessizce hiçbir şeyi
    korumazdı. Ayrı bir kilit dosyası bu sınıfı yapısal olarak kapatır.

    KİLİT DOSYASI TEMBEL AÇILIR: `file_lock(ad)` yalnız nesneyi verir, hiçbir bayt yazmaz
    (testlerdeki kimlik iddiası ve canlı-state sızıntı bekçisi bu davranışa bağlı)."""

    __slots__ = ("name", "_rlock", "_depth", "_fd", "_dir")

    def __init__(self, name: str, lock_dir: Path):
        self.name = name
        self._rlock = _th.RLock()
        self._depth = 0
        self._fd: int | None = None
        self._dir = lock_dir

    def _lock_path(self) -> Path:
        return self._dir / (str(self.name).replace(os.sep, "_") + ".lock")

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        if not self._rlock.acquire(blocking, timeout):
            return False
        if self._depth == 0:
            try:
                self._dir.mkdir(parents=True, exist_ok=True)
                fd = os.open(str(self._lock_path()), os.O_RDWR | os.O_CREAT, 0o644)
                fcntl.flock(fd, fcntl.LOCK_EX)
                self._fd = fd
            except OSError as e:
                # SÜREÇLER-ARASI katman kurulamadı (salt-okunur dizin, NFS, fd tükenmesi).
                # Süreç-İÇİ kilit yine de tutuluyor — yani eski davranışa düşülür, kilitsiz
                # kalınmaz. Sessiz kalırsa "kilit var" iddiası ölçülmemiş olur; bir kez uyarılır.
                if self.name not in _FLOCK_WARNED:
                    _FLOCK_WARNED.add(self.name)
                    try:
                        from . import obs
                        obs.warn("file_lock_flock_unavailable", file=str(self.name),
                                 error=f"{type(e).__name__}: {e}",
                                 detail="süreçler-arası kilit kurulamadı — süreç-İÇİ RLock'a düşüldü")
                    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                        pass
                self._fd = None
        self._depth += 1
        return True

    def release(self) -> None:
        self._depth -= 1
        if self._depth == 0 and self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
            except OSError:  # sessiz-yutma: kilit tanıtıcısı zaten kapanmış/geçersiz; süreç sonu onu her hâlükârda toplar ve bırakma denemesi çağıranı düşüremez
                pass
            self._fd = None
        self._rlock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
        return False


def file_lock(name: str):
    """Ada göre TEK kilit nesnesi. Anahtar (state_dizini, ad): ölçüm sandbox'ları `config.STATE`i
    değiştirir ve iki ayrı sandbox'ın aynı adı AYNI kilide düşerse testler birbirini bekletirdi."""
    key = (str(_state()), str(name))
    with _LOCKS_GUARD:
        lk = _FILE_LOCKS.get(key)
        if lk is None:
            lk = _FileLock(name, Path(_state()) / ".locks")
            _FILE_LOCKS[key] = lk
        return lk


from . import provenance as _prov


def update_json(name: str, fn, default: Any = None) -> Any:
    """Kilitli oku-değiştir-yaz. fn(doc) belgeyi yerinde değiştirir ve True dönerse yazılır.
    İki yazar arasındaki kayıp-güncellemeyi yapısal olarak imkânsız kılar."""
    with file_lock(name):
        doc = read_json(name, default)
        changed = fn(doc)
        if changed:
            write_json(name, doc)
        return doc


def update_jsonl(name: str, fn) -> list:
    """JSONL için aynı disiplin: kilit altında oku, değiştir, (gerekirse) yaz."""
    with file_lock(name):
        rows = read_jsonl(name)
        changed = fn(rows)
        if changed:
            write_jsonl(name, rows)
        return rows


def _atomic_write(path: Path, data: str) -> None:
    """TEK ATOMİK YAZIM YOLU (B1): tmp → write → fsync → os.replace → dizin fsync.

    Eskiden fsync YOKTU: `os.replace` yer değiştirmenin atomik olduğunu söyler, verinin diske
    indiğini SÖYLEMEZ. Güç kesintisi/kernel panic sonrası dosya VAR ama içi boş olabilirdi ve
    `read_json` onu "bozuk dosya → varsayılan" diye yutardı (defter BOŞ görünürdü). Bütün
    yazarlar bu tek boğazdan geçtiği için sertleşme bedavaya yayılır."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)   # atomic
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik; geçici dosya zaten yoksa yapacak bir şey yok ve asıl istisna yukarı çıkmaya devam eder
            pass
        raise
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:  # sessiz-yutma: dizin fsync'i EN İYİ ÇABAdır (bazı dosya sistemleri dizin fd'sine fsync kabul etmez); dosyanın KENDİ fsync'i yukarıda garanti edildi, kayıp yarım-yazım değil en fazla yer değiştirmenin gecikmiş kalıcılığıdır
        pass


def write_json(name: str, obj: Any) -> Path:
    t0 = _time.perf_counter()
    payload = sanitize(obj)
    if db_backed(name):
        storage.write_entity(name, payload)
        _record_io((_time.perf_counter() - t0) * 1000.0)
        return storage.db_path()
    path = _path(name)
    _atomic_write(path, json.dumps(payload, indent=2))
    _record_io((_time.perf_counter() - t0) * 1000.0)
    return path


def read_json(name: str, default: Any = None) -> Any:
    if db_backed(name):
        doc = storage.read_entity(name)
        return default if doc is None else _prov.sar(name, doc)
    path = _path(name)
    if not path.exists():
        return default
    try:
        with open(path) as f:
            # KÖKEN TAKİBİ: kapalıyken `sar` nesneyi olduğu gibi döndürür (sıfır maliyet).
            # Açıkken her .get()/[] okuması kaydedilir — bkz. meridian/provenance.py
            return _prov.sar(name, json.load(f))
    except (json.JSONDecodeError, OSError) as e:
        # a corrupt/unreadable state file must degrade to the default, never 500 an endpoint or kill a
        # cycle — writers are atomic, so this only fires on external damage (ops audit hardening).
        # AMA SESSİZ OLMAZ (denetim turu 34, 2026-07-21): portfolio.json bozulursa defter BOŞ görünür
        # ve motor pozisyonları yokmuş gibi davranır. "Varsayılana düştük" bir olay olarak kaydedilir;
        # dosya başına bir kez (log seli yok).
        if name not in _CORRUPT_SEEN:
            _CORRUPT_SEEN.add(name)
            try:
                from . import obs
                obs.warn("state_file_unreadable", file=str(name),
                         error=f"{type(e).__name__}", detail="varsayılana düşüldü — dosya bozuk olabilir")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
        return default


def append_jsonl(name: str, row: dict) -> None:
    t0 = _time.perf_counter()
    payload = sanitize(row)
    if db_backed(name):
        storage.append_row(name, payload)
        _record_io((_time.perf_counter() - t0) * 1000.0)
        return
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(payload) + "\n")
    _record_io((_time.perf_counter() - t0) * 1000.0)


def read_jsonl(name: str, limit: int | None = None) -> list[dict]:
    if db_backed(name):
        return _prov.sar(name, storage.read_rows(name, limit=limit))
    path = _path(name)
    if not path.exists():
        return []
    rows, bad = [], 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                    bad += 1
                    continue
    if bad and name not in _CORRUPT_SEEN:
        # BOZUK SATIR = SESSİZ VERİ KAYBI (turu 34): append_jsonl atomik değildir; çökme ya da disk
        # dolması yarım bir satır bırakır ve o işlem/plan/olay defterden sessizce düşerdi.
        _CORRUPT_SEEN.add(name)
        try:
            from . import obs
            obs.warn("jsonl_rows_skipped", file=str(name), skipped=bad, kept=len(rows))
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return _prov.sar(name, rows[-limit:] if limit else rows)


def merge_dated_jsonl(name: str, date_value: str, new_rows: list[dict], cap: int = 500) -> None:
    """Idempotent per-date write: drop any existing rows for date_value, append new_rows, keep the
    last `cap`. Lets candidates/plans accumulate a dated history without duplicating on re-run.

    KİLİT (B3, 2026-07-31): bu bir OKU-DEĞİŞTİR-YAZdır ve kilitsizdi. `loop.daily_cycle` bunu
    `trade_plans.jsonl` için çağırırken Hermes'in görüş damgası (`update_jsonl`, KİLİTLİ) aynı
    deftere yazabiliyordu — kilitli taraf kilitsiz tarafı bekletemez, yani kilit tek taraflıysa
    kilit YOKTUR. Aynı ada bağlanır, böylece iki yol aynı sırayı paylaşır."""
    with file_lock(name):
        existing = [r for r in read_jsonl(name) if r.get("date") != date_value]
        write_jsonl(name, (existing + new_rows)[-cap:])


def write_jsonl(name: str, rows: list[dict]) -> None:
    if db_backed(name):
        storage.replace_rows(name, [sanitize(r) for r in rows])
        return
    path = _path(name)
    _atomic_write(path, "".join(json.dumps(sanitize(r)) + "\n" for r in rows))


# ---- TAZELİK DAMGASI (dosya mtime'ının arka-uç bağımsız karşılığı) ------------------------------
# NEDEN VAR: beş yerde `(config.STATE / ad).stat()` ile ÖNBELLEK ANAHTARI ve TAZELİK ölçülüyordu
# (analytics._nd_stamp, shadow_model.dataset_fingerprint, intraday_cycle._planned,
# ledgerstamp._mtime, watchdog.coherence_report). Defter DB'ye taşındığında o dosyalar `.migrated`
# ekiyle DONAR: mtime bir daha ASLA değişmez, yani önbellek sonsuza kadar bayat kalır ve tazelik
# dedektörü "hiç güncellenmiyor" der. İkisi de SESSİZ yanlış cevaptır. Bu iki fonksiyon damgayı
# arka uçtan soyutlar; DB'de karşılığı `entity_meta.updated_at`/`rev`tir.
def stamp(name: str) -> tuple:
    """(değişim_damgası, boyut/revizyon) — yalnız İÇERİK değiştiğinde değişir. Yoksa (0, 0)."""
    if db_backed(name):
        return storage.stamp(name) or (0, 0)
    try:
        st = _path(name).stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:  # sessiz-yutma: defter henüz yok — damga sabit (0,0) ve bu KAYDA GEÇEN bir değerdir ("dosya yok" hâli), çağıran onu boş defterle aynı önbellek anahtarına eşler
        return (0, 0)


def mtime(name: str) -> float | None:
    """Son yazım zamanı (epoch sn) ya da ölçülemediyse None — arka uçtan bağımsız."""
    if db_backed(name):
        m = storage.meta(name)
        return float(m["updated_at"]) if m and m["present"] else None
    try:
        return _path(name).stat().st_mtime
    except OSError:  # sessiz-yutma: dosya yoksa/okunamıyorsa ÖLÇÜM YAPILAMADI demektir ve None tam olarak bunu söyler — çağıran onu "bilinmiyor" diye taşır, sıfır ya da şimdi UYDURULMAZ
        return None
