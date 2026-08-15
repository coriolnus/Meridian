"""regime_trigger.py — ertelenmiş rejim-bütçe tetikleyicisi: rejim başına örneklem sayacı + "kanıt hazır" sinyali.

NE YAPAR. Mevcut statik duruş ("chop → %0 maruziyet") KİLİTLİ kalır — bir rejimde yalnız bir avuç
gerçekleşmiş işlem varken dinamik kenar-bütçelemesi süs olur. Bu modül karar VERMEZ; kanıtın
biriktiği anı görünür kılar: `DeferredRegimeBudgetTrigger.evaluate` kapanmış işlem defterini rejim
etiketine göre sayar (evren config.VALID_REGIMES), rejim başına {n, threshold, ready} döndürür ve
bir rejim eşiği İLK kez aştığında tek seferlik `regime_budget_trigger` olayı basar — dinamik
bootstrap/edge bütçelemesine geçişin "artık kanıt var" sinyali.

KİLİT GİRİŞLER: THRESHOLD_N = 30 (rejim başına asgari kapanmış işlem), STATE_FILE
("regime_trigger.json" — ateşlenmiş rejimlerin kalıcı listesi), `evaluate(trades=None)` (defteri
kendisi okur ya da çağıranın verdiği listeyi sayar).

DEĞİŞMEZLER: eşik aşımı rejim başına yalnız BİR kez olaylanır (fired listesi kalıcı); geçişin
kendisi bu modülün DIŞINDA, ayrı ve bilinçli bir operatör/tasarım kararıdır — burada hiçbir bütçe,
kapı ya da parametre değişmez.

OKUR: trades.jsonl (ya da verilen liste), regime_trigger.json. YAZAR: regime_trigger.json
("fired") + obs olay defteri."""
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
