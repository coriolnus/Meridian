"""regime_trigger.py — Ertelenmiş Rejim Bütçe Tetikleyicisi (karar mekanizması v3, Component 4).

Mevcut statik duruş ("chop → %0") KİLİTLİ kalır — chop'ta yalnız 8 gerçekleşmiş işlem varken dinamik
kenar-bütçelemesi süs olur. Bu modül karar VERMEZ: rejim başına kapanmış işlem sayısını sayar ve
N ≥ 30 eşiği aşıldığında karne API'sine bir tetikleyici bayrağı fırlatır (+ bir kez obs.log) —
dinamik bootstrap/edge bütçelemesine geçişin "artık kanıt var" sinyali. Geçişin kendisi ayrı ve
bilinçli bir tasarım kararıdır."""
from __future__ import annotations

from . import config, store, obs

THRESHOLD_N = 30
STATE_FILE = "regime_trigger.json"


class DeferredRegimeBudgetTrigger:
    def __init__(self, threshold: int = THRESHOLD_N):
        self.threshold = int(threshold)

    def evaluate(self, trades: list | None = None) -> dict:
        """{regime: {n, ready}} + yeni hazır olan rejim için tek seferlik olay kaydı."""
        trades = trades if trades is not None else store.read_jsonl("trades.jsonl")
        counts: dict[str, int] = {r: 0 for r in config.VALID_REGIMES}
        for t in trades:
            r = t.get("regime")
            if r in counts:
                counts[r] += 1
        fired = set(store.read_json(STATE_FILE, {}).get("fired", []))
        out, newly = {}, []
        for r, n in counts.items():
            ready = n >= self.threshold
            out[r] = {"n": n, "threshold": self.threshold, "ready": ready}
            if ready and r not in fired:
                newly.append(r)
        if newly:
            obs.log("regime_budget_trigger", regimes=newly,
                    detail="dinamik kenar-bütçelemesi için örneklem eşiği aşıldı — geçiş operatör kararı")
            store.write_json(STATE_FILE, {"fired": sorted(fired | set(newly))})
        return out
