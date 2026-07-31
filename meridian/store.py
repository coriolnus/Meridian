"""store.py — state persistence helpers. Atomic JSON writes, JSONL append, and numpy sanitization
so nothing on disk carries np.float64 (which breaks json). state/ is the only mutable directory."""
from __future__ import annotations
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any
import numpy as np

from . import config


def _state():
    return config.STATE


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
import threading as _th
_FILE_LOCKS: dict = {}
_LOCKS_GUARD = _th.Lock()


def file_lock(name: str) -> "_th.RLock":
    with _LOCKS_GUARD:
        if name not in _FILE_LOCKS:
            _FILE_LOCKS[name] = _th.RLock()
        return _FILE_LOCKS[name]


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


def write_json(name: str, obj: Any) -> Path:
    t0 = _time.perf_counter()
    path = _state() / name if not os.path.isabs(name) else Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(sanitize(obj), indent=2)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(data)
    os.replace(tmp, path)   # atomic
    _record_io((_time.perf_counter() - t0) * 1000.0)
    return path


def read_json(name: str, default: Any = None) -> Any:
    path = _state() / name if not os.path.isabs(name) else Path(name)
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
    path = _state() / name if not os.path.isabs(name) else Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(sanitize(row)) + "\n")
    _record_io((_time.perf_counter() - t0) * 1000.0)


def read_jsonl(name: str, limit: int | None = None) -> list[dict]:
    path = _state() / name if not os.path.isabs(name) else Path(name)
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
    last `cap`. Lets candidates/plans accumulate a dated history without duplicating on re-run."""
    existing = [r for r in read_jsonl(name) if r.get("date") != date_value]
    write_jsonl(name, (existing + new_rows)[-cap:])


def write_jsonl(name: str, rows: list[dict]) -> None:
    path = _state() / name if not os.path.isabs(name) else Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        for r in rows:
            f.write(json.dumps(sanitize(r)) + "\n")
    os.replace(tmp, path)
